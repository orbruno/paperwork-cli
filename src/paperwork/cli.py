"""CLI for Paperwork.

Templates dir is resolved in this order:
    1. --templates-dir flag
    2. PAPERWORK_TEMPLATES_DIR env var
    3. ./templates/ in current directory (if it exists)

Usage:
    paperwork generate --profile profile.yaml --template classic --output cv.pdf
    paperwork validate --profile profile.yaml --template classic
    paperwork templates list
    paperwork estimate --profile profile.yaml --template classic

All commands write JSON to stdout. Errors write a JSON envelope to stderr.

Exit codes:
    0  success
    2  argument misuse (bad flag, missing required arg)
    3  validation error (profile fails template requirements)
    4  render error (PDF generation failed)
    5  profile load error (bad YAML, missing file)
    6  template not found
"""

import json
import os
import platform
import re
import sys
import tempfile
import webbrowser
from pathlib import Path

import click

from .engine.renderer import RenderEngine, ValidationError
from .profiles.loader import load_profile, ProfileLoadError, load_job, JobLoadError


# =============================================================================
# Exit codes
# =============================================================================

class ExitCode:
    OK = 0
    ARG_MISUSE = 2
    VALIDATION_ERROR = 3
    RENDER_ERROR = 4
    PROFILE_LOAD_ERROR = 5
    TEMPLATE_NOT_FOUND = 6


# =============================================================================
# Output helpers
# =============================================================================

def _use_color() -> bool:
    """Return True only when stdout is a TTY and NO_COLOR is not set."""
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _out(data: object) -> None:
    """Write structured data as JSON to stdout."""
    click.echo(json.dumps(data, indent=2, default=str))


def _err(
    code: int,
    error_type: str,
    message: str,
    detail: str = "",
    fix: str = "",
) -> None:
    """Write a structured JSON error envelope to stderr and exit."""
    envelope = {
        "error": {
            "code": code,
            "type": error_type,
            "message": message,
            **({"detail": detail} if detail else {}),
            **({"fix": fix} if fix else {}),
            "help": "paperwork --help",
        }
    }
    click.echo(json.dumps(envelope, indent=2), err=True)
    sys.exit(code)


# =============================================================================
# Input validation
# =============================================================================

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _validate_slug(slug: str) -> None:
    """Reject template slugs that contain control characters or invalid format."""
    if "\x00" in slug or any(ord(c) < 32 for c in slug):
        _err(
            ExitCode.ARG_MISUSE,
            "invalid_argument",
            f"Template slug contains control characters: {slug!r}",
            fix="Use a slug matching [a-z0-9][a-z0-9_-]* (e.g. 'classic')",
        )
    if not _SLUG_RE.match(slug):
        _err(
            ExitCode.ARG_MISUSE,
            "invalid_argument",
            f"Invalid template slug: {slug!r}",
            fix="Use a slug matching [a-z0-9][a-z0-9_-]* (e.g. 'classic')",
        )


def _validate_path(p: Path, *, allow_create: bool = False) -> Path:
    """Reject path traversal, null bytes, and non-existent paths (unless allow_create)."""
    raw = str(p)
    if "\x00" in raw:
        _err(
            ExitCode.ARG_MISUSE,
            "invalid_path",
            f"Path contains null byte: {raw!r}",
            fix="Provide a valid filesystem path without null bytes.",
        )
    resolved = p.resolve()
    # Reject paths that escape via traversal (only relevant for profile/output, not templates-dir)
    if not allow_create and not resolved.exists():
        _err(
            ExitCode.ARG_MISUSE,
            "path_not_found",
            f"Path does not exist: {resolved}",
            fix=f"Check that the path is correct and the file exists.",
        )
    return resolved


# =============================================================================
# Templates-dir resolution
# =============================================================================

def _parse_layout_vars(layout_vars: tuple[str, ...]) -> dict[str, str]:
    """Parse --set KEY=VALUE strings into a dict. Exits on malformed input."""
    result: dict[str, str] = {}
    for item in layout_vars:
        if "=" not in item:
            _err(
                ExitCode.ARG_MISUSE,
                "invalid_argument",
                f"--set value must be KEY=VALUE, got: {item!r}",
                fix="Example: --set font-size-body=9px",
            )
        key, _, value = item.partition("=")
        result[key.strip()] = value.strip()
    return result


def _build_layout_overrides(overrides: dict[str, str]) -> list[str]:
    """Convert a layout overrides dict into CSS override strings.

    Page margin keys inject @page rules directly (WeasyPrint var() in @page
    is unreliable). All other keys become :root custom property declarations.
    """
    PAGE_MARGIN_MAP = {
        "page-margin":        lambda v: f"margin: {v}",
        "page-margin-top":    lambda v: f"margin-top: {v}",
        "page-margin-bottom": lambda v: f"margin-bottom: {v}",
        "page-margin-side":   lambda v: f"margin-left: {v}; margin-right: {v}",
    }

    root_vars: dict[str, str] = {}
    page_decls: list[str] = []

    for key, value in overrides.items():
        if key in PAGE_MARGIN_MAP:
            page_decls.append(PAGE_MARGIN_MAP[key](value))
        else:
            root_vars[f"--{key}"] = value

    result: list[str] = []
    if root_vars:
        decls = "; ".join(f"{k}: {v}" for k, v in root_vars.items())
        result.append(f":root {{ {decls}; }}")
    if page_decls:
        decls = "; ".join(page_decls)
        result.append(f"@page {{ {decls}; }}")

    return result


def _resolve_templates_dir(explicit: Path | None) -> Path:
    if explicit:
        return _validate_path(explicit)

    from_env = os.environ.get("PAPERWORK_TEMPLATES_DIR")
    if from_env:
        resolved = Path(from_env).expanduser().resolve()
        if resolved.exists():
            return resolved

    try:
        local = Path.cwd() / "templates"
        if local.exists():
            return local
    except (PermissionError, OSError):
        pass

    _err(
        ExitCode.ARG_MISUSE,
        "templates_dir_not_found",
        "No templates directory found.",
        detail="Searched: --templates-dir flag, PAPERWORK_TEMPLATES_DIR env var, ./templates/ in cwd.",
        fix=(
            "Provide one via:\n"
            "  --templates-dir PATH\n"
            "  PAPERWORK_TEMPLATES_DIR env var\n"
            "  Place templates in ./templates/ in current directory"
        ),
    )


def _ensure_library_path() -> None:
    """Set library path for WeasyPrint on macOS with Homebrew."""
    if platform.system() != "Darwin":
        return
    homebrew_lib = Path("/opt/homebrew/lib")
    if not homebrew_lib.exists():
        return
    current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    if str(homebrew_lib) not in current:
        parts = [str(homebrew_lib)]
        if current:
            parts.append(current)
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(parts)


_ensure_library_path()


# =============================================================================
# CLI root
# =============================================================================

CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"],
    color=_use_color(),
)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--templates-dir",
    type=click.Path(path_type=Path, exists=False, readable=False),
    default=None,
    help="Templates directory. Falls back to PAPERWORK_TEMPLATES_DIR env var, then ./templates/.",
)
@click.pass_context
def cli(ctx, templates_dir):
    """Paperwork — Generate PDFs from structured YAML data and templates.

    How it works:

    \b
      1. Write your CV as a YAML profile (name, experience, skills, etc.)
      2. Pick a template (e.g. "classic")
      3. Run generate — get a PDF

    The template spec defines every field, its constraints (min/max chars,
    max items), and layout parameters. Always consult it before writing or
    adapting a profile:

    \b
      paperwork spec --template classic

    Typical workflow:

    \b
      paperwork spec     --template classic                          # field constraints
      paperwork validate --profile me.yaml  --template classic       # check profile
      paperwork generate --profile me.yaml  --template classic \\
                        --output cv.pdf                             # render PDF
    """
    ctx.ensure_object(dict)
    ctx.obj["templates_dir"] = _resolve_templates_dir(templates_dir)


# =============================================================================
# templates list
# =============================================================================

@cli.group("templates")
@click.pass_context
def templates_group(ctx):
    """Manage and inspect available templates.

    Example:
      paperwork templates list
    """
    pass


@templates_group.command("list")
@click.pass_context
def list_templates(ctx):
    """List available templates as JSON.

    \b
    Example:
      paperwork templates list
      paperwork templates list | jq '.[].slug'
    """
    engine = RenderEngine(ctx.obj["templates_dir"])
    templates = engine.registry.list_templates()
    _out([t.model_dump() for t in templates])


# =============================================================================
# generate
# =============================================================================

@cli.command()
@click.option("--profile", "-p", default=None, type=click.Path(path_type=Path, exists=False, readable=False), help="Path to YAML profile.")
@click.option("--job", "-j", default=None, type=click.Path(path_type=Path, exists=False, readable=False), help="Path to job YAML (profile + render: block). Replaces --profile/--template/--output.")
@click.option("--template", "-t", default=None, help="Template slug (e.g. classic). Not needed with --job.")
@click.option("--output", "-o", default=None, type=click.Path(path_type=Path, exists=False, readable=False), help="Output PDF path. Not needed with --job.")
@click.option("--auto-fit", is_flag=True, default=False, help="Auto-fit content to target page count.")
@click.option("--target-pages", type=int, default=None, help="Target number of pages (default: 1).")
@click.option("--fit-report", is_flag=True, default=False, help="Include auto-fit report in output.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview what would be generated without writing to disk.")
@click.option("--force", is_flag=True, default=False, help="Overwrite output file if it already exists.")
@click.option(
    "--set", "layout_vars", multiple=True, metavar="KEY=VALUE",
    help=(
        "Override a layout variable. Repeatable. Merged with layout_overrides in --job. "
        "Example: --set font-size-body=9px --set section-gap=14px. "
        "Page margins: --set page-margin=0.8cm | --set page-margin-top=0.8cm | "
        "--set page-margin-side=0.8cm | --set page-margin-bottom=0.8cm."
    ),
)
@click.pass_context
def generate(ctx, profile, job, template, output, auto_fit, target_pages, fit_report, dry_run, force, layout_vars):
    """Render a CV to PDF. Accepts a profile (--profile) or a self-contained job YAML (--job).

    \b
    Profile mode (template + output required):
      paperwork generate --profile me.yaml --template classic --output cv.pdf
      paperwork generate --profile me.yaml --template classic --output cv.pdf --force
      paperwork generate --profile me.yaml --template classic --output cv.pdf --auto-fit --fit-report
      paperwork generate --profile me.yaml --template classic --output cv.pdf \\
                        --set font-size-body=9px --set section-gap=14px
      paperwork generate --profile me.yaml --template classic --output cv.pdf \\
                        --set page-margin=0.8cm

    \b
    Job mode (template + output + layout_overrides come from the render: block):
      paperwork generate --job jobs/acme-corp.yaml
      paperwork generate --job jobs/acme-corp.yaml --force
      paperwork generate --job jobs/acme-corp.yaml --set section-gap=12px
    """
    # --- input validation ---
    if job and profile:
        _err(ExitCode.ARG_MISUSE, "invalid_argument",
             "--job and --profile are mutually exclusive.",
             fix="Use --job for a self-contained job YAML, or --profile with --template and --output.")
    if not job and not profile:
        _err(ExitCode.ARG_MISUSE, "invalid_argument",
             "Provide either --profile or --job.",
             fix="paperwork generate --profile me.yaml --template classic --output cv.pdf")

    # --- load inputs ---
    if job:
        job = _validate_path(job)
        try:
            cv_data, render_config = load_job(job)
        except JobLoadError as e:
            _err(ExitCode.PROFILE_LOAD_ERROR, "job_load_error",
                 f"Failed to load job file: {job.name}", detail=str(e),
                 fix="Check the YAML for syntax errors and ensure a render: block is present.")
        template = render_config.template
        output = Path(render_config.output)
        # CLI --set overrides merge on top of job file layout_overrides
        merged_overrides = {**render_config.layout_overrides, **_parse_layout_vars(layout_vars)}
        if auto_fit is False and render_config.auto_fit:
            auto_fit = render_config.auto_fit
        if target_pages is None:
            target_pages = render_config.target_pages
        if not fit_report and render_config.fit_report:
            fit_report = render_config.fit_report
    else:
        if not template:
            _err(ExitCode.ARG_MISUSE, "invalid_argument", "--template is required with --profile.",
                 fix="paperwork generate --profile me.yaml --template classic --output cv.pdf")
        if not output:
            _err(ExitCode.ARG_MISUSE, "invalid_argument", "--output is required with --profile.",
                 fix="paperwork generate --profile me.yaml --template classic --output cv.pdf")
        merged_overrides = _parse_layout_vars(layout_vars)
        try:
            cv_data = load_profile(profile)
        except ProfileLoadError as e:
            _err(ExitCode.PROFILE_LOAD_ERROR, "profile_load_error",
                 f"Failed to load profile: {profile.name}", detail=str(e),
                 fix="Check the YAML file for syntax errors or missing required fields.")

    if target_pages is None:
        target_pages = 1

    _validate_slug(template)
    output = _validate_path(output, allow_create=True)

    would_overwrite = output.exists()
    if not dry_run and would_overwrite and not force:
        _err(
            ExitCode.ARG_MISUSE,
            "file_exists",
            f"Output file already exists: {output}",
            detail="Overwriting without --force is not allowed.",
            fix="Add --force to overwrite, or choose a different output path.",
        )

    if dry_run:
        _out({
            "dry_run": True,
            "source": str(job) if job else str(profile),
            "template": template,
            "output": str(output),
            "would_overwrite": would_overwrite,
            "auto_fit": auto_fit,
            "target_pages": target_pages,
            "layout_overrides": merged_overrides,
        })
        return

    engine = RenderEngine(ctx.obj["templates_dir"])
    css_overrides: list[str] = _build_layout_overrides(merged_overrides)
    render_cv = cv_data
    fit_report_data = None

    if auto_fit:
        from .autofit import optimize, FitConfig

        meta = engine.registry.get_template(template)
        try:
            layout = meta.get_layout_params()
        except ValueError as e:
            _err(
                ExitCode.ARG_MISUSE,
                "auto_fit_not_supported",
                f"Template '{template}' does not support --auto-fit.",
                detail=str(e),
                fix="Check that template.yaml includes a layout_params block.",
            )

        from .models.cv import CVData
        config = FitConfig(target_pages=target_pages, layout=layout)
        result = optimize(cv_data.model_dump(), config)
        render_cv = CVData(**result.trimmed_cv)
        css_overrides = css_overrides + result.css_overrides
        if fit_report:
            fit_report_data = result.report.format()

    try:
        pdf_bytes = engine.render_pdf(render_cv, template, css_overrides=css_overrides)
    except ValidationError as e:
        _err(
            ExitCode.VALIDATION_ERROR,
            "validation_error",
            "Profile data failed template validation.",
            detail=str(e),
            fix=f"Run: paperwork validate --profile {profile} --template {template}",
        )
    except Exception as e:
        _err(
            ExitCode.RENDER_ERROR,
            "render_error",
            "PDF generation failed.",
            detail=str(e),
            fix="Check that WeasyPrint dependencies are installed and the template is valid.",
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pdf_bytes)

    result_data = {
        "status": "ok",
        "output": str(output),
        "size_bytes": len(pdf_bytes),
        "template": template,
        "source": str(job) if job else str(profile),
    }
    if fit_report_data:
        result_data["fit_report"] = fit_report_data

    _out(result_data)


# =============================================================================
# validate
# =============================================================================

@cli.command()
@click.option("--profile", "-p", required=True, type=click.Path(path_type=Path, exists=False, readable=False), help="Path to YAML profile.")
@click.option("--template", "-t", required=True, help="Template slug (e.g. classic).")
@click.pass_context
def validate(ctx, profile, template):
    """Check that a YAML profile satisfies a template's required fields.

    Exits 0 if valid, 3 if required fields are missing. Run this before
    generate to catch problems early.

    \b
    Example:
      paperwork validate --profile me.yaml --template classic
      paperwork validate --profile me.yaml --template classic | jq '.status'
    """
    _validate_slug(template)
    profile = _validate_path(profile)

    try:
        cv_data = load_profile(profile)
    except ProfileLoadError as e:
        _err(
            ExitCode.PROFILE_LOAD_ERROR,
            "profile_load_error",
            f"Failed to load profile: {profile.name}",
            detail=str(e),
            fix="Check the YAML file for syntax errors.",
        )

    engine = RenderEngine(ctx.obj["templates_dir"])
    result = engine.validate(cv_data, template)

    if result.is_valid:
        _out({
            "status": "valid",
            "template": template,
            "profile": str(profile),
            "present_required": result.present_required,
            "present_optional": result.present_optional,
            "missing_optional": result.missing_optional,
        })
    else:
        _out({
            "status": "invalid",
            "template": template,
            "profile": str(profile),
            "missing_required": result.missing_required,
            "present_required": result.present_required,
        })
        sys.exit(ExitCode.VALIDATION_ERROR)


# =============================================================================
# preview
# =============================================================================

@cli.command()
@click.option("--profile", "-p", required=True, type=click.Path(path_type=Path, exists=False, readable=False), help="Path to YAML profile.")
@click.option("--template", "-t", required=True, help="Template slug (e.g. classic).")
@click.pass_context
def preview(ctx, profile, template):
    """Render the CV as HTML and open it in the browser for quick visual inspection.

    \b
    Example:
      paperwork preview --profile me.yaml --template classic
    """
    _validate_slug(template)
    profile = _validate_path(profile)

    try:
        cv_data = load_profile(profile)
    except ProfileLoadError as e:
        _err(
            ExitCode.PROFILE_LOAD_ERROR,
            "profile_load_error",
            f"Failed to load profile: {profile.name}",
            detail=str(e),
            fix="Check the YAML file for syntax errors.",
        )

    engine = RenderEngine(ctx.obj["templates_dir"])
    try:
        html = engine.render_html(cv_data, template)
    except ValidationError as e:
        _err(
            ExitCode.VALIDATION_ERROR,
            "validation_error",
            "Profile data failed template validation.",
            detail=str(e),
            fix=f"Run: paperwork validate --profile {profile} --template {template}",
        )

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(html)
        html_path = f.name

    webbrowser.open(f"file://{html_path}")
    _out({"status": "ok", "html_path": html_path, "template": template})


# =============================================================================
# spec
# =============================================================================

@cli.command()
@click.option("--template", "-t", required=True, help="Template slug (e.g. classic).")
@click.pass_context
def spec(ctx, template):
    """Return the full field spec for a template as JSON.

    Outputs every field with its type, description, and constraints
    (min/max chars, min/max items, recommended ranges) plus the layout
    reference (margins, column widths, font sizes).

    Designed for LLM consumption: feed this output to a model before asking
    it to write or adapt any CV field so it knows exactly what to produce
    and within what limits.

    \b
    Example:
      paperwork spec --template classic
      paperwork spec --template classic | jq '.fields.profile.constraints'
      paperwork spec --template classic | jq '.fields.work_experience.fields.roles.constraints'
      paperwork spec --template classic | jq '.layout'
    """
    import yaml

    _validate_slug(template)
    engine = RenderEngine(ctx.obj["templates_dir"])
    meta = engine.registry.get_template(template)

    if not meta.spec_file:
        _err(
            ExitCode.ARG_MISUSE,
            "spec_not_found",
            f"Template '{template}' has no spec_file defined in template.yaml.",
            fix="Add spec_file: spec.yaml to the template manifest.",
        )

    template_dir = engine.registry.get_template_dir(template)
    spec_path = template_dir / meta.spec_file

    if not spec_path.exists():
        _err(
            ExitCode.ARG_MISUSE,
            "spec_not_found",
            f"Spec file not found: {spec_path}",
            fix=f"Create {meta.spec_file} in the template directory.",
        )

    with open(spec_path) as f:
        spec_data = yaml.safe_load(f)

    _out(spec_data)


# =============================================================================
# estimate
# =============================================================================

@cli.command()
@click.option("--profile", "-p", required=True, type=click.Path(path_type=Path, exists=False, readable=False), help="Path to YAML profile.")
@click.option("--template", "-t", required=True, help="Template slug (e.g. classic).")
@click.option("--target-pages", type=int, default=1, help="Target number of pages (default: 1).")
@click.pass_context
def estimate(ctx, profile, template, target_pages):
    """Estimate whether a profile fits within the target page count.

    Breaks down content into line-equivalent units and compares the total
    against the layout budget. Useful before running --auto-fit to understand
    how much content needs to be trimmed.

    Exits 0 if the profile fits, 3 if it overflows.

    \b
    Example:
      paperwork estimate --profile me.yaml --template classic
      paperwork estimate --profile me.yaml --template classic --target-pages 2
      paperwork estimate --profile me.yaml --template classic | jq '.fits'
    """
    _validate_slug(template)
    profile = _validate_path(profile)

    try:
        cv_data = load_profile(profile)
    except ProfileLoadError as e:
        _err(
            ExitCode.PROFILE_LOAD_ERROR,
            "profile_load_error",
            f"Failed to load profile: {profile.name}",
            detail=str(e),
            fix="Check the YAML file for syntax errors.",
        )

    engine = RenderEngine(ctx.obj["templates_dir"])
    meta = engine.registry.get_template(template)

    try:
        layout = meta.get_layout_params()
    except ValueError as e:
        _err(
            ExitCode.ARG_MISUSE,
            "layout_params_missing",
            f"Template '{template}' has no layout_params defined.",
            detail=str(e),
            fix="Add a layout_params block to the template's template.yaml.",
        )

    from .autofit import estimate_all, total_lines

    estimates = estimate_all(cv_data.model_dump(), layout)
    total = total_lines(estimates)
    budget = layout.available_lines(layout.margin_max_mm) * target_pages
    fits = total <= budget

    _out({
        "template": template,
        "profile": str(profile),
        "target_pages": target_pages,
        "budget_lines": round(budget, 1),
        "total_lines": round(total, 1),
        "fits": fits,
        "spare_lines": round(budget - total, 1),
        "breakdown": [
            {"field": e.field, "lines": round(e.lines, 1), "detail": e.detail}
            for e in estimates
        ],
    })

    if not fits:
        sys.exit(ExitCode.VALIDATION_ERROR)
