# Architecture Decision Records

ADRs for Paperwork. Each record captures a significant architectural or technology decision with full rationale.

## Records

| # | Area | Title | Date | Status |
|---|------|-------|------|--------|
| [001](ADR-001__eng__pdf-rendering-library.md) | eng | PDF Rendering Library Selection | 2026-05-12 | Implemented |
| [002](ADR-002__tpl__template-format.md) | tpl | CV Template Format — HTML + CSS + Jinja2 | 2026-05-12 | Implemented |
| [003](ADR-003__sys__engine-only-design.md) | sys | Engine-Only Design — External Templates and Profiles | 2026-05-12 | Implemented |
| [004](ADR-004__sys__profile-schema-design.md) | sys | CVData — Pydantic Model as Profile-Template Contract | 2026-05-12 | Implemented |
| [005](ADR-005__fit__two-phase-optimizer.md) | fit | Auto-Fit Two-Phase Optimizer — Margins First, Content Second | 2026-05-12 | Implemented |
| [006](ADR-006__fit__immutable-data-patterns.md) | fit | Immutable Data Patterns in the Auto-Fit Optimizer | 2026-05-12 | Implemented |
| [007](ADR-007__tpl__spec-yaml-llm.md) | tpl | Machine-Readable spec.yaml for LLM-Assisted Profile Generation | 2026-05-12 | Implemented |
| [008](ADR-008__sys__photo-field-design.md) | sys | Photo Field Design | 2026-05-12 | Implemented |
| [009](ADR-009__api__fastapi-optional-extra.md) | api | FastAPI as Optional Extra | 2026-05-12 | Implemented |
| [010](ADR-010__cli__template-dir-resolution.md) | cli | Template Directory Resolution Order | 2026-05-12 | Implemented |
| [011](ADR-011__cli__job-yaml-format.md) | cli | Job YAML — Per-Application Render Configuration | 2026-05-13 | Proposed |

## When to Create an ADR

- Making an architectural or technology choice
- Choosing between approaches with trade-offs
- A decision that affects multiple components
- Something future-you will wonder "why did we do it this way?"

## Naming Convention

`ADR-NNN__[area]__slug.md` — Three-digit number, area code, kebab-case slug. Double underscores separate each segment.

### Area Codes

| Code | Area |
|------|------|
| `sys` | System / cross-cutting |
| `cli` | CLI interface |
| `eng` | Rendering engine |
| `tpl` | Template system |
| `fit` | Auto-fit / layout optimization |
| `api` | FastAPI layer |

Custom area codes are allowed (lowercase, 2-4 chars).

### Examples

- `ADR-001__eng__pdf-rendering-library.md`
- `ADR-002__tpl__template-format-choice.md`
- `ADR-003__sys__profile-schema-design.md`

## ADR Lifecycle

```
Draft → In Review → Approved → Implemented
                              → Deprecated (if superseded)
```

---

Last Updated: 2026-05-13
