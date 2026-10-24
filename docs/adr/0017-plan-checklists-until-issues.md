# 0017. Milestone checklists stay in the plan for now

- Status: Accepted, partially supersedes [0014](0014-docs-in-repo.md) (where open work is tracked)
- Date: 2026-10-24

## Context

[ADR-0014](0014-docs-in-repo.md) moved `docs/` into the repository and decided that open work lives in GitHub Milestones and issues rather than in the checklists of `plan.md`. The first half is being carried out now. The second half has not been: no milestones or issues exist yet, while the checklists are up to date and the remaining MVP work is being done in quick succession for a prototype.

Moving the tracking now would cost setup time and leave the plan and the issues out of sync while both exist.

## Decision

- `plan.md` keeps its milestone checklists and the Status column of URL templates as the record of open work.
- Every pull request that completes a checklist item, or changes a template's status, updates `plan.md` in the same pull request, so the plan changes together with the code it describes.
- The rest of ADR-0014 stands: `docs/` is committed and in English, `docs/research.md` stays local.
- Moving open work to GitHub issues is revisited after the MVP prototype, as a new ADR.

## Consequences

- One place to look for progress, reviewed with the code.
- Checklists are maintained by hand; a stale tick is caught in review, not by tooling.
- `AGENTS.md` points agents to `plan.md`, not to `gh issue list`.
