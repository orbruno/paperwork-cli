# Test Suite — Requirements

**Version**: 1.0
**Created**: 2026-05-12
**Author**: Orlando Bruno
**Status**: Draft
**Phase**: 1 of 3 (Requirements)

---

## Source Document

- **PRD Reference**: `../../01_PRD/prd.md`
- **Initiative**: NFR-10 — 80% test coverage across engine, CLI, and API

---

## Overview

This spec defines the requirements for the Paperwork test suite — the first test infrastructure for the project. It covers what must be tested, at what coverage threshold, with what tooling, and under what constraints. The test suite must be runnable from a single command (`uv run pytest`) and must integrate with CI without requiring a display server or PDF-capable system library.

The suite spans four layers: unit tests for pure functions and data models, integration tests for the rendering engine and profile loader, API tests via FastAPI's `TestClient`, and CLI tests via Click's `CliRunner`. PDF generation via WeasyPrint is explicitly excluded from CI targets due to system dependency constraints (see Constraints).

---

## Problem Statement

Paperwork has zero test files. The codebase has grown to 21 Python source files across six modules (models, profiles, templates, engine, autofit, api, cli). Every non-trivial change — new template, new trim strategy, new API endpoint — carries regression risk that is currently caught only by manual testing.

Specific risks of the untested state:

- `load_profile()` in `profiles/loader.py` raises `ProfileLoadError` for missing files, bad YAML, and schema violations. None of these error paths are verified. A future change to exception handling could silently swallow errors.
- `_resolve_field()` in `templates/validator.py` uses dot-notation path resolution that must correctly handle nested dicts, empty lists, and `None` values. This logic is subtle and has no regression coverage.
- `estimate_all()` and `total_lines()` in `autofit/estimator.py` are pure functions with deterministic inputs — ideal for parameterized unit tests — but currently untestable without a test harness.
- The `optimize()` function in `autofit/optimizer.py` orchestrates two phases with early-exit conditions and immutable dict operations. The phase interaction logic is the most complex in the codebase and has no snapshot tests.
- The FastAPI routes in `api/routes.py` return different status codes (200, 400, 404, 422) depending on engine state. These response codes are unverified.
- The CLI in `cli.py` has five commands with option parsing, environment variable fallback, and multiple error paths. None are exercised by automated tests.

NFR-10 in the PRD mandates 80% coverage. The current state (0%) violates this requirement as of project inception.

---

## User Stories

### US-T01: Run the full test suite with a single command

> As a developer working on Paperwork,
> I want to run all tests with `uv run pytest tests/`,
> so that I can verify correctness without any manual setup.

**Acceptance criteria**:
- `uv run pytest tests/` exits 0 when all tests pass.
- No test requires manual intervention, a running server, or a display.
- Tests complete in under 60 seconds on a standard developer machine.

### US-T02: See coverage after every run

> As a developer,
> I want coverage reported automatically after each test run,
> so that I can see which lines remain uncovered without running a separate command.

**Acceptance criteria**:
- `uv run pytest tests/ --cov=src/paperwork --cov-report=term-missing` shows per-file coverage.
- `--cov-fail-under=80` causes pytest to exit non-zero if total coverage drops below 80%.

### US-T03: Reproduce a bug with a failing test

> As a developer investigating a regression,
> I want to write a focused test that targets a specific function,
> so that I can confirm the bug before fixing it and prevent recurrence.

**Acceptance criteria**:
- Each test module maps 1:1 to a source module (e.g., `tests/unit/test_loader.py` tests `profiles/loader.py`).
- Tests use plain `pytest` assertions without additional assertion libraries.
- Fixtures provide minimal, valid CVData and template data without requiring real files.

### US-T04: CI passes without WeasyPrint system dependencies

> As a developer running CI on a minimal Linux image,
> I want the test suite to pass without installing system-level WeasyPrint dependencies (Pango, Cairo, etc.),
> so that CI configuration remains simple and fast.

**Acceptance criteria**:
- No test that runs in CI calls `engine.render_pdf()` without mocking or skipping WeasyPrint.
- `render_html()` is tested in CI (Jinja2 only, no WeasyPrint).
- PDF render tests are marked `@pytest.mark.slow` and excluded from default CI runs.

### US-T05: Add a new template and have tests catch regressions

> As a template author adding a new template pack,
> I want the test suite to verify that the registry discovers it and validator evaluates it correctly,
> so that I do not accidentally break existing template behavior.

**Acceptance criteria**:
- `tests/unit/test_registry.py` tests `TemplateRegistry._scan()` with a fixture template directory.
- `tests/unit/test_validator.py` parameterizes required-field and optional-field scenarios.
- Fixture template directory uses the real `templates/classic/` structure as reference.

---

## Requirements

### Functional Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| FR-T01 | The test suite must include unit tests for all functions in `autofit/estimator.py`: `estimate_all()`, `total_lines()`, `estimate_section()`, and all private `_estimate_*` helpers. | NFR-10 |
| FR-T02 | The test suite must include unit tests for all pure functions in `autofit/css_override.py` (`margin_override()`), `engine/filters.py` (`base_url_filter()`), and `autofit/optimizer.py` private helpers (`_phase_margins()`, `_phase_trim()`). | NFR-10 |
| FR-T03 | The test suite must test `profiles/loader.py` `load_profile()` for: valid YAML, valid JSON, missing file (raises `ProfileLoadError`), malformed YAML (raises `ProfileLoadError`), unsupported extension (raises `ProfileLoadError`), and schema violation (raises `ProfileLoadError`). | NFR-10, US-T03 |
| FR-T04 | The test suite must test `templates/registry.py` `TemplateRegistry` for: scanning a directory with one valid template, scanning an empty directory, `get_template()` with valid slug, `get_template()` with unknown slug (raises `TemplateNotFoundError`), and `get_template_dir()` path resolution. | NFR-10 |
| FR-T05 | The test suite must test `templates/validator.py` `validate_profile_for_template()` for: all required fields present (valid), one required field missing (invalid), empty list field treated as missing, `None` field treated as missing, and optional fields reported correctly. | NFR-10 |
| FR-T06 | The test suite must test `models/cv.py` Pydantic models: `CVData` instantiation with full data, `CVData` with only required fields (`name`), nested model construction (`ContactInfo`, `Education`, `WorkExperience`, `CompetencyGroup`, `Language`, `Certification`). | NFR-10 |
| FR-T07 | The test suite must test `models/template_meta.py` `TemplateMeta`: `get_layout_params()` with `layout_params` defined, `get_layout_params()` when `layout_params` is `None` (raises `ValueError`), and `_coerce_layout_params` validator pass-through. | NFR-10 |
| FR-T08 | The test suite must test `autofit/models.py` dataclasses: `LayoutParams.available_lines()` (numeric correctness), `LayoutParams.chars_for_margin()` (proportional scaling), `TrimRule.from_dict()` for each `TrimStrategy`, and `LayoutParams.from_dict()` with trim_rules. | NFR-10 |
| FR-T09 | The test suite must test `engine/renderer.py` `RenderEngine.render_html()` end-to-end (Jinja2 only, no WeasyPrint): output is a non-empty string, output contains the CV name, and `ValidationError` is raised when required fields are missing. | NFR-10, US-T04 |
| FR-T10 | The test suite must test all FastAPI routes in `api/routes.py` via `httpx.AsyncClient` or `TestClient`: `GET /` health, `GET /templates`, `POST /render` success, `POST /render` with unknown template (404), `POST /render` with invalid body (422), `GET /render/{profile_slug}` success, `GET /render/{profile_slug}` missing profile (404), and `POST /render-cv` legacy endpoint. | NFR-10 |
| FR-T11 | The test suite must test CLI commands in `cli.py` via Click's `CliRunner`: `templates` lists output, `validate` success and failure exit codes, `estimate` output format, and `preview` creates a temp HTML file. The `generate` command with `render_pdf` must mock WeasyPrint. | NFR-10, US-T04 |
| FR-T12 | The `conftest.py` must provide shared fixtures: `sample_cv_data` (a valid `CVData` instance), `sample_cv_dict` (the dict form), `fixture_templates_dir` (a `tmp_path` directory with a minimal template), `sample_profile_yaml` (a `tmp_path` YAML file), and `sample_layout_params` (a default `LayoutParams` instance). | US-T01, US-T03 |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-T01 | Total test coverage for `src/paperwork/` must reach 80% or higher, measured by `pytest-cov`. | 80% |
| NFR-T02 | The full test suite (excluding `@pytest.mark.slow`) must complete in under 60 seconds on a developer MacBook (Apple Silicon). | < 60s |
| NFR-T03 | Tests must be hermetic: no network calls, no real file system side effects outside `tmp_path`, no ports opened. | 100% |
| NFR-T04 | Tests must run with `uv run pytest tests/` — no other setup step required after `uv sync --extra dev`. | Single command |
| NFR-T05 | CI must pass without WeasyPrint system libraries. PDF render paths must be skipped via `@pytest.mark.slow` or mocked. | CI-safe |
| NFR-T06 | Every test file must have a module-level docstring describing what it tests. | All files |
| NFR-T07 | Test functions must follow the Arrange-Act-Assert (AAA) pattern with blank lines separating each phase. | All tests |

---

## Success Criteria

- [ ] `uv run pytest tests/ --cov=src/paperwork --cov-fail-under=80` exits 0.
- [ ] No test imports WeasyPrint at module level.
- [ ] All six routes in `api/routes.py` have at least one test case.
- [ ] All five CLI commands in `cli.py` have at least one test case.
- [ ] `load_profile()` has tests for all four error paths (missing file, bad YAML, unsupported extension, schema violation).
- [ ] `validate_profile_for_template()` has parameterized tests covering required-present, required-missing, and optional scenarios.
- [ ] `estimate_all()` and `total_lines()` have numerical correctness assertions.
- [ ] A CI configuration comment in the test README documents the `--cov-fail-under=80` flag.

---

## Constraints

**WeasyPrint system dependencies**: WeasyPrint requires Pango, Cairo, GDK-PixBuf, and libffi as native libraries. These are not available in a minimal Linux CI container without explicit installation. Tests that invoke `render_pdf()` must either mock WeasyPrint or be marked `@pytest.mark.slow` and excluded from default CI runs. Only `render_html()` (Jinja2 only) is safe to call in CI.

**uv-only tooling**: The project uses `uv` exclusively. No `pip install`, no bare `python -m pytest`. All dependency changes must be made in `pyproject.toml` under the `[project.optional-dependencies]` `dev` key, then resolved with `uv sync --extra dev`.

**Python 3.11+**: Test code must be compatible with Python 3.11. No use of `match/case` or other 3.10+ syntax that is not supported in 3.11.

**Pydantic v2**: Fixtures must use Pydantic v2 APIs (`model_dump()`, not `.dict()`). No Pydantic v1 compatibility shims.

**No test database**: There is no database. Profile data is file-based. Tests must use `tmp_path` (pytest built-in) for any file I/O. No global test directories that persist between runs.

**FastAPI `api` extra required**: The FastAPI routes test requires the `api` optional dependency group (`fastapi[standard]`, `uvicorn`). `httpx` must be added to the `dev` group for the TestClient transport. Tests that import from `paperwork.api` must be skipped or conditional if the `api` extra is not installed.

---

## Out of Scope

- **End-to-end browser tests**: No Playwright or Selenium. The HTML output is tested as a string, not rendered in a browser.
- **Visual regression tests**: No pixel-level PDF comparison. PDF correctness is left to manual inspection.
- **Load / performance tests**: No `locust` or `k6` benchmarks. The sub-60-second suite runtime is an internal constraint, not a benchmark target.
- **Windows CI**: Windows is not a supported platform (PRD §3). No Windows-specific test paths.
- **Template authoring tests**: No tests verify that `cv.scss` compiles correctly or that `cv.html` passes W3C validation.
- **Profile generation quality tests**: No tests verify that LLM-generated YAML profiles are semantically correct.

---

## Dependencies

| Dependency | Version Constraint | Purpose | Already in pyproject.toml? |
|---|---|---|---|
| `pytest` | `>=8.0` | Test runner | Yes (dev group) |
| `pytest-cov` | `>=5.0` | Coverage measurement | No — must add |
| `httpx` | `>=0.27` | FastAPI TestClient transport | No — must add |
| `ruff` | `>=0.5.0` | Linting (already present) | Yes (dev group) |
| `fastapi[standard]` | `>=0.116.1` | API routes under test | Yes (api group) |
| Fixture template directory | — | `templates/classic/` (already in repo root) | Yes |

`pyproject.toml` change required:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "httpx>=0.27",
    "ruff>=0.5.0",
]
```

---

## Related Documents

- PRD: `../../01_PRD/prd.md`
- Design spec: `./02_design.md`
- Tasks spec: `./03_tasks.md`
- Source: `src/paperwork/` (all modules)

---

## Change Log

| Date | Version | Author | Change |
|------|---------|--------|--------|
| 2026-05-12 | 1.0 | Orlando Bruno | Initial draft |

**Last Updated**: 2026-05-12
