# 0001. Record architecture decisions as ADRs

- Status: Accepted
- Date: 2026-10-11

## Context

The project is developed together with AI agents. A decision made in conversation dies with the session context, and an agent without it may silently reverse it.

## Decision

Significant decisions are recorded in `docs/adr/NNNN-title.md` in Nygard's format ([template.md](template.md)). Accepted ADRs are not edited on substance, only superseded by new ones. `AGENTS.md` points agents at this directory.

## Consequences

Every agent and human has one source of truth for why things are the way they are. The cost is a short note for each significant decision.
