# Additional Template Designs — Tasks

**Version**: 1.0
**Created**: 2026-05-12
**Author**: Orlando Bruno
**Status**: Draft
**Phase**: 3 of 3 (Tasks)

---

## Overview

These tasks implement the `minimal` and `modern` template packs as specified in `02_design.md`. All work is purely filesystem-level: new directories and files under `templates/`. No engine Python source files are modified.

Tasks 1–5 cover `minimal`. Tasks 6–10 cover `modern`. Task 11 verifies both.

---

## Task 1 — Create `templates/minimal/` directory structure

**ID**: T-MIN-01
**Files to create**: `templates/minimal/` (directory only)

### Steps

```bash
mkdir -p templates/minimal
```

### Acceptance check

```bash
test -d templates/minimal && echo "OK"
```

---

## Task 2 — Write `templates/minimal/template.yaml`

**ID**: T-MIN-02
**File**: `templates/minimal/template.yaml`

### Key design decisions

- `slug: "minimal"` — matches directory name, used as the `-t` flag value.
- `page_size: "A4"` — 210 x 297mm.
- `supports_photo: false` — the template has no `<img>` element; this flag prevents the engine from warning about a missing photo.
- `required_fields` lists `name`, `contact_info`, `education`, `work_experience` — same contract as `classic`.
- `layout_params` defines A4 geometry (`page_width_mm: 210`, `page_height_mm: 297`) with tight margins (min 10mm, max 15mm) and `chars_per_line: 105` reflecting the wider printable area of A4 at 1.5cm margins.
- `trim_rules` cover all variable-length sections; `profile` uses `truncate_words` with `min_words: 30`.

### Content

See `02_design.md` §2.4 for the full YAML content.

### Acceptance check

```bash
uv run python -c "
import yaml
from src.paperwork.models.template_meta import TemplateMeta
with open('templates/minimal/template.yaml') as f:
    data = yaml.safe_load(f)
meta = TemplateMeta(**data)
assert meta.slug == 'minimal'
assert meta.supports_photo == False
assert meta.page_size == 'A4'
lp = meta.get_layout_params()
assert lp.chars_per_line == 105
print('OK')
"
```

---

## Task 3 — Write `templates/minimal/cv.html`

**ID**: T-MIN-03
**File**: `templates/minimal/cv.html`

### Key design decisions

- No `<img>` element anywhere in the file — enforces `supports_photo: false`.
- Header: full-width `<div class="header">` with `<h1>{{ name }}</h1>`, optional titles, and a single contact line using `{% if %}` guards for every `contact_info` sub-field.
- Section heading row: `<div class="section__heading-row">` contains `<h2 class="section__heading">` and `<span class="section__rule"></span>`. CSS renders these as two `display: table-cell` elements — heading shrinks to content width, rule spans the remainder as a bottom border. This avoids `flexbox gap`.
- Skills: rendered as inline grouped text using a `{% for item in competencies_and_skills[:9] %}` loop. Each group: `<strong>{{ item.competency }}:</strong> {{ item.skills | join(', ') }}`. Groups separated by a mid-dot entity.
- Education and experience: `<table class="entry-table">` with `<td class="entry-table__date">` (80px) and `<td class="entry-table__detail">`. Uses HTML table layout — no CSS Grid or flexbox.
- All optional sections (`profile`, `competencies_and_skills`, `languages`, `certifications`) are guarded with `{% if field %}...{% endif %}`.

### Content

See `02_design.md` §2.2 for the full HTML content.

### Acceptance check

```bash
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates/minimal'))
env.filters['base_url'] = lambda url: url
tmpl = env.get_template('cv.html')
assert '<img' not in tmpl.source
print('No img element: OK')
"
```

---

## Task 4 — Write `templates/minimal/cv.css`

**ID**: T-MIN-04
**File**: `templates/minimal/cv.css`

### Key design decisions

- `@page { size: A4; margin: 1.5cm; }` — the only place page geometry is defined.
- `display: table` / `display: table-cell` for the heading row — no `flexbox gap`, no CSS Grid.
- No colour other than `#1a1a1a` (body text), `#444444` / `#333333` (subdued contact/titles), and `#aaaaaa` (hairline rule). Zero accent colour.
- `font-family: Arial, sans-serif` — available to WeasyPrint without installation.
- No `var()` custom properties anywhere.
- No `position: sticky`.
- `.entry-table` uses `border-collapse: collapse` and vertical `padding-bottom` on cells instead of `gap`.

### Content

See `02_design.md` §2.3 for the full CSS content.

### Acceptance check

```bash
python -c "
css = open('templates/minimal/cv.css').read()
assert 'size: A4' in css, 'missing A4 page size'
assert 'var(' not in css, 'var() found — WeasyPrint incompatible'
assert 'position: sticky' not in css, 'sticky found — WeasyPrint incompatible'
assert 'display: table' in css, 'heading-row table display missing'
print('OK')
"
```

---

## Task 5 — Write `templates/minimal/spec.yaml`

**ID**: T-MIN-05
**File**: `templates/minimal/spec.yaml`

### Key design decisions

- `template: minimal` at root — identifies the owning template.
- Every field referenced in `cv.html` has an entry: `name`, `titles`, `contact_info` (and all six sub-fields), `profile`, `competencies_and_skills` (with `competency` and `skills`), `education` (with all six sub-fields), `work_experience` (with all five sub-fields), `languages` (with two sub-fields), `certifications` (with three sub-fields).
- Each field has `required`, `type`, `description`, and at least one `constraints` entry (e.g. `max_chars`, `max_items`).
- `layout` block at the end documents page geometry and typography constants for LLM context.
- `photo` field is intentionally absent — `minimal` does not render it.

### Content

See `02_design.md` §2.5 for the full YAML content.

### Acceptance check

```bash
python -c "
import yaml
spec = yaml.safe_load(open('templates/minimal/spec.yaml'))
assert spec['template'] == 'minimal'
required_keys = ['name','titles','contact_info','profile',
                 'competencies_and_skills','education',
                 'work_experience','languages','certifications']
for k in required_keys:
    assert k in spec['fields'], f'missing field: {k}'
assert 'photo' not in spec['fields'], 'photo should not appear in minimal spec'
print('OK')
"
```

---

## Task 6 — Create `templates/modern/` directory structure and copy photo asset

**ID**: T-MOD-01
**Files to create**: `templates/modern/` (directory), `templates/modern/assets/` (directory), `templates/modern/assets/profile.jpg` (copied from classic)

### Steps

```bash
mkdir -p templates/modern/assets
cp templates/classic/assets/profile.jpg templates/modern/assets/profile.jpg
```

The `profile.jpg` from `classic` serves as the photo fallback for `modern`. It is a placeholder; users replace it with their own photo path via the `photo` field.

### Acceptance check

```bash
test -f templates/modern/assets/profile.jpg && echo "OK"
```

---

## Task 7 — Write `templates/modern/template.yaml`

**ID**: T-MOD-02
**File**: `templates/modern/template.yaml`

### Key design decisions

- `slug: "modern"` — matches directory name.
- `page_size: "Letter"` — 215.9 x 279.4mm.
- `supports_photo: true` — the template renders a photo when present; falls back to `assets/profile.jpg`.
- `required_fields` identical to `minimal` and `classic`: `name`, `contact_info`, `education`, `work_experience`.
- `layout_params` defines Letter geometry (`page_width_mm: 215.9`, `page_height_mm: 279.4`). `chars_per_line: 98` accounts for the 14px accent bar reducing effective content width. `margin_max_mm: 20` — generous upper bound for auto-fit expansion.
- `trim_rules` are identical to `minimal` — same strategies, same min values.

### Content

See `02_design.md` §3.4 for the full YAML content.

### Acceptance check

```bash
uv run python -c "
import yaml
from src.paperwork.models.template_meta import TemplateMeta
with open('templates/modern/template.yaml') as f:
    data = yaml.safe_load(f)
meta = TemplateMeta(**data)
assert meta.slug == 'modern'
assert meta.supports_photo == True
assert meta.page_size == 'Letter'
lp = meta.get_layout_params()
assert lp.chars_per_line == 98
print('OK')
"
```

---

## Task 8 — Write `templates/modern/cv.html`

**ID**: T-MOD-03
**File**: `templates/modern/cv.html`

### Key design decisions

- Outer structure: `<table class="page-layout">` with one `<tr>` and two `<td>` cells.
  - Left cell: `<td class="accent-bar">` — empty, styled with `background-color: #1e3a5f` in CSS.
  - Right cell: `<td class="content-pane">` — contains all content.
- Photo: `{% if photo %}<div class="header__photo-wrap"><img src="{{ photo }}" ... /></div>{% endif %}` — floated right inside the header div. Falls back to `assets/profile.jpg` is NOT handled in the template; the profile YAML `photo` field should reference `assets/profile.jpg` explicitly when a custom photo is not available, or the field should be omitted and the engine/user is responsible for the fallback path. To keep the template simple and consistent with `classic`, use: `src="{{ photo if photo else 'assets/profile.jpg' }}"`.
- Skills: `{% set ns = namespace(all_skills=[]) %}` loop pools all skills across all competency groups; `ns.all_skills[:15] | join(' &middot; ')` renders the flat list. Competency labels are not displayed.
- Education and experience: `<table class="entry-table">` with `<td class="entry-table__date">` (84px) and `<td class="entry-table__detail">`. Same table-based layout as `minimal`.
- All optional sections guarded with `{% if field %}...{% endif %}`.

### Content

See `02_design.md` §3.2 for the full HTML content.

**Correction to §3.2**: The photo `src` should use the fallback pattern:

```html
<img src="{{ photo if photo else 'assets/profile.jpg' }}" alt="Profile picture" class="header__photo" />
```

Replace the bare `src="{{ photo }}"` shown in §3.2 with this pattern so photo-absent profiles render the placeholder.

### Acceptance check

```bash
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates/modern'))
env.filters['base_url'] = lambda url: url
tmpl = env.get_template('cv.html')
src = tmpl.source
assert 'accent-bar' in src, 'accent-bar cell missing'
assert 'content-pane' in src, 'content-pane cell missing'
assert 'page-layout' in src, 'page-layout table missing'
assert 'assets/profile.jpg' in src, 'photo fallback missing'
print('OK')
"
```

---

## Task 9 — Write `templates/modern/cv.css`

**ID**: T-MOD-04
**File**: `templates/modern/cv.css`

### Key design decisions

- `@page { size: Letter; margin: 0; }` — zero page margin so the accent bar extends to the physical page edge. Internal spacing is applied via `.content-pane` padding.
- `.page-layout { table-layout: fixed; width: 100%; height: 100%; }` — the outer table fills the page.
- `.accent-bar { width: 14px; background-color: #1e3a5f; vertical-align: top; }` — the entire accent colour effect is this one rule.
- `.content-pane { padding: 28px 20px 20px 22px; vertical-align: top; }` — top padding is larger to align visually with a notional 1cm top margin.
- `.section__heading-row { border-bottom: 1.5pt solid #1e3a5f; padding-bottom: 2px; }` — the heading underline replaces the hairline rule used in `minimal`. No `display: table` needed here since there is no trailing rule span.
- `.entry-table__date { color: #1e3a5f; }` — date column rendered in accent colour.
- `.header h1 { color: #1e3a5f; }` — name rendered in accent colour.
- No `var()`, no `position: sticky`, no `flexbox gap`.

### Content

See `02_design.md` §3.3 for the full CSS content.

### Acceptance check

```bash
python -c "
css = open('templates/modern/cv.css').read()
assert 'size: Letter' in css, 'missing Letter page size'
assert '#1e3a5f' in css, 'accent colour missing'
assert 'var(' not in css, 'var() found — WeasyPrint incompatible'
assert 'position: sticky' not in css, 'sticky found — WeasyPrint incompatible'
assert 'accent-bar' in css, 'accent-bar rule missing'
print('OK')
"
```

---

## Task 10 — Write `templates/modern/spec.yaml`

**ID**: T-MOD-05
**File**: `templates/modern/spec.yaml`

### Key design decisions

- `template: modern` at root.
- All fields rendered in `cv.html` are documented: `name`, `titles`, `contact_info` (six sub-fields), `profile`, `photo`, `competencies_and_skills` (with `competency` and `skills`), `education` (six sub-fields), `work_experience` (five sub-fields), `languages` (two sub-fields), `certifications` (three sub-fields).
- `photo` field is included (unlike `minimal`) with a `constraints.note` explaining the 72px circle rendering and square crop requirement.
- `competencies_and_skills` description explicitly states that competency labels are not rendered — only pooled skills appear. This guides LLMs generating profiles for this template.
- `layout` block documents the accent bar width and colour, photo size, and date column width.

### Content

See `02_design.md` §3.5 for the full YAML content.

### Acceptance check

```bash
python -c "
import yaml
spec = yaml.safe_load(open('templates/modern/spec.yaml'))
assert spec['template'] == 'modern'
required_keys = ['name','titles','contact_info','profile','photo',
                 'competencies_and_skills','education',
                 'work_experience','languages','certifications']
for k in required_keys:
    assert k in spec['fields'], f'missing field: {k}'
assert 'photo' in spec['fields'], 'photo must appear in modern spec'
print('OK')
"
```

---

## Task 11 — Verify both templates with `paperwork templates` and `paperwork validate`

**ID**: T-VERIFY-01
**Files**: none created; uses all files from Tasks 1–10 and a standard test profile.

### Pre-condition

A standard test profile must exist at `tests/fixtures/standard_profile.yaml`. If it does not exist, create it with the minimum required fields for all three templates:

```yaml
name: "Jane Smith"
titles:
  - "Senior Data Engineer"
contact_info:
  email: "jane.smith@example.com"
  phone: "+49 151 00000000"
  location: "Berlin, Germany"
  github: "https://github.com/janesmith"
  linkedin: "https://linkedin.com/in/janesmith"
profile: >
  Experienced data engineer with 8 years building scalable pipelines and ML platforms.
  Passionate about clean architecture and open-source tooling.
competencies_and_skills:
  - competency: "Data Engineering"
    skills: ["Python", "dbt", "Spark", "Airflow"]
  - competency: "Cloud & Infra"
    skills: ["AWS", "GCP", "Terraform", "Docker"]
  - competency: "ML Platforms"
    skills: ["MLflow", "Kubeflow", "Feature Store"]
education:
  - year: "2014 – 2016"
    degree: "M.Sc. Computer Science"
    institution: "TU Berlin"
    location: "Berlin, Germany"
    grade: "1.2"
  - year: "2011 – 2014"
    degree: "B.Sc. Mathematics"
    institution: "University of Cologne"
    location: "Cologne, Germany"
work_experience:
  - years: "2021 – Present"
    position: "Senior Data Engineer"
    company: "DataCo GmbH"
    location: "Berlin, Germany"
    roles:
      - "Designed and maintained a real-time Kafka pipeline processing 500k events/day."
      - "Led migration from on-prem Hadoop to GCP Dataproc, reducing cost by 40%."
      - "Mentored 3 junior engineers and established team coding standards."
  - years: "2018 – 2021"
    position: "Data Engineer"
    company: "Analytics AG"
    location: "Hamburg, Germany"
    roles:
      - "Built ETL pipelines in Airflow serving 12 internal BI dashboards."
      - "Introduced dbt for SQL transformation layer, cutting query time by 30%."
languages:
  - language: "English"
    level: "C2 – Fluent"
  - language: "German"
    level: "C1 – Advanced"
certifications:
  - name: "AWS Certified Data Analytics – Specialty"
    issuer: "AWS"
    year: "2023"
  - name: "dbt Developer Certification"
    issuer: "dbt Labs"
    year: "2022"
```

### Verification steps

```bash
# 1. Both templates appear in the registry
uv run paperwork templates | grep -E "minimal|modern"

# 2. Validate against the standard profile
uv run paperwork validate -p tests/fixtures/standard_profile.yaml -t minimal
uv run paperwork validate -p tests/fixtures/standard_profile.yaml -t modern

# 3. Generate PDFs
uv run paperwork generate -p tests/fixtures/standard_profile.yaml -t minimal -o /tmp/test-minimal.pdf
uv run paperwork generate -p tests/fixtures/standard_profile.yaml -t modern  -o /tmp/test-modern.pdf

# 4. Confirm PDFs are non-empty
test -s /tmp/test-minimal.pdf && echo "minimal PDF: OK"
test -s /tmp/test-modern.pdf  && echo "modern PDF: OK"
```

### Acceptance check

All four `uv run paperwork` commands exit with code 0. Both PDF files are non-empty (size > 0 bytes).

---

## Summary

| ID | Task | Template | Output |
|---|---|---|---|
| T-MIN-01 | Create `templates/minimal/` directory | minimal | directory |
| T-MIN-02 | Write `template.yaml` | minimal | `templates/minimal/template.yaml` |
| T-MIN-03 | Write `cv.html` | minimal | `templates/minimal/cv.html` |
| T-MIN-04 | Write `cv.css` | minimal | `templates/minimal/cv.css` |
| T-MIN-05 | Write `spec.yaml` | minimal | `templates/minimal/spec.yaml` |
| T-MOD-01 | Create `templates/modern/` directory and copy asset | modern | directory + `assets/profile.jpg` |
| T-MOD-02 | Write `template.yaml` | modern | `templates/modern/template.yaml` |
| T-MOD-03 | Write `cv.html` | modern | `templates/modern/cv.html` |
| T-MOD-04 | Write `cv.css` | modern | `templates/modern/cv.css` |
| T-MOD-05 | Write `spec.yaml` | modern | `templates/modern/spec.yaml` |
| T-VERIFY-01 | Verify both templates | both | exit 0 + non-empty PDFs |

---

**Last Updated**: 2026-05-12 by Orlando Bruno
