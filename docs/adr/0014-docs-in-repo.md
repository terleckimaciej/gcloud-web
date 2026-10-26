# 0014. Documentation in the repository, work tracked in GitHub

- Status: Accepted; its part on open work was deferred by [0017](0017-plan-checklists-until-issues.md) and is in force again through [0021](0021-open-work-in-github-issues.md)
- Date: 2026-10-18

## Context

`docs/` was written in Polish and excluded from git via `.git/info/exclude` while the project was being sketched out. Three consequences became limiting: the repository has no `README.md`; the ADRs — the record of why the code looks the way it does ([ADR-0001](0001-record-architecture-decisions.md)) — are invisible to anyone cloning it; and the milestone checklists in `plan.md` are the kind of content nobody opens a markdown file to read.

Files and issues are good at different things. A file is reviewed in the same pull request as the code it describes, is available offline, and stays correct for as long as the code does. An issue is navigable, linkable from a pull request, and shows progress without being maintained by hand.

## Decision

- `docs/` is committed and written in English: the [index](../README.md), the [architecture overview](../architecture.md), [how gcloud is built](../gcloud-internals.md), the [plan](../plan.md) and the ADRs.
- `README.md` in the repository root is the front page: purpose, command shapes, installation, security posture, local development.
- Open work lives in GitHub Milestones and issues, not in markdown checklists. `plan.md` keeps what an issue cannot carry: the goal, the MVP scope and the long-term direction. Verification status of URL templates is a tracking issue.
- `docs/research.md` stays local and in Polish: a working notebook, not a statement about the project.
- `.git/info/exclude` excludes `/docs/research.md` instead of `/docs/`.

## Consequences

- Reading the plan requires network access and access to the repository (`gh issue list`). `AGENTS.md` points agents there.
- Documentation changes go through the same pull request process as code.
- Documentation can drift from the code. `AGENTS.md` carries the remedy: architecture or CLI changes update the architecture overview and the root README; a new decision is a new ADR plus a row in the ADR index.
