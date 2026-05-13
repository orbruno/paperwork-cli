# paperwork-cli

PDF generation engine for CVs/resumes. Takes **profile data** (YAML/JSON) + **template packs** (HTML/CSS) and produces high-quality PDFs via Jinja2 + WeasyPrint.

This is the **engine only** — templates and profiles live externally.

## Install

```bash
uv sync
```

## CLI Usage

Templates dir is resolved in order: `--templates-dir` flag > `RENDERCV_TEMPLATES_DIR` env var > `./templates/` in cwd.

```bash
# Point to external templates
paperwork --templates-dir ~/path/to/templates generate -p profile.yaml -t classic -o cv.pdf

# Or set env var
export RENDERCV_TEMPLATES_DIR=~/Documents/Areas/Professional/Tools/RenderCV/templates
paperwork templates
paperwork validate -p profile.yaml -t classic
paperwork generate -p profile.yaml -t classic -o cv.pdf
paperwork preview -p profile.yaml -t classic

# Or cd into a directory that has a templates/ folder
cd ~/Documents/Areas/Professional/Tools/RenderCV
paperwork templates
```

## HTTP API (optional extra)

```bash
uv sync --extra api

RENDERCV_TEMPLATES_DIR=/path/to/templates \
    uv run uvicorn paperwork.api.app:app --host 0.0.0.0 --port 8000
```

Endpoints:
- `GET /` — health check
- `GET /templates` — list templates
- `GET /templates/{slug}/spec` — return raw spec.yaml for a template *(pending)*
- `POST /render` — render from JSON body
- `POST /render-cv` — legacy endpoint (backward compatible)
- `GET /render/{profile_slug}` — render stored profile

## Using as a Package

```python
from paperwork.engine import RenderEngine
from paperwork.profiles import load_profile

engine = RenderEngine(templates_dir="path/to/templates")
cv_data = load_profile("profile.yaml")
pdf_bytes = engine.render_pdf(cv_data, "classic")
```

## System Requirements

WeasyPrint needs system libraries:
- **macOS**: `brew install pango glib cairo` (auto-detected by CLI)
- **Linux**: `apt-get install libpango-1.0-0 libcairo2`
- **Docker**: Handled by Dockerfile

## Current Status

**Phase**: Design complete — ready for implementation
**Last updated**: 2026-05-12

- Full SDD in place: PRD (19 FRs, 10 NFRs, 6 Goals), 10 ADRs, 3 feature specs
- Classic template production-ready (photo field, certifications section, spec.yaml)
- Implementation queue: test suite → `GET /templates/{slug}/spec` → minimal + modern templates
