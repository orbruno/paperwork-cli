# Product Requirements Documents

Product-level intent for Paperwork: what is being built, for whom, and how success is measured. PRDs sit **upstream** of the SDD design lifecycle (Research → ADR → Spec) and feed product clarity into it.

## Documents

| File | Product / Initiative | Created | Status |
|------|----------------------|---------|--------|
| [prd.md](./prd.md) | Paperwork | 2026-05-12 | Draft |

## When to Create a PRD

- A new product, feature, or initiative with a user-facing surface
- Stakeholders need to align on *what* is being built before *how*
- AI-assisted implementation requires explicit non-goals and testable acceptance criteria
- The work is large enough to warrant decomposition into multiple specs

## Pipeline

```
PRD  →  /sdd:research  →  /sdd:adr  →  /sdd:spec  →  Implementation
 ^         exploration      decision    requirements    code
 |
 product-level intent
 (problem, users, goals, non-goals, success metrics)
```

## Naming Convention

- Default: `prd.md` (single PRD per project)
- Multiple PRDs: kebab-case slug, e.g., `prd-autofit.md`, `prd-api.md`, or versioned `prd-v2.md`

---

Last Updated: 2026-05-12
