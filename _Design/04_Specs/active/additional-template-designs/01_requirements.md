# Spec: Additional Template Designs — Requirements

**Feature**: additional-template-designs
**Phase**: 1 — Requirements
**Status**: Draft
**Created**: 2026-05-12
**Author**: Orlando Bruno
**PRD references**: Goal 5, FR-16, FR-17, FR-18

---

## 1. PRD References

| Reference | Statement |
|-----------|-----------|
| Goal 5 | "Ship multiple distinct visual CV designs as built-in template packs, so users can choose a style without having to author templates themselves." Target: ≥ 3 distinct designs by v0.3.0. |
| FR-16 | "The repository shall include multiple distinct visual CV template designs (beyond `classic`), each as a self-contained template pack, so users can select a style without authoring templates themselves." Priority: High. |
| FR-17 | "Every template pack shall include a `spec.yaml` — a machine-readable document describing all fields, types, constraints (max_chars, max_items), and layout context — to enable LLM-assisted profile generation." Priority: High. |
| FR-18 | "The HTTP API shall expose a `GET /templates/{slug}/spec` endpoint that returns the full `spec.yaml` content for a given template, so remote clients can fetch it without filesystem access before generating a profile." Priority: High. |
| NFR-01 | `paperwork generate` shall complete PDF rendering in under 10 seconds for a standard single-page profile on a modern laptop. |
| NFR-06 | Adding a new template pack shall require only creating a new directory with a valid `template.yaml` + HTML + CSS; no engine code modification required. |
| Story 5 | LLM/automation client fetches `spec.yaml` to generate a correctly structured profile YAML without manual authoring. |

---

## 2. Overview

Paperwork currently ships one built-in template (`classic`). PRD Goal 5 requires ≥ 3 distinct designs by v0.3.0. This spec covers the creation of two additional built-in templates:

### minimal
A single-column, text-only layout for users who want a clean, no-frills professional CV. Omits the profile photo entirely (`supports_photo: false`). No decorative elements — section headings use a simple left-aligned uppercase label with a hairline rule. Tight body spacing to maximise content density. Targets A4 paper (common outside North America). Best suited for senior professionals, academics, and technical roles where content density matters more than visual branding.

### modern
A contemporary two-column layout anchored by a solid left accent bar (a fixed-width coloured column). The right pane contains all content. Photo is optional. Skills are rendered as a compact inline list rather than a grid. Accent colour: deep slate blue (`#1e3a5f`). Targets US Letter paper. Best suited for users who want a visually distinctive CV without sacrificing readability — designers, product people, AI/data professionals building a portfolio-style document.

Both templates must be complete, self-contained template packs that slot into the existing `templates/{slug}/` directory structure without engine changes.

---

## 3. User Stories

### Story A: Developer Choosing a Template Design

> **As a** developer maintaining my CV as a YAML or JSON profile,
> **I want to** choose between multiple visual designs using the `-t` flag,
> **so that** I can match the CV style to the type of role I am applying for without creating a custom template.

**Acceptance criteria**:
- `paperwork templates` lists `classic`, `minimal`, and `modern` as available templates.
- `paperwork generate -p profile.yaml -t minimal -o cv.pdf` produces a valid single-page PDF.
- `paperwork generate -p profile.yaml -t modern -o cv.pdf` produces a valid single-page PDF.
- Switching templates requires no profile changes beyond fields that one template requires and the other does not.

### Story B: LLM Generating a Profile for a Specific Template

> **As an** LLM or automation client,
> **I want to** read the `spec.yaml` for `minimal` or `modern` and generate a correctly structured profile YAML,
> **so that** the resulting PDF renders cleanly without manual correction or layout overflow.

**Acceptance criteria**:
- `spec.yaml` exists for both `minimal` and `modern`.
- The spec covers every field the template renders, with `type`, `required`, and `constraints` (max_chars, max_items).
- A profile generated strictly within the constraints in `spec.yaml` passes `paperwork validate -p <profile> -t <slug>` with exit code 0.
- `GET /templates/minimal/spec` and `GET /templates/modern/spec` return the spec content over HTTP.

### Story C: User Wanting a Photo-Free CV

> **As a** user who prefers not to include a profile photo,
> **I want** a built-in template that does not show a photo panel at all,
> **so that** the layout does not leave empty space when the `photo` field is absent.

**Acceptance criteria**:
- The `minimal` template has `supports_photo: false` in `template.yaml`.
- The `minimal` CV layout contains no `<img>` element and no photo placeholder.
- The header of `minimal` renders cleanly at full page width with no reserved right column.

---

## 4. Functional Requirements

### 4.1 Per-Template Requirements

Each new template must satisfy all rows in the table below.

| ID | Requirement | minimal | modern |
|----|-------------|---------|--------|
| TFR-01 | Template directory exists at `templates/{slug}/` with all required files. | required | required |
| TFR-02 | `template.yaml` is present and valid against the `TemplateMeta` Pydantic schema. | required | required |
| TFR-03 | `cv.html` is a Jinja2 template that renders all sections present in `CVData`. | required | required |
| TFR-04 | `cv.css` is a WeasyPrint-compatible stylesheet with `@page` rule defining page size and margins. | required | required |
| TFR-05 | `spec.yaml` is present and covers every field referenced in `cv.html`. | required | required |
| TFR-06 | `template.yaml` includes a `layout_params` block with all fields required by `LayoutParams.from_dict()`. | required | required |
| TFR-07 | `template.yaml` includes `required_fields` and `optional_fields` lists in dot notation. | required | required |
| TFR-08 | All optional CVData sections use `{% if field %}...{% endif %}` guards in `cv.html`. | required | required |
| TFR-09 | Template renders without error against a standard profile YAML used for the `classic` template. | required | required |
| TFR-10 | `supports_photo` is `false` and no photo element exists in `cv.html`. | required | n/a |
| TFR-11 | `supports_photo` is `true` and photo falls back to `assets/profile.jpg` when `photo` field is absent. | n/a | required |
| TFR-12 | `assets/profile.jpg` exists in the template directory as a placeholder. | n/a | required |
| TFR-13 | Template discovers and is listed by `paperwork templates` command without engine code changes. | required | required |
| TFR-14 | `paperwork validate -p <profile> -t <slug>` exits 0 for a standard compliant profile. | required | required |

### 4.2 Distinct Visual Design

The two new templates must be visually distinct from each other and from `classic`. Distinction is measured by:
- Different page layout structure (column arrangement, header organisation).
- Different typographic treatment of section headings.
- Different decorative elements (or intentional absence thereof).

`minimal` must have zero decorative elements beyond the hairline section rule. `modern` must have a visible accent colour bar on the left side of the page.

---

## 5. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| TNFR-01 | Performance | Both templates render in under 10 seconds on macOS M-series or Linux x86-64 (inherits NFR-01). |
| TNFR-02 | Spec coverage | `spec.yaml` covers 100% of fields rendered in `cv.html` — no rendered field is undocumented. |
| TNFR-03 | Validation | Both templates pass `paperwork validate` with a standard profile (same profile used for `classic` integration tests). |
| TNFR-04 | WeasyPrint compatibility | CSS must not use properties unsupported by WeasyPrint: no `flexbox gap`, no `CSS Grid` shorthand, no `position: sticky`, no `var()` custom properties. |
| TNFR-05 | Font availability | Templates must use only fonts available to WeasyPrint without additional installation: `Arial`, `Helvetica`, `Georgia`, `Times New Roman`, `Courier New`, or a Google Fonts `@import` that WeasyPrint can fetch at render time. |
| TNFR-06 | Engine isolation | No engine Python files (`src/paperwork/`) are modified. Template addition is purely filesystem (new directory + files). |
| TNFR-07 | Immutability | Template files do not implement any server-side logic; all data transformation is done in the engine before template rendering. |

---

## 6. Success Criteria Checklist

- [ ] `templates/minimal/` directory exists with: `template.yaml`, `cv.html`, `cv.css`, `spec.yaml`.
- [ ] `templates/modern/` directory exists with: `template.yaml`, `cv.html`, `cv.css`, `spec.yaml`, `assets/profile.jpg`.
- [ ] `uv run paperwork templates` output includes `minimal` and `modern`.
- [ ] `uv run paperwork validate -p <standard-profile> -t minimal` exits 0.
- [ ] `uv run paperwork validate -p <standard-profile> -t modern` exits 0.
- [ ] `uv run paperwork generate -p <standard-profile> -t minimal -o /tmp/test-minimal.pdf` produces a non-empty PDF file.
- [ ] `uv run paperwork generate -p <standard-profile> -t modern -o /tmp/test-modern.pdf` produces a non-empty PDF file.
- [ ] Both PDFs fit on a single page for a standard 1-page profile.
- [ ] `minimal` PDF contains no profile photo element.
- [ ] `modern` PDF displays the left accent colour bar.
- [ ] `spec.yaml` for each template documents all rendered fields with `type`, `required`, and at least one `constraints` entry per field.
- [ ] Total built-in template count is ≥ 3 (classic + minimal + modern), satisfying PRD Goal 5.
- [ ] `_Design/04_Specs/README.md` index is updated to reflect this spec.

---

## 7. Out of Scope

These items are explicitly excluded from this spec. Any work on them requires a separate spec.

- GUI template picker or visual template browser — excluded per PRD Non-Goals.
- Template thumbnail or preview image generation — no automated screenshot pipeline.
- WYSIWYG editor for template or profile authoring — excluded per PRD Non-Goals.
- Template marketplace or community submission mechanism — excluded per PRD Non-Goals.
- A fourth or fifth template design — this spec covers exactly `minimal` and `modern`.
- SCSS source files — `cv.scss` is optional per `TemplateMeta`; plain CSS is sufficient and avoids a build step dependency.
- Auto-fit tuning for the new templates — `layout_params` will be defined with reasonable defaults, but optimisation of trim rules is deferred to post-v0.3.0 iteration.
- Windows compatibility testing for WeasyPrint rendering — excluded per PRD Non-Goals.

---

## 8. Dependencies

| Dependency | Nature | Notes |
|------------|--------|-------|
| Existing render engine (`src/paperwork/engine/`) | Hard — templates are consumed by the engine unchanged. | No engine code changes required. Engine must be functional before templates are tested. |
| WeasyPrint CSS constraints | Hard — CSS properties must be supported by WeasyPrint's paged media rendering. | Flexbox `gap` property not supported; use `margin` instead. CSS Grid column shorthand may have limited support — test explicitly. |
| `TemplateMeta` Pydantic schema | Hard — `template.yaml` must conform exactly to the schema in `src/paperwork/models/template_meta.py`. | `layout_params` keys must match `LayoutParams.from_dict()` parameter names. |
| `LayoutParams.from_dict()` | Hard — `layout_params` dict in `template.yaml` must provide exactly the fields `LayoutParams` expects. | See `src/paperwork/autofit/models.py`. |
| Standard test profile | Soft — a YAML profile covering all standard CVData fields is needed to run validation and render tests. | Can use the same profile used in existing `classic` template testing, or create a `tests/fixtures/standard_profile.yaml` if one does not exist. |
| `templates/classic/assets/profile.jpg` | Soft — can be copied as placeholder for `templates/modern/assets/profile.jpg`. | The `modern` template needs a photo fallback; copying from `classic` is acceptable for the initial implementation. |

---

**Last Updated**: 2026-05-12 by Orlando Bruno
**Next**: Phase 2 — Design (`02_design.md`)
