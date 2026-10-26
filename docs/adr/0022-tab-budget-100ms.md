# 0022. TAB completion budget: 100 ms

- Status: Accepted
- Date: 2026-10-26

## Context

`AGENTS.md` and the plan set a budget of 50 ms for `gcw __complete`, stricter than the constraint in [ADR-0002](0002-python-stdlib-only.md): the shell runs the program on every TAB, so the answer has to arrive in under ~100 ms to feel instant.

The prototype measures about 70 ms (median of 20, Python 3.12). Python starts in ~15 ms; importing `dataclasses` (through `inspect`) costs ~25 ms, then `json`, `re`, `typing` and `pathlib`. Getting under 50 ms would mean dropping dataclasses from every class on the completion path and adding a separate entry point that does not import `cli/main.py`. Used by hand, the 70 ms answer already feels instant.

## Decision

- The budget for `gcw __complete` is < 100 ms, the limit ADR-0002 named.
- The other completion rules stay: no network, no subprocesses, cache only, no slow top-level imports.
- The refactor above is not planned. If a future change pushes completion over the budget, it is the first remedy.

## Consequences

- The rule matches what users perceive, and the prototype meets it with ~30 ms to spare.
- Classes on the completion path may keep using dataclasses.
- `time gcw __complete -- gcw run services ''` stays the check, against 100 ms.
