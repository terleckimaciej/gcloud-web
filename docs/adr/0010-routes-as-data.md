# 0010. URL routes as data in service modules, with user overrides

- Status: Accepted, partially superseded by [0012](0012-cli-syntax-and-routes.md) (placeholders: a single `{location}`; the default tab is the first of `tabs`; `Route` lives in `web/route.py`)
- Date: 2026-10-11 (revised 2026-10-12, before implementation: routes moved from a single `routes.toml` into service modules)

## Context

Console URLs are not a public API and change with redesigns. A fix should be a one-liner and possible without a new release. We want everything about one service (routes, tabs, fetching the resource list) in one place ([ADR-0011](0011-project-structure.md)).

## Decision

- Every module in `src/gcw/services/` declares its routes as **Python data** (a dictionary of `Route` objects, no logic): a path template with placeholders (`{project}`, `{region}`, `{zone}`, `{location}`, `{name}`, `{tab}`), allowed tabs, the default tab, and the cache type the names come from.
- `services/__init__.py` collects the routes of all modules into one registry. CLI subcommands and completion are generated from that registry.
- `~/.config/gcw/routes.toml` lets the user override and add routes without changing code.

## Consequences

- When Google changes a URL, the fix is one line in the service module or in the overrides file.
- The IDE completes route fields and catches typos. No data file has to be shipped in the package.
- Adding an L0 service is one entry in `services/landing.py`. L1 adds a module with routes and a function that fetches the list.
- Service modules must not import heavy things at the top level, because completion loads the registry (guarded by a test, see ADR-0011).
- Templates have to be verified manually against the console (the Status column in the plan).
