"""Core rendering engine.

Combines profile data + template to produce PDF bytes.
Pure function interface -- no global state, no singletons.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .filters import register_filters
from ..models.cv import CVData
from ..templates.registry import TemplateRegistry
from ..templates.validator import validate_profile_for_template, ValidationResult


class RenderEngine:
    def __init__(self, templates_dir: Path):
        self._templates_dir = Path(templates_dir)
        self._registry = TemplateRegistry(templates_dir)

    @property
    def registry(self) -> TemplateRegistry:
        return self._registry

    def validate(self, cv_data: CVData, template_slug: str) -> ValidationResult:
        """Validate profile data against a template's requirements."""
        meta = self._registry.get_template(template_slug)
        return validate_profile_for_template(cv_data, meta)

    def render_pdf(
        self,
        cv_data: CVData,
        template_slug: str,
        skip_validation: bool = False,
        css_overrides: list[str] | None = None,
    ) -> bytes:
        """Render CV data to PDF using the specified template.

        Args:
            cv_data: Validated CV data.
            template_slug: Template identifier (e.g., "classic").
            skip_validation: Skip required field validation (for testing).
            css_overrides: Extra CSS strings injected after template CSS
                (e.g., margin overrides from auto-fit).

        Returns:
            PDF file contents as bytes.

        Raises:
            ValidationError: If required fields are missing (unless skip_validation).
            TemplateNotFoundError: If template slug doesn't exist.
        """
        meta = self._registry.get_template(template_slug)
        template_dir = self._registry.get_template_dir(template_slug)

        if not skip_validation:
            result = validate_profile_for_template(cv_data, meta)
            if not result.is_valid:
                raise ValidationError(result.format_errors())

        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html"]),
        )
        register_filters(env)

        template = env.get_template(meta.html_file)
        html_content = template.render(**cv_data.model_dump())

        from weasyprint import HTML, CSS

        css_path = template_dir / meta.css_file
        base_url = template_dir.as_uri() + "/"

        stylesheets = [CSS(str(css_path))]
        if css_overrides:
            for override in css_overrides:
                stylesheets.append(CSS(string=override))

        return HTML(
            string=html_content,
            base_url=base_url,
        ).write_pdf(stylesheets=stylesheets)

    def render_html(
        self,
        cv_data: CVData,
        template_slug: str,
        skip_validation: bool = False,
    ) -> str:
        """Render CV data to HTML string (useful for preview/debugging)."""
        meta = self._registry.get_template(template_slug)
        template_dir = self._registry.get_template_dir(template_slug)

        if not skip_validation:
            result = validate_profile_for_template(cv_data, meta)
            if not result.is_valid:
                raise ValidationError(result.format_errors())

        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html"]),
        )
        register_filters(env)

        template = env.get_template(meta.html_file)
        return template.render(**cv_data.model_dump())


class ValidationError(Exception):
    """Raised when profile data fails template validation."""
