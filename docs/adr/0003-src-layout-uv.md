# 0003. `src/` layout and uv

- Status: Accepted
- Date: 2026-10-11

## Context

In a flat layout, `import gcw` in tests can load the directory from the current folder instead of the installed package. Tests pass while the installed tool is broken, for example because a data file is missing from the wheel. That risk is real here, since routes were to live in `routes.toml`.

## Decision

A `src/gcw/` layout, managed with uv (`uv init --package` produces it by default). User installation: `uv tool install` or `pipx`.

## Consequences

Tests run against what is actually installed, so a missing data file shows up immediately. The cost is one more directory level.
