# 0002. Python with a standard-library-only runtime

- Status: Accepted
- Date: 2026-10-11

## Context

Go (a single binary, ~5 ms startup), Python and Bash with fzf were considered. TAB latency is the critical constraint: the shell runs the program on every keypress, so the answer has to arrive in under ~100 ms. Python's own startup is ~20–50 ms; the popular libraries (typer+rich, google-cloud-*, google-auth) add another 150–500 ms.

## Decision

Python >= 3.11. The runtime uses the standard library only: `argparse`, `configparser`, `tomllib`, `json`, `sqlite3`, `urllib`, `concurrent.futures`, `webbrowser`. Third-party dependencies are allowed in the dev group only.

## Consequences

- Startup and completion fit the budget. Installation pulls no dependencies.
- A small custom REST client on `urllib` instead of the Google libraries.
- If the budget turned out to be unreachable, rewriting the completion path alone in Go stays possible, because the boundary between it and the rest is the cache format (JSON).
