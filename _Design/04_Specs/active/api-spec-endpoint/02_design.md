# GET /templates/{slug}/spec — Design

**Version**: 1.0
**Created**: 2026-05-12
**Author**: Orlando Bruno
**Status**: Draft
**Phase**: 2 of 3 (Design)

---

## 1. Route Implementation

The route is added inside `create_router()` in `src/paperwork/api/routes.py`. No new imports are required — `Response`, `HTTPException`, `Path`, and `TemplateNotFoundError` are all already imported at the top of the file.

```python
@router.get("/templates/{slug}/spec")
def get_template_spec(slug: str):
    """Return the raw spec.yaml content for the given template as plain text.

    Used by LLMs and automation clients to fetch the field schema
    before generating a profile for POST /render.
    """
    # --- 404: unknown slug ---
    try:
        meta = engine.registry.get_template(slug)
    except TemplateNotFoundError:
        available = sorted(t.slug for t in engine.registry.list_templates())
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Template '{slug}' not found.",
                "available": available,
            },
        )

    # --- 404: no spec_file declared ---
    if not meta.spec_file:
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Template '{slug}' has no spec file defined.",
            },
        )

    # --- 500: spec_file declared but missing from disk ---
    template_dir = engine.registry.get_template_dir(slug)
    spec_path = template_dir / meta.spec_file
    if not spec_path.exists():
        raise HTTPException(
            status_code=500,
            detail={
                "error": (
                    f"Template '{slug}' declares spec_file '{meta.spec_file}' "
                    "but the file is missing from the template package. "
                    "This is a server configuration error."
                ),
            },
        )

    # --- 200: return raw text ---
    content = spec_path.read_text(encoding="utf-8")
    return Response(content=content, media_type="text/plain; charset=utf-8")
```

Design notes:
- `TemplateRegistry.get_template()` raises `TemplateNotFoundError` on unknown slug. The catch block re-raises as `HTTPException` with a structured detail dict so the available slugs are machine-readable — not embedded in a string.
- `TemplateRegistry.get_template_dir(slug)` is called after the slug check, so it never executes on an unknown slug (it internally calls `get_template()` again, which would raise).
- The 500 detail includes only the declared filename (`meta.spec_file`), never the resolved absolute path, satisfying NFR-09.
- `spec_path.read_text(encoding="utf-8")` — explicit encoding prevents platform-dependent defaults.
- Path traversal is not a concern: `meta.spec_file` is a server-side value from `template.yaml`; no user-supplied path component reaches the filesystem beyond the slug, which is validated by the registry.

---

## 2. Error Cases

| Condition | HTTP Status | Response body |
|-----------|-------------|---------------|
| Slug resolves, `spec_file` declared, file exists | `200 OK` | Raw UTF-8 text of the spec file. `Content-Type: text/plain; charset=utf-8`. No JSON wrapping. |
| `slug` not in the template registry | `404 Not Found` | `{"detail": {"error": "Template '{slug}' not found.", "available": ["classic", ...]}}` — slugs only, no paths. |
| Slug resolves but `TemplateMeta.spec_file` is `null` | `404 Not Found` | `{"detail": {"error": "Template '{slug}' has no spec file defined."}}` |
| `spec_file` declared in `template.yaml` but file absent from disk | `500 Internal Server Error` | `{"detail": {"error": "Template '{slug}' declares spec_file '{filename}' but the file is missing from the template package. This is a server configuration error."}}` |

The `available` list in the 404-unknown-slug case contains only slug strings, never filesystem paths (NFR-09 / NFR-18.3). The 500 detail includes only the declared filename (e.g. `"spec.yaml"`), not the resolved absolute path.

---

## 3. Integration Point

Add the route **directly after `list_templates()`** and **before `render()`** inside `create_router()`. This keeps all template-related `GET` routes grouped together before the `POST /render` family.

```python
def create_router(engine: RenderEngine, profiles_dir: Path) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    def health(): ...

    @router.get("/templates")
    def list_templates(): ...

    # ← INSERT get_template_spec HERE

    @router.post("/render")
    def render(...): ...

    @router.post("/render-cv")
    def render_cv_legacy(...): ...

    @router.get("/render/{profile_slug}")
    def render_from_profile(...): ...

    return router
```

FastAPI matches routes in registration order. The `/templates/` prefix is entirely distinct from `/render/`, so there is no path ambiguity regardless of placement order relative to `render_from_profile`.

---

## 4. Test Design

Tests live at `tests/api/test_spec_endpoint.py`. The module uses FastAPI's `TestClient` from `starlette.testclient` (available via `fastapi[standard]`, already in the `api` extra). Each test function uses `tmp_path` to build a minimal, isolated template directory — no dependency on the real `templates/` directory on disk.

```python
"""Tests for GET /templates/{slug}/spec endpoint."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from paperwork.engine.renderer import RenderEngine
from paperwork.api.routes import create_router


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SPEC_CONTENT = "template: classic\nfields:\n  name:\n    required: true\n    type: string\n"

CLASSIC_MANIFEST = (
    "name: Classic\n"
    "slug: classic\n"
    "version: 1.0.0\n"
    "html_file: cv.html\n"
    "css_file: cv.css\n"
    "spec_file: spec.yaml\n"
)

MINIMAL_MANIFEST = (
    "name: Minimal\n"
    "slug: minimal\n"
    "version: 1.0.0\n"
    "html_file: cv.html\n"
    "css_file: cv.css\n"
    # spec_file intentionally absent
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_template(root, slug: str, manifest: str, spec_content: str | None = None):
    """Scaffold a bare-minimum template directory."""
    tdir = root / slug
    tdir.mkdir()
    (tdir / "template.yaml").write_text(manifest)
    (tdir / "cv.html").write_text("<html></html>")
    (tdir / "cv.css").write_text("")
    if spec_content is not None:
        (tdir / "spec.yaml").write_text(spec_content)


def _make_client(templates_dir, tmp_path) -> TestClient:
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir(exist_ok=True)
    engine = RenderEngine(templates_dir)
    app = FastAPI()
    app.include_router(create_router(engine, profiles_dir))
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_spec_200(tmp_path):
    """200: existing slug with spec_file declared and file present on disk."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    _write_template(templates_dir, "classic", CLASSIC_MANIFEST, SPEC_CONTENT)

    client = _make_client(templates_dir, tmp_path)
    response = client.get("/templates/classic/spec")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == SPEC_CONTENT


def test_get_spec_404_unknown_slug(tmp_path):
    """404: slug not registered — response lists available slugs, no absolute paths."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    _write_template(templates_dir, "classic", CLASSIC_MANIFEST, SPEC_CONTENT)

    client = _make_client(templates_dir, tmp_path)
    response = client.get("/templates/nonexistent/spec")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "nonexistent" in detail["error"]
    assert "classic" in detail["available"]
    # No absolute filesystem paths in the response
    for slug in detail["available"]:
        assert "/" not in slug
        assert "\\" not in slug


def test_get_spec_404_no_spec_file(tmp_path):
    """404: slug resolves but template.yaml has no spec_file field."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    _write_template(templates_dir, "minimal", MINIMAL_MANIFEST)

    client = _make_client(templates_dir, tmp_path)
    response = client.get("/templates/minimal/spec")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "minimal" in detail["error"]
    assert "no spec file" in detail["error"].lower()


def test_get_spec_500_missing_file(tmp_path):
    """500: spec_file declared in template.yaml but the file is absent from disk."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    # Write manifest declaring spec_file but do NOT create spec.yaml
    _write_template(templates_dir, "classic", CLASSIC_MANIFEST, spec_content=None)

    client = _make_client(templates_dir, tmp_path)
    response = client.get("/templates/classic/spec")

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert "classic" in detail["error"]
    # Must not expose absolute filesystem path (NFR-09)
    assert str(templates_dir) not in detail["error"]
```

Test-to-requirement mapping:

| Test function | Condition covered | Expected status |
|---------------|------------------|----------------|
| `test_get_spec_200` | Valid slug, `spec_file` declared, file on disk | 200 |
| `test_get_spec_404_unknown_slug` | Slug not in registry; available list, no paths | 404 |
| `test_get_spec_404_no_spec_file` | Slug valid, `spec_file` is null | 404 |
| `test_get_spec_500_missing_file` | `spec_file` declared, file absent from disk | 500 |

Fixture notes:
- `_write_template` creates only the files each scenario needs. `cv.html` and `cv.css` are placeholders that satisfy `TemplateRegistry._scan()` without triggering WeasyPrint rendering.
- `_make_client` wires `RenderEngine` → `TemplateRegistry` → `create_router()` → `TestClient` the same way `create_app()` does in production, with no mocking.
- `test_get_spec_500_missing_file` passes `spec_content=None` to `_write_template`, so `spec.yaml` is absent from disk while `template.yaml` still declares `spec_file: spec.yaml`.

Run with:

```bash
uv run pytest tests/api/test_spec_endpoint.py -v
```

---

## 5. Sequence Diagram

```mermaid
sequenceDiagram
    participant Client as HTTP Client<br/>(LLM / curl)
    participant Router as FastAPI Router<br/>GET /templates/{slug}/spec
    participant Registry as TemplateRegistry
    participant Disk as Filesystem

    Client->>Router: GET /templates/classic/spec

    Router->>Registry: get_template("classic")
    alt slug not in registry
        Registry-->>Router: raises TemplateNotFoundError
        Router-->>Client: 404 {"error": "Template 'classic' not found.", "available": [...]}
    else slug found
        Registry-->>Router: TemplateMeta (spec_file="spec.yaml")
    end

    Router->>Router: check meta.spec_file is not None
    alt spec_file is null
        Router-->>Client: 404 {"error": "Template 'classic' has no spec file defined."}
    end

    Router->>Registry: get_template_dir("classic")
    Registry-->>Router: Path(".../templates/classic")

    Router->>Disk: (template_dir / "spec.yaml").exists()
    alt file missing from disk
        Disk-->>Router: False
        Router-->>Client: 500 {"error": "Template 'classic' declares spec_file 'spec.yaml' but the file is missing..."}
    else file present
        Disk-->>Router: True
        Router->>Disk: read_text("utf-8")
        Disk-->>Router: raw YAML string
        Router-->>Client: 200 Content-Type: text/plain; charset=utf-8<br/>body: raw spec.yaml content
    end
```

---

## 6. Design Rationale

Three response format options were evaluated before choosing `text/plain`.

- **Option A (chosen): Raw YAML as `text/plain; charset=utf-8`** — LLMs consume YAML natively. YAML comments in `spec.yaml` carry layout constraints that are not representable in parsed form; returning raw text preserves them verbatim. No server-side parsing step means no parse failures and no serialisation round-trip that could alter content. `curl` output is immediately human-readable. `application/yaml` is not IANA-registered; `text/plain` has broader client compatibility.
- **Option B: Parse YAML, return JSON** — loses all comments, which are a primary documentation mechanism in `spec.yaml`. Adds a parse step with no functional benefit for LLM consumers.
- **Option C: `application/octet-stream` download** — forces clients to write to disk before reading; inferior ergonomics for programmatic use and `curl` pipelines.

The 404-unknown-slug detail uses a structured dict (`{"error": ..., "available": [...]}`) rather than a plain string, consistent with how `TemplateRegistry.get_template()` error messages are formatted in the rest of the routes and making the available list machine-readable for client automation.

---

**Last Updated**: 2026-05-12 by Orlando Bruno
