# GET /templates/{slug}/spec — Tasks

**Version**: 1.0
**Created**: 2026-05-12
**Author**: Orlando Bruno
**Status**: Draft
**Phase**: 3 of 3 (Tasks)

---

## Dependency Order

```
T1 (read routes.py)
    └── T2 (add route to routes.py)
            └── T3 (write tests)
                    └── T4 (run tests)
                            └── T5 (verify no path leakage)
```

T1 has no prerequisites. Each subsequent task depends on the one before it.

---

## Estimates

| Task | Story Points |
|------|-------------|
| T1 | 0 (read-only, no change) |
| T2 | 1 |
| T3 | 2 |
| T4 | 1 |
| T5 | 1 |
| Total | 5 |

---

## T1 — Read `routes.py` to confirm current route list and router setup

**Files**: `src/paperwork/api/routes.py` (read only)

Confirm before writing any code:

1. The file imports `Response` from `fastapi.responses` and `HTTPException` from `fastapi`.
2. `TemplateNotFoundError` is imported from `..templates.registry`.
3. `create_router(engine: RenderEngine, profiles_dir: Path)` is the factory function.
4. The current route list is: `GET /`, `GET /templates`, `POST /render`, `POST /render-cv`, `GET /render/{profile_slug}`.
5. No `GET /templates/{slug}/spec` route exists yet.

Acceptance check: all five points confirmed by reading the file. No change made.

---

## T2 — Add `GET /templates/{slug}/spec` route to `create_router()`

**File**: `src/paperwork/api/routes.py`

Insert the following function after the `list_templates` route and before the `render` route. No new imports are needed.

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

The resulting route order inside `create_router()`:

```
GET /
GET /templates
GET /templates/{slug}/spec    ← new
POST /render
POST /render-cv
GET /render/{profile_slug}
```

Acceptance check:
- `src/paperwork/api/routes.py` contains the `get_template_spec` function.
- The function is registered as `@router.get("/templates/{slug}/spec")`.
- No new import statements were added to the file.
- The file passes a `ruff check` with no errors: `uv run ruff check src/paperwork/api/routes.py`.

---

## T3 — Write `tests/api/test_spec_endpoint.py` with all four test cases

**File**: `tests/api/test_spec_endpoint.py` (create; create `tests/api/__init__.py` if the directory does not exist)

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
    """Scaffold a bare-minimum template directory under root."""
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
    """404: slug not registered — lists available slugs with no absolute paths."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    _write_template(templates_dir, "classic", CLASSIC_MANIFEST, SPEC_CONTENT)

    client = _make_client(templates_dir, tmp_path)
    response = client.get("/templates/nonexistent/spec")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "nonexistent" in detail["error"]
    assert "classic" in detail["available"]
    # No absolute filesystem paths in the available list
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
    """500: spec_file declared in template.yaml but file is absent from disk."""
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

Acceptance check:
- File exists at `tests/api/test_spec_endpoint.py`.
- `tests/api/__init__.py` exists (empty file is fine).
- Four test functions present: `test_get_spec_200`, `test_get_spec_404_unknown_slug`, `test_get_spec_404_no_spec_file`, `test_get_spec_500_missing_file`.
- File passes `ruff check tests/api/test_spec_endpoint.py` with no errors.

---

## T4 — Run tests

**Command**:

```bash
uv run pytest tests/api/test_spec_endpoint.py -v
```

Expected output:

```
tests/api/test_spec_endpoint.py::test_get_spec_200 PASSED
tests/api/test_spec_endpoint.py::test_get_spec_404_unknown_slug PASSED
tests/api/test_spec_endpoint.py::test_get_spec_404_no_spec_file PASSED
tests/api/test_spec_endpoint.py::test_get_spec_500_missing_file PASSED

4 passed in 0.XXs
```

Acceptance check: all four tests pass with exit code 0. No skips. No warnings about missing fixtures.

If any test fails:
1. Read the failure traceback to identify which assertion failed.
2. Cross-reference with the route implementation in T2 — the most likely causes are a mismatched detail key name (`"error"` vs a string) or the `Content-Type` header casing.
3. Fix the implementation (not the tests) unless the test assertion is provably wrong.

---

## T5 — Verify no absolute paths leak in error responses

**Method**: manual `curl` verification after starting the server locally.

```bash
# Start the server
uv sync --extra api
uv run uvicorn paperwork.api.app:app --reload --port 8000
```

In a separate terminal:

```bash
# 1. Confirm 200 + correct Content-Type
curl -si http://localhost:8000/templates/classic/spec | head -5
# Expected headers include: content-type: text/plain; charset=utf-8

# 2. Confirm 404 for unknown slug — check for no filesystem paths
curl -s http://localhost:8000/templates/does-not-exist/spec
# Expected: {"detail":{"error":"Template 'does-not-exist' not found.","available":["classic"]}}
# Must NOT contain: /app/templates, /Users/, /home/, or any absolute path

# 3. Confirm GET /templates regression (no change to existing behavior)
curl -s http://localhost:8000/templates | python3 -m json.tool | head -10
# Expected: JSON array containing classic template metadata with spec_file field present
```

Acceptance check:
- Step 1: `content-type: text/plain; charset=utf-8` present in response headers.
- Step 2: No absolute path string (`/app`, `/Users`, `/home`, `C:\\`) appears anywhere in the 404 response body.
- Step 3: `GET /templates` returns the same structure as before T2 (no regression).

---

## Pre-merge Checklist

- [ ] T1: current route list in `routes.py` confirmed before making changes
- [ ] T2: `get_template_spec` added after `list_templates`, before `render`
- [ ] T2: no new imports added to `routes.py`
- [ ] T2: `ruff check` passes on `routes.py`
- [ ] T3: four test functions present in `tests/api/test_spec_endpoint.py`
- [ ] T3: `ruff check` passes on the test file
- [ ] T4: all four tests pass (`uv run pytest tests/api/test_spec_endpoint.py -v`)
- [ ] T5: `curl` 404 response contains no absolute filesystem path
- [ ] T5: `GET /templates` regression check passes

---

**Last Updated**: 2026-05-12 by Orlando Bruno
