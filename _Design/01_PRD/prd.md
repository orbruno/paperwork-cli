# Paperwork — Product Requirements Document

**Version**: 0.1
**Created**: 2026-05-12
**Author**: Orlando Bruno
**Status**: Draft
**Document Type**: PRD (precedes `/sdd:research`, `/sdd:adr`, `/sdd:spec`)

---

> **What this document is**: The product-level contract — *what* you are building, *for whom*, and *how you will know it worked*. It is the upstream artifact that downstream SDD documents (Research, ADR, Specs) consume.
>
> **What this document is NOT**: A technical spec. Do not specify architecture, libraries, or implementation here. That belongs in `02_design.md` or an ADR. The PRD says *"sessions must survive browser refresh"*; the spec says *how*.
>
> **How to fill this in**: Lead with evidence, not solutions. Quantify everything that can be quantified. State non-goals explicitly — especially for AI-assisted implementation, where omitted scope is not inferable. Iterate; do not wait for completeness before sharing.

---

## 1. Problem Statement

Resume and CV generation is a recurring, high-friction activity for knowledge workers. Existing approaches share a compounding problem: **format and content are entangled**. Word processors require manual layout work every time content changes. Online builders lock users into proprietary formats and limited design flexibility. LaTeX-based solutions require deep TeX expertise and offer poor portability. None of these integrate cleanly into automation pipelines (e.g., CI/CD, HTTP-based workflows).

The result: updating a CV is a time-consuming manual task that people avoid — producing outdated documents at exactly the moments they matter most (job applications, portfolio updates, grant submissions).

**Why now?** Three converging trends make a code-first, pipeline-friendly CV engine viable and valuable:
1. YAML/JSON-native data management is standard practice for developers and data professionals — the target users already live in structured files.
2. Headless browser rendering (WeasyPrint via HTML+CSS) has matured to the point where professional-quality PDFs are achievable without a LaTeX toolchain.
3. LLMs can generate well-structured YAML from unstructured CV data — and when each template ships a machine-readable `spec.yaml` describing its fields, constraints, and layout, an LLM can produce a profile perfectly adapted to any chosen design without manual authoring.

Paperwork solves this by cleanly separating the **content layer** (profile YAML/JSON, optionally LLM-generated) from the **presentation layer** (template packs), enabling human-driven CLI workflows, LLM-assisted profile generation, and fully automated pipeline integrations via an HTTP API.

### Workflow Context (Informational — Outside CLI Scope)

A typical power user maintains a **master CV** — a comprehensive document with their full experience, skills, and history, unconstrained by any template. When applying for a specific job, they:

1. Run `paperwork spec --template <slug>` to learn the chosen template's field constraints (max chars, max items per section, layout parameters)
2. Ask an LLM to generate a job-specific profile adapted from their master CV, trimmed to those constraints
3. Store the adapted profile alongside render configuration (template, output path, layout overrides) as a single **job YAML** file
4. Run `paperwork generate --job acme-corp.yaml` to produce the PDF

Paperwork's responsibility is step 1 (exposing the spec) and steps 3–4 (accepting the job YAML and rendering). The master CV and LLM interaction are the user's concern and outside the CLI's scope.

---

## 2. Goals & Success Metrics

### Goals

- Goal 1: Enable a developer/data professional to go from a structured YAML or JSON profile to a production-quality PDF CV in a single command, with zero manual layout work.
- Goal 2: Support fully automated CV generation from any HTTP client or orchestration pipeline via a stable HTTP API.
- Goal 3: Make template authoring and iteration fast — a template author should be able to create a new template pack without touching the engine code.
- Goal 4: Eliminate the need to re-edit layout when CV content changes (via the auto-fit engine).
- Goal 5: Ship multiple distinct visual CV designs as built-in template packs, so users can choose a style without having to author templates themselves.
- Goal 6: Enable LLM-assisted profile generation — each template exposes a machine-readable `spec.yaml` so an LLM (local or remote) can generate a correctly structured, constraint-aware profile YAML adapted to any chosen design.
- Goal 7: Support per-job-application render configuration — users can store CV content and render settings (template, output path, layout overrides) in a single versioned file per application and re-render identically at any time.
- Goal 8: Allow template customization without engine changes — users can copy a built-in template pack locally, modify HTML/CSS/layout parameters, and use it via `--templates-dir`.

### Success Metrics

#### Impact Metrics (business outcomes)

| Metric | Baseline | Target | Timeframe |
|--------|----------|--------|-----------|
| Time to generate PDF from profile YAML (CLI) | Manual (minutes) | < 5 seconds per render | At v0.2.0 release |
| Successful HTTP pipeline integration | Not integrated | End-to-end workflow operational | Within 1 sprint of API stabilization |
| Template pack creation time (new template from scratch) | N/A | < 2 hours for a developer familiar with HTML/CSS | At v0.3.0 |
| Number of built-in visual template designs | 1 (classic only) | ≥ 3 distinct designs | At v0.3.0 |
| LLM-generated profile passes `paperwork validate` without manual correction | Not tested | 100% for profiles generated from spec.yaml | At v0.3.0 |

#### Usage Metrics (leading indicators)

| Metric | Target | Timeframe |
|--------|--------|-----------|
| CLI `generate` command succeeds on first run with a valid profile + template | 100% (no silent failures) | At v0.2.0 |
| Auto-fit produces a single-page PDF for a standard 1-page profile | ≥ 90% of attempts | At v0.2.0 |
| HTTP API `/render` endpoint returns a PDF binary within 10 seconds | P95 < 10s on local Docker | At v0.2.0 |
| Validation command catches all missing required fields before render | 100% (no render-time crashes from missing fields) | At v0.2.0 |
| `GET /templates/{slug}/spec` returns valid spec.yaml for every built-in template | N/A | 100% | At v0.3.0 |

---

## 3. Non-Goals

**Critical for AI-assisted development**: An AI coding agent cannot infer scope from omission. Every boundary must be stated positively.

What this PRD does **not** cover (and why, and where it might go later):

- ❌ **Template marketplace or community contributions** — The repository ships its own curated template designs, but there is no registry, download command, or community submission mechanism for third-party templates. Users can create and use their own template packs as external directories.
- ❌ **User accounts or multi-tenancy** — No login, no user management, no per-user profile storage. The engine is stateless; profiles are files on disk or JSON in API request bodies. Multi-tenancy is a deployment concern, not an engine concern.
- ❌ **GUI or web-based editor** — No browser-based WYSIWYG editor for the profile or template. The target user edits YAML in a text editor or generates profile data programmatically.
- ❌ **ATS optimization or content suggestions** — No AI-driven content rewriting, keyword suggestion, or ATS scoring. The engine renders content exactly as provided.
- ❌ **Microsoft Word / DOCX output** — PDF via WeasyPrint is the only output format. DOCX export is not planned for v0.x.
- ❌ **Windows native support** — macOS (primary dev environment) and Linux (Docker/production) are the supported platforms. Windows may work but is not tested or supported.
- ❌ **Cloud storage integration** — No S3, GDrive, or Dropbox connectors. File I/O is local filesystem or HTTP multipart; cloud integration is the caller's responsibility.
- ❌ **HTTP API authentication** — The API ships with no authentication layer (no API keys, no OAuth, no JWT). It is designed to run inside a private network or Docker Compose stack. Securing access at the network level is the deployer's responsibility.
- ❌ **`watch` / live-reload command** — No file watcher or auto-regenerate-on-change command for v0.x. Tight edit-preview loops are served by `paperwork preview` run manually. A `watch` command may be considered in a future version.

---

## 4. Target User / Personas

### Primary User: The Automation-Oriented Developer / Data Professional

**Who**: A developer, data scientist, or AI engineer who maintains their CV as structured data and wants generation to be a command, not a project. Likely working on macOS or Linux. Comfortable with YAML, CLI tools, and Docker.

**Current behavior**: Maintains a Word doc or Overleaf LaTeX file. Updates it manually every few months. Spends 30–90 minutes reformatting layout after content changes. May have a half-finished LaTeX template they're not happy with.

**Goals**: Generate a polished PDF CV on demand — ideally from a single command or API call — without touching layout. Profile data is stored externally as a YAML or JSON file, managed independently of the engine.

**Context of use**: Running the CLI locally during a job search or portfolio update cycle. Potentially integrating into a personal automation workflow that auto-generates a CV nightly or on profile change.

**Technical proficiency**: Can read and write YAML, run CLI commands, edit HTML/CSS for template customization, and configure Docker. Does not need to understand the rendering pipeline internals.

### Secondary User: The Pipeline / API Operator

**Who**: Someone (may be the same person) building an automated workflow — e.g., a pipeline that pulls updated profile data from a database or external source, calls the Paperwork HTTP API, and stores or emails the resulting PDF.

**Current behavior**: Either no automation (manual process), or a fragile custom script that shells out to a LaTeX engine and breaks on system updates.

**Goals**: A reliable, container-deployable HTTP endpoint that accepts JSON profile data and returns a PDF binary. Minimal dependencies, predictable behavior.

**Context of use**: Docker-deployed service, called from any HTTP client or automation tool. May run in a headless CI environment.

**Technical proficiency**: Can configure Docker Compose, write automation workflows, and read API documentation. Does not need to modify engine code.

### Integration Target: The LLM / Automated Agent

**Who**: A large language model or AI agent acting as a client — either locally (reading `spec.yaml` from disk) or remotely (fetching it via `GET /templates/{slug}/spec`) — that generates a profile YAML adapted to a chosen template and then calls the render endpoint or CLI.

**Current behavior**: No standard interface exists for LLMs to discover CV template requirements. Profile generation requires manual authoring or bespoke prompting without schema grounding.

**Goals**: A stable, machine-readable `spec.yaml` per template that provides field names, types, constraints, and layout context sufficient to generate a layout-safe profile without human correction.

**Context of use**: Called programmatically as part of a CV generation pipeline. May be embedded in a Claude Code workflow, an n8n AI node, a custom agent, or any tool-using LLM setup.

**Technical proficiency**: N/A — consumes structured data (spec.yaml), calls HTTP endpoints or CLI commands. Does not require understanding of the rendering pipeline.

---

## 5. User Stories

### Story 1: Single-Command PDF Generation

> **As a** developer maintaining my CV as a YAML or JSON file,
> **I want to** run a single CLI command with my profile and a template name,
> **so that** I get a production-quality PDF without any manual layout work.

**Acceptance criteria**:
- [ ] `paperwork generate -p profile.yaml -t classic -o cv.pdf` completes without error when profile and template are valid.
- [ ] The output PDF renders all sections defined in the profile in the order specified by the template.
- [ ] The command exits with a non-zero status code and a descriptive error message if the profile is missing required fields for the chosen template.
- [ ] The command exits with a non-zero status code if the template slug does not resolve to a valid template directory.
- [ ] Total elapsed time from command invocation to PDF written to disk is under 10 seconds for a standard single-page profile on a modern laptop.

### Story 2: Automated Pipeline Rendering via HTTP API

> **As a** pipeline operator,
> **I want to** POST a JSON profile to the `/render` endpoint and receive a PDF binary in the response,
> **so that** I can automate CV generation without any local tooling.

**Acceptance criteria**:
- [ ] `POST /render?template=classic` with a valid JSON body returns a `200 OK` with `Content-Type: application/pdf` and a valid PDF binary.
- [ ] The endpoint returns a structured JSON error with HTTP 4xx for validation failures (missing required fields, unknown template).
- [ ] The endpoint returns HTTP 5xx (not a crash) for rendering errors, with a descriptive error message.
- [ ] The Docker image starts and serves the API with `docker compose up` using the provided `docker-compose.yml`.
- [ ] The API is callable from any standard HTTP client with no custom configuration beyond the endpoint URL and JSON body.

### Story 3: Content-Driven Auto-Fit to Page Budget

> **As a** developer generating a 1-page CV,
> **I want to** run `paperwork generate --auto-fit --target-pages 1`,
> **so that** the engine automatically adjusts margins and trims content to fit exactly one page, without me manually tuning CSS or removing content.

**Acceptance criteria**:
- [ ] With `--auto-fit` and `--target-pages 1`, the output PDF fits within the target page count for profiles that are within 15% overflow of the target.
- [ ] Phase 1 (margin reduction) runs before Phase 2 (content trimming). Phase 2 only activates if Phase 1 is insufficient.
- [ ] With `--fit-report`, the CLI prints a summary of which auto-fit phase was used and what was changed.
- [ ] Auto-fit never silently drops required fields — it only trims items explicitly marked as trimmable in `template.yaml` trim rules.
- [ ] The original profile YAML is not modified by auto-fit; all mutations produce a new in-memory data structure.

### Story 4: Template Validation Before Render

> **As a** developer iterating on a new CV profile,
> **I want to** run `paperwork validate -p profile.yaml -t classic` before generating the PDF,
> **so that** I catch missing or malformed fields early without waiting for a render cycle.

**Acceptance criteria**:
- [ ] `paperwork validate` exits 0 and prints "Validation passed" when the profile satisfies all required fields declared in `template.yaml`.
- [ ] `paperwork validate` exits non-zero and lists all missing required fields when validation fails.
- [ ] Validation completes in under 1 second (no PDF rendering triggered).
- [ ] Validation detects type mismatches (e.g., a string where a list is expected) in addition to missing fields.

### Story 5: LLM-Assisted Profile Generation

> **As an** LLM or automation client,
> **I want to** fetch a template's `spec.yaml` — either from the local filesystem or via the API — and use it to generate a correctly structured profile YAML adapted to that template's constraints,
> **so that** the resulting PDF matches the chosen design without manual profile authoring.

**Acceptance criteria**:
- [ ] Every built-in template ships a `spec.yaml` that documents all fields, types, constraints, and layout context in a machine-readable format.
- [ ] `GET /templates/{slug}/spec` returns the full `spec.yaml` content so remote clients can access it without filesystem access.
- [ ] A profile generated from `spec.yaml` by an LLM passes `paperwork validate` against the same template without manual correction.
- [ ] The spec includes enough constraint detail (max_chars, max_items, descriptions) for an LLM to produce layout-safe content without overflowing the template.

### Story 6: Per-Job-Application Render Configuration

> **As a** developer running a job search,
> **I want to** store my adapted CV content and render settings in a single YAML file per application,
> **so that** I can re-render exactly what I submitted at any time and version-control each application independently.

**Acceptance criteria**:
- [ ] A job YAML file with a `render:` block (template, output, layout_overrides) and standard CVData fields at root is accepted by `paperwork generate --job job.yaml`.
- [ ] `paperwork validate --job`, `paperwork preview --job`, and `paperwork estimate --job` also accept the job YAML format.
- [ ] `--job` and `--profile` are mutually exclusive; providing both exits with code 2 and a descriptive error.
- [ ] `layout_overrides` in the `render:` block (margin_mm, font_size_pt, line_height) are applied as CSS custom property overrides without modifying `template.yaml`.
- [ ] A job YAML with no `render:` block fails with a clear error naming the missing key.

### Story 7: Local Template Customization

> **As a** developer who wants to tweak a built-in template's visual design or layout parameters,
> **I want to** copy a template pack locally with a single command,
> **so that** I can modify it and use my custom version via `--templates-dir` without touching the engine or the built-in templates.

**Acceptance criteria**:
- [ ] `paperwork templates copy <slug> <destination>` copies the full template pack (HTML, CSS, assets, template.yaml, spec.yaml) to the destination directory.
- [ ] `paperwork templates copy <slug> <destination> --manifest-only` copies only `template.yaml` to the destination.
- [ ] The copied template is immediately usable with `paperwork --templates-dir <destination> generate ...`.
- [ ] The command errors with a clear message if the slug does not exist or the destination already contains a directory with that slug (unless `--force` is provided).

---

## 6. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | The system shall accept a profile (YAML or JSON file) and a template slug as inputs to the `generate` command and produce a PDF output file. | High |
| FR-02 | The system shall resolve the template directory from: `--templates-dir` CLI flag → `RENDERCV_TEMPLATES_DIR` env var → `./templates/` in the current working directory, in that priority order. | High |
| FR-03 | The system shall validate the profile against the template's `required_fields` list before rendering and halt with a descriptive error if any required field is absent. | High |
| FR-04 | The system shall expose a `templates` command that lists all available template slugs discovered in the resolved templates directory. | High |
| FR-05 | The system shall expose a `validate` command that performs field validation without rendering a PDF. | High |
| FR-06 | The system shall expose a `preview` command that renders an HTML preview and opens it in the default browser. | Medium |
| FR-07 | The system shall expose an `estimate` command that reports the line budget for a given profile and template, used to diagnose auto-fit eligibility. | Medium |
| FR-08 | The system shall support an `--auto-fit` flag on `generate` that activates the two-phase optimizer: margin reduction (Phase 1) followed by content trimming (Phase 2), in that order. | High |
| FR-09 | The auto-fit optimizer shall never modify the source profile file on disk; all mutations shall produce new in-memory data structures. | High |
| FR-10 | The system shall provide an HTTP API (`GET /`, `GET /templates`, `GET /templates/{slug}/spec`, `POST /render`, `POST /render-cv`, `GET /render/{profile_slug}`) as an optional `api` extra. | High |
| FR-11 | The `POST /render` endpoint shall accept a JSON body conforming to the `CVData` schema and return a PDF binary with `Content-Type: application/pdf`. | High |
| FR-12 | The system shall be importable as a Python library with `from paperwork.engine import RenderEngine` and `from paperwork.profiles import load_profile`. | Medium |
| FR-13 | The system shall read template metadata from a `template.yaml` manifest in each template directory; templates without a valid manifest shall be excluded from the resolved template list with a warning. | High |
| FR-14 | The `--fit-report` flag on `generate` shall print a human-readable summary of auto-fit actions taken (phase used, margins adjusted, items trimmed). | Low |
| FR-15 | The system shall support an `extra: dict` field in the profile for template-specific arbitrary data not covered by the standard `CVData` schema. | Medium |
| FR-16 | The repository shall include multiple distinct visual CV template designs (beyond `classic`), each as a self-contained template pack, so users can select a style without authoring templates themselves. | High |
| FR-17 | Every template pack shall include a `spec.yaml` — a machine-readable document describing all fields, types, constraints (max_chars, max_items), and layout context — to enable LLM-assisted profile generation. | High |
| FR-18 | The HTTP API shall expose a `GET /templates/{slug}/spec` endpoint that returns the full `spec.yaml` content for a given template, so remote clients can fetch it without filesystem access before generating a profile. | High |
| FR-19 | The `CVData` profile schema shall include an optional `photo` field (file path or URL). Templates that support photos shall render it dynamically when provided and fall back to a default image in `assets/` when absent. The `supports_photo` flag in `template.yaml` indicates whether a template participates in this behavior. | High |
| FR-20 | The system shall support a Job YAML format: a single file containing a `render:` block (template slug, output path, optional layout_overrides) and standard CVData fields at root level. | High |
| FR-21 | The `generate`, `validate`, `preview`, and `estimate` commands shall accept a `--job` flag as an alternative to `--profile`. When `--job` is provided, template and output are read from the `render:` block. `--job` and `--profile` shall be mutually exclusive. | High |
| FR-22 | Layout overrides in the `render:` block (`margin_mm`, `font_size_pt`, `line_height`) shall be applied as CSS custom property overrides injected before the template stylesheet, without modifying `template.yaml`. | High |
| FR-23 | The system shall expose a `paperwork templates copy <slug> <destination>` command that copies the full template pack (HTML, CSS, assets, template.yaml, spec.yaml) to the destination directory for local customization. | Medium |
| FR-24 | The `paperwork templates copy` command shall accept a `--manifest-only` flag that copies only `template.yaml` to the destination, for users who only need to override layout parameters. | Medium |

---

## 7. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Performance | `paperwork generate` shall complete PDF rendering in under 10 seconds for a standard single-page profile on a modern laptop (macOS M-series or Linux x86-64). |
| NFR-02 | Performance | The HTTP API `/render` endpoint shall return a PDF response within 15 seconds at P95 under single-user load on a Docker container with 2 CPU cores and 2 GB RAM. |
| NFR-03 | Reliability | The engine shall never crash silently; all rendering failures shall propagate as structured exceptions or HTTP error responses with descriptive messages. |
| NFR-04 | Portability | The engine shall run on macOS (Homebrew WeasyPrint) and Linux (system packages `libpango`, `libcairo`) without code changes; platform-specific library path detection is handled at startup. |
| NFR-05 | Immutability | The auto-fit optimizer shall use immutable data patterns throughout — no in-place mutation of dicts or lists; every transformation returns a new object. |
| NFR-06 | Extensibility | Adding a new template pack shall require only creating a new directory with a valid `template.yaml` + HTML + CSS; no engine code modification required. |
| NFR-07 | Containerization | A working `Dockerfile` and `docker-compose.yml` shall be maintained such that `docker compose up` starts the HTTP API with a mounted templates directory. |
| NFR-08 | Observability | CLI commands shall print progress to stdout and errors to stderr; the API shall log request/response metadata at INFO level and errors at ERROR level. |
| NFR-09 | Security | The HTTP API shall not expose internal filesystem paths in error responses; profile data from API requests shall not be persisted to disk unless explicitly configured. |
| NFR-10 | Maintainability | The codebase shall maintain a minimum of 80% test coverage across the engine, CLI, and API layers. All new features shall be accompanied by unit and integration tests before merging. |

---

## 8. Assumptions & Dependencies

### Assumptions

- Users have WeasyPrint and its system dependencies (Pango, Cairo, GDK-PixBuf) installed, or are running via Docker where these are pre-installed in the image.
- Template authors are comfortable writing HTML/CSS and Jinja2 templates; no visual template editor is assumed.
- Profile data is maintained by the user in YAML or JSON format; the engine does not validate business-logic correctness of CV content (e.g., date ordering), only schema correctness.
- The pipeline integration scenario assumes Paperwork is deployed as a Docker container accessible over HTTP; network configuration is the user's responsibility.
- `uv` is available in the development environment; `pip` is not used anywhere in the project.
- The `hatchling` build backend is stable for the project's packaging needs through v0.x.

### Dependencies

- **WeasyPrint** — Core PDF rendering engine. Hard dependency; no fallback renderer. Version compatibility with `libpango` / `libcairo` must be maintained.
- **Jinja2** — Template rendering engine for HTML output. Hard dependency.
- **Pydantic** — Data model validation (`CVData`, `TemplateMeta`). Hard dependency.
- **Click** — CLI framework. Hard dependency.
- **FastAPI + Uvicorn** — HTTP API layer. Optional (`api` extra); not required for CLI-only usage.
- **System libraries (macOS)**: Homebrew-installed `pango`, `cairo`, `gdk-pixbuf` for WeasyPrint on macOS. Auto-detected via `DYLD_FALLBACK_LIBRARY_PATH`.
- **System libraries (Linux/Docker)**: `libpango-1.0-0`, `libcairo2`, `libgdk-pixbuf-2.0-0` installed in the Docker image.
- **Python 3.11+** — Minimum Python version; type hint syntax and Pydantic v2 behavior are assumed.

---

## 9. Open Questions

| Question | Owner | Resolution by | Status |
|----------|-------|---------------|--------|
| Should the HTTP API support multipart file upload for profile YAML or JSON (in addition to JSON body)? This would simplify some pipeline integrations. | Orlando Bruno | 2026-06-01 | Open |
| Is there a need for a `paperwork watch` command (auto-regenerate on profile file change) for tight edit-preview loops? | Orlando Bruno | 2026-06-01 | Open |
| Should `template.yaml` support a `preview_fields` list to define which fields are shown in `paperwork templates` output? | Orlando Bruno | 2026-06-01 | Open |
| What is the strategy for test coverage? No test files were found in the current codebase scan. Should a TDD sprint be scheduled before v0.3.0? | Orlando Bruno | 2026-05-26 | Open |
| Should the `extra: dict` field in `CVData` have any schema-level constraints (e.g., max depth, allowed value types), or remain fully open? | Orlando Bruno | 2026-06-15 | Open |
| Is there a plan to publish Paperwork to PyPI for global install via `uv tool install`? | Orlando Bruno | 2026-06-15 | Open |

---

## 10. Related Documents

### Upstream (informs this PRD)

- Project codebase: `/Users/orlandobruno/Documents/Areas/Software-Dev/CLI-Tools/paperwork-cli/`
- Port registry (for API port assignment): `~/Documents/Library/30-System/Config/Port-Registry.md`

### Downstream (SDD pipeline — created from this PRD)

- Research: `../02_Research/` *(exploration of options — e.g., alternative PDF renderers, auto-fit strategies)*
- ADR: `../03_ADR/` *(architectural decisions — e.g., WeasyPrint choice, immutable auto-fit design, template manifest schema)*
- Spec: `../04_Specs/active/` *(feature-level requirements derived from this PRD — e.g., auto-fit engine spec, HTTP API spec)*

---

## Status Log

| Date | Status | Note |
|------|--------|------|
| 2026-05-12 | Draft | Initial fill-in from codebase analysis |
| 2026-05-13 | Draft | Added workflow context (master CV pattern, informational); Goals 7–8; Stories 6–7; FR-20–24; ADR-011 covers job YAML design decision |

---

**Last Updated**: 2026-05-13 by Orlando Bruno
**Next steps**: Once this PRD is reviewed and stable, run `/sdd:research <topic>` to explore implementation options (e.g., test strategy, WeasyPrint alternatives), or `/sdd:spec <feature-name>` to formalize a specific feature (e.g., auto-fit engine, HTTP API).
