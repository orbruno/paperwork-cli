# Engine-Only Design — External Templates and Profiles

**Version**: 1.0 / **Created**: 2026-05-12 / **Author**: Orlando Bruno / **Status**: Implemented / **Area**: sys / **Related Documents**: `ADR-004__sys__profile-schema-design.md`, `_Design/01_Architecture/`, `_Design/02_Specs/`

---

## Executive Summary

Paperwork adopts an engine-only design in which the repository ships a rendering engine and a curated set of built-in template designs, while profile data always lives externally — in user-managed files or API request payloads. This separation ensures that personal CV data is never committed to a shared codebase, that the engine evolves independently of content and design, and that the system remains open to community-authored templates and organisation-specific designs without requiring a fork. The API use case, where profile data arrives as a request payload, makes any tighter coupling architecturally untenable.

---

## 1. Problem Statement — Context + Desired Outcome

**Context**: Paperwork needs to decide where templates and profile data live relative to the engine repository. Templates are presentation artefacts (Jinja2 layouts, CSS, assets). Profile data is personal YAML/JSON authored by each user. The engine's sole responsibility is accepting profile data and a template, then producing a rendered CV document.

**Desired Outcome**: A clean boundary where the engine repository contains only rendering logic and reference template designs, profile data is always external (no user content committed to the repo), and additional templates can be added without touching the engine.

---

## 2. Architecture Overview

```mermaid
graph TD
    subgraph Engine Repository
        CLI["CLI entrypoint<br/>paperwork render"]
        API["FastAPI layer<br/>POST /render"]
        Loader["profiles/loader.py<br/>YAML · JSON · dict"]
        Registry["templates/registry.py<br/>TemplateRegistry"]
        Engine["Rendering Engine<br/>Jinja2 · WeasyPrint"]
        BuiltIn["Built-in Templates<br/>templates/classic/ …"]
    end

    subgraph External — User Managed
        ProfileFile["profile.yaml / profile.json<br/>(any file path)"]
        ExtTemplates["Custom template dir<br/>(--templates-dir / env var)"]
        APIPayload["API request payload<br/>JSON body"]
    end

    ProfileFile -->|file path arg| Loader
    APIPayload -->|request body| Loader
    Loader -->|CVData| Engine
    Registry -->|resolved template| Engine
    BuiltIn -->|bundled| Registry
    ExtTemplates -->|scanned at startup| Registry
    CLI --> Loader
    CLI --> Registry
    API --> Loader
    API --> Registry
    Engine -->|PDF · HTML| Output["Output Document"]
```

The engine owns the rendering pipeline end-to-end. Profile data enters through `loader.py` regardless of source (file or API payload). Template resolution flows through `TemplateRegistry`, which merges built-in templates with any externally configured directory. No path in the engine writes or stores profile data.

---

## 3. Options Considered

### Option A: Engine-Only (Chosen)

The repository ships the rendering engine plus a curated set of built-in template designs. Profile data always lives externally. Users can point to additional template directories.

Pros:
- Personal CV data never committed to a code repository
- Engine versioned independently from content and designs
- Supports multi-user and API use cases without architectural change
- Community templates require no engine fork
- Clear single-responsibility boundary

Cons:
- Users must manage their own profile files
- No built-in profile versioning or storage
- Template directory misconfiguration is a possible failure mode

### Option B: Monorepo with Profiles

Profile YAML files committed alongside the engine. Single git history for both code and content.

Pros:
- Simple for single-user, local-only setups
- One repository to manage

Cons:
- CV data (often private) lives in a shared code repository
- Breaks multi-user and API use cases
- Profile changes pollute engine commit history
- Violates separation of concerns

### Option C: Bundled Single Template

Engine ships with one hardcoded template. Zero external dependency.

Pros:
- Zero configuration; no template resolution logic needed
- Easiest to distribute

Cons:
- Inflexible; no user customisation of presentation
- Defeats the purpose of a pluggable template system
- Adding a second template requires engine changes

---

## 4. Chosen Solution

**Decision**: Option A — Engine-Only Design.

**Rationale**:

1. Profile data is personal and often private — it should never be committed to a shared code repository.
2. The rendering engine changes independently from content and design; coupling them forces unnecessary releases.
3. External templates allow community authoring and organisation-specific designs without forking the engine.
4. The API use case requires profile data to arrive as request payloads; any monorepo approach is architecturally incompatible with this.

---

## 5. Implementation Specification

### Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| Profile Loader | `src/paperwork/profiles/loader.py` | Loads YAML/JSON from any file path; no concept of a profiles directory in the CLI |
| Template Registry | `src/paperwork/templates/registry.py` | Scans resolved template directory at startup; no hardcoded template list |
| Built-in Templates | `templates/classic/` (and future designs) | Reference implementations shipped in repo |
| CLI entrypoint | `src/paperwork/cli/main.py` | Accepts `--profile` (path) and `--templates-dir` flags |
| FastAPI layer | `src/paperwork/api/routes/render.py` | Accepts profile JSON as request body; reads from `RENDERCV_PROFILES_DIR` for slug-based endpoint |

### Template Directory Resolution

Resolution order at startup (first match wins):

1. `--templates-dir` CLI flag
2. `RENDERCV_TEMPLATES_DIR` environment variable
3. `./templates/` in the current working directory

### Key Interfaces

```python
# profiles/loader.py
def load_profile(source: Union[Path, dict]) -> CVData:
    """Load and validate a profile from a file path or a pre-parsed dict."""

# templates/registry.py
class TemplateRegistry:
    def __init__(self, templates_dir: Path) -> None: ...
    def resolve(self, template_name: str) -> TemplateMeta: ...
    def list_available(self) -> list[str]: ...

# API endpoint — profile slug reads from RENDERCV_PROFILES_DIR (optional)
# GET  /render/{profile_slug}   → resolves slug to file, renders, returns PDF
# POST /render                  → accepts full CVData JSON body, renders, returns PDF
```

---

## 6. Performance & Cost

| Concern | Impact | Notes |
|---------|--------|-------|
| Registry scan at startup | Negligible | Scans one directory once; cached in memory for process lifetime |
| Profile file I/O | Negligible | Single YAML/JSON read per render; no database round-trip |
| External template loading | Low | Jinja2 template compilation is cached after first load |
| API payload parsing | Low | Pydantic validation on each request; sub-millisecond for typical profile sizes |
| No bundled profile storage | None | Engine has zero storage cost for user data |

---

## 7. Quality Assurance & Validation

### Success Metrics

- [ ] `paperwork render --profile path/to/cv.yaml` works from any working directory
- [ ] `--templates-dir` correctly overrides default template resolution
- [ ] `RENDERCV_TEMPLATES_DIR` env var respected when flag is absent
- [ ] `TemplateRegistry` raises a clear `TemplateNotFoundError` with resolution steps when a template is missing
- [ ] API `POST /render` accepts a full CVData JSON body and returns a valid PDF
- [ ] No profile data is written to disk by the engine
- [ ] Built-in `classic` template renders correctly out of the box

### Testing Strategy

- Unit tests for `loader.py`: valid YAML, valid JSON, invalid path, malformed YAML
- Unit tests for `TemplateRegistry`: correct resolution order, unknown template error, empty directory
- Integration tests: CLI end-to-end with `--profile` and `--templates-dir`
- Integration tests: API `POST /render` with valid and invalid payloads
- Contract test: built-in `classic` template renders without errors against a reference profile

---

## 8. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Users lose profile files (no version control) | Medium | High | Documentation strongly recommends keeping profile files in a personal git repo |
| Template directory misconfiguration | Medium | Medium | Clear error messages with the exact resolution order and actionable fix steps |
| Community templates break on engine upgrades | Low | Medium | Semantic versioning + `spec.yaml` declares minimum engine version; deprecation warnings before breaking changes |
| API misuse — large payloads | Low | Low | Request size limit enforced at FastAPI middleware level |

---

## 9. Implementation Roadmap

### Phase 1 — Core Engine (Complete)
- `profiles/loader.py` with YAML/JSON support
- `TemplateRegistry` with three-step resolution
- `templates/classic/` built-in reference template
- CLI `--profile` and `--templates-dir` flags

### Phase 2 — API Layer (Complete)
- `POST /render` endpoint accepting CVData JSON body
- `GET /render/{profile_slug}` with `RENDERCV_PROFILES_DIR`
- Request size limits and error handling

### Phase 3 — Developer Experience (Planned)
- `paperwork template list` command showing available templates
- `paperwork template validate <dir>` to check a custom template before use
- Community template authoring guide

---

## 10. Decision Log

| Date | Author | Change |
|------|--------|--------|
| 2026-05-12 | Orlando Bruno | Initial decision — Option A selected |

---

## 11. Success Criteria

- [ ] Engine repository contains zero committed user profile files
- [ ] All three template directory resolution steps are tested and documented
- [ ] `TemplateRegistry` has no hardcoded template names
- [ ] CLI and API both use the same `loader.py` and `TemplateRegistry`
- [ ] Built-in `classic` template produces a valid PDF from a reference profile
- [ ] Error messages for missing templates include resolution steps

---

## 12. Related Documents

- `ADR-004__sys__profile-schema-design.md` — CVData Pydantic model that defines the profile contract
- `_Design/01_Architecture/` — system architecture diagrams
- `_Design/02_Specs/` — component specifications
- `templates/classic/spec.yaml` — built-in template specification

---

**Last Updated**: 2026-05-12 by Orlando Bruno
