# 0011. Project structure: application layers and a flat directory of GCP services

- Status: Accepted, partially superseded by [0012](0012-cli-syntax-and-routes.md) (`web/` also holds `route.py`; `browser.py` without `--copy`)
- Date: 2026-10-12

## Context

The original sketch had all modules flat in `src/gcw/`, with service logic smeared across one routes file and one `fetch.py`. With about 15 services, and more in stage 2, it would be hard to find where anything is. We considered categorising GCP services (compute, data, security…) and rejected it: it is the application that needs order, not Google's service catalogue.

## Decision

```
src/gcw/
  cli/        main.py (argparse, global flags), complete.py (__complete), shell/ (completion, shell-init)
  context/    gcloud_config.py (INI reading), resolve.py (flag > env > config > cache > lookup)
  cache/      store.py (JSON, soft TTL), refresh.py (background refresh)
  api/        auth.py (token from gcloud), client.py (REST over urllib)
  web/        url.py (building console URLs), browser.py (opening, -n, --copy)
  services/   one file = one GCP service, flat; __init__.py = registry; landing.py = L0 pages
```

- **Dependencies only point down:** `cli` → `services` → (`api`, `cache`, `context`, `web`). Lower layers do not import `cli` or `services`.
- "Services" means GCP services only. Parts of the application are called layers.
- A service module contains: a docstring (what it covers), routes (ADR-0010) and `list_*` functions that fetch resources. HTTP imports are lazy, inside functions.
- A test guards the completion budget: after `__complete`, `sys.modules` contains neither `ssl` nor `urllib.request`, and the time fits the budget. A generated registry index is added only if measurements show the need.

## Consequences

- It is obvious where to look: completion in `cli/complete.py`, the Cloud Run URL in `services/run.py`, the token in `api/auth.py`.
- Layers can be tested separately.
- In the MVP some directories hold 1–2 files. That is a deliberate cost in exchange for not moving files later.
