# Plan: gcw ("gcloud web")

A living document, updated together with the work it describes ([ADR-0017](adr/0017-plan-checklists-until-issues.md)). Decisions and their reasoning are in [adr/](adr/). Market research and notes on the gcloud/gh code are kept locally in `research.md`.

## Goal

A CLI in the style of `gh browse` / `gh pr view --web` that opens any Google Cloud service or resource in the browser from the terminal. It takes its context (account, project, region) from the gcloud CLI configuration. TAB completion of resource names has to be instant.

```
$ gcw run services ap<TAB>
api-gateway   europe-west1 · prod-proj
api-worker    europe-west1 · prod-proj
$ gcw run services api-gateway --tab logs   # the service's logs, no region needed
$ gcw sql instances main-db -n              # only print the URL
$ gcw storage buckets my-bucket/exports/2026
$ gcw -c work gke clusters <TAB>            # clusters from the "work" configuration
$ gcw logs run api-worker                   # Logs Explorer with a ready filter
$ gcw composer environments etl --airflow   # the environment's Airflow UI
$ gcw run                                   # service overview
$ gcw billing                               # the service's start page
```

Rule: **gcw navigates, gcloud operates** ([ADR-0004](adr/0004-navigation-only.md)).

## MVP scope

### UX and flags

- Syntax: `gcw <service> [<kind> [<name>]] [-l LOCATION] [--tab T]`. The resource kind is always explicit, as in gcloud (`gcw run services api`), except in services with a single kind, which omit it (`gcw secrets NAME`). `gcw <service>` opens the service overview, `gcw <service> <kind>` the list, and with a name one resource. Without arguments `gcw` opens the project dashboard.
- `-l/--location` (aliases `--region`, `--zone`): the resource's region or zone. By default from the gcloud property named by the route (e.g. `run/region`), and from M3 from the cache.
- Global flags, working before and after the command: `-p/--project`, `-c/--configuration`, `-n/--no-browser` (only print the URL, as in `gh browse`), `--no-authuser`. No `--copy`: `gcw -n | wl-copy` (or `clip.exe`) is enough for the clipboard.
- `gcw open <path>`: any console path with the context appended.
- `gcw ls [type]`: a table from the cache (name, location, project).
- `gcw refresh [type]`: forced cache refresh.
- `gcw services`: the list of supported services and routes.
- `gcw completion bash|zsh|fish` and the hidden `gcw __complete …`.
- `gcw env <config>`: exports `CLOUDSDK_ACTIVE_CONFIG_NAME`, i.e. switches the configuration in the current shell only.
- ~~`gcw shell-init`~~: rejected in [ADR-0015](adr/0015-no-gcloud-shell-wrapper.md); `gcw` is the only entry point.

### Services

Levels: **L0** the service page (no cache), **L1** one resource, **L2** a resource tab (`--tab`). URL templates are drafts; each has to be verified against the real console before it is marked done.

Status: ☐ not implemented · 🔧 implemented, template unverified · ✅ verified in the console. All templates use a single `{location}` placeholder (region or zone, depending on the service).

| Command | Level | URL template (draft) | Status |
|---|---|---|---|
| `gcw run services [svc] [--tab metrics\|logs\|revisions\|triggers\|yaml]` | L2 | list `run/services`, resource `run/detail/{location}/{name}/{tab}` | 🔧 |
| `gcw run jobs [job] [--tab executions\|logs\|triggers\|yaml]` | L2 | list `run/jobs`, resource `run/jobs/details/{location}/{name}/{tab}` | 🔧 |
| `gcw functions [fn]` | L1 | `functions/details/{location}/{name}` | 🔧 |
| `gcw compute instances [vm]` | L1 | `compute/instancesDetail/zones/{location}/instances/{name}` | 🔧 |
| `gcw gke clusters [cluster] [--tab details\|nodes\|storage\|observability\|logs]` | L2 | `kubernetes/clusters/details/{location}/{name}/{tab}` | 🔧 |
| `gcw sql instances [inst] [--tab overview\|connections\|users\|databases\|backups\|replicas\|operations]` | L2 | `sql/instances/{name}/{tab}` | 🔧 |
| `gcw storage buckets [bucket[/path]]` | L1 | `storage/browser/{name}` | 🔧 |
| `gcw secrets [name] [--tab versions\|overview\|permissions\|logs]` | L2 | `security/secret-manager/secret/{name}/{tab}` | 🔧 |
| `gcw artifacts repositories [repo]` | L1 | `artifacts/docker/{project}/{location}/{name}` (Docker only until the format comes from the cache) | 🔧 |
| `gcw dataproc clusters [cluster] [--tab monitoring\|jobs\|vms\|configuration]` | L2 | `dataproc/clusters/{name}/{tab}?region={location}` | 🔧 |
| `gcw dataproc batches [id]` | L1 | `dataproc/batches/{location}/{name}` | 🔧 |
| `gcw dataproc jobs [id]` | L1 | `dataproc/jobs/{name}?region={location}` | 🔧 |
| `gcw composer environments [env] [--tab monitoring\|logs\|dags]` | L2 | `composer/environments/detail/{location}/{name}/{tab}` | 🔧 |
| `gcw composer environments env --airflow` | L1 | `config.airflowUri` from the cache | ☐ |
| `gcw logs [run\|gke\|sql\|functions <name>] [--query Q]` | L1 | `logs/query;query={filter}` (a separate case, to be designed) | ☐ |
| `gcw iam [service-accounts EMAIL]` | L0/L1 | `iam-admin/iam`, `iam-admin/serviceaccounts/details/{name}` | 🔧 |
| `gcw <service>` (55 start pages) | L0 | a static list in `services/landing.py` | 🔧 |

Services with a single resource kind (Functions, Secret Manager) omit the kind: `gcw secrets db-password`. Services with several kinds always require it ([ADR-0012](adr/0012-cli-syntax-and-routes.md)).

Every URL gets `?project={project}` appended; templates that already have a `?` are joined with `&`. `authuser={account}` is added only when opening the browser (choosing the right Google account when several are signed in). Links printed by `-n` come without it, clean for sharing.

Right after the MVP: Pub/Sub, BigQuery, Cloud Build, Workflows, Scheduler.

## Architecture

Structure as in [ADR-0011](adr/0011-project-structure.md). Dependencies only point down: `cli` → `services` → (`api`, `cache`, `context`, `web`).

```
pyproject.toml          # uv, entry point gcw = gcw.cli.main:main, Python >= 3.11
src/gcw/
  cli/
    main.py             # argparse, global flags; subcommands generated from the service registry
    complete.py         # __complete: cache only, no network, no heavy imports
    shell/              # bash/zsh/fish completion scripts
  context/
    gcloud_config.py    # reading the gcloud configuration (INI) without subprocesses
    resolve.py          # flag > env > config > cache > live lookup
  cache/
    store.py            # ~/.cache/gcw/<account>/<project>/<type>.json, atomic writes, soft TTL
    refresh.py          # background refresh (detached process)
  api/
    auth.py             # token from `gcloud auth print-access-token`, opt-in: access_tokens.db
    client.py           # minimal REST client over urllib, parallel in threads
  web/
    route.py            # Route: resource page template → console path, RouteError
    url.py              # building the console URL (?project=…[&authuser=…])
    browser.py          # webbrowser.open (the CLI decides about -n)
  services/             # one file = one GCP service (routes as data + list_*), flat
    __init__.py         # service registry
    run.py functions.py compute.py gke.py sql.py storage.py secrets.py
    artifacts.py dataproc.py composer.py logs.py iam.py
    landing.py          # about 50 L0 start pages
tests/
```

Key principles, justified in ADRs:
- Standard-library-only runtime ([0002](adr/0002-python-stdlib-only.md)), `src/` layout ([0003](adr/0003-src-layout-uv.md)).
- Context from gcloud's files ([0005](adr/0005-context-from-gcloud-config.md)).
- TAB never waits for the network, a cache without hard expiry ([0006](adr/0006-cache-never-blocks-completion.md)).
- Tokens from the official gcloud command ([0016](adr/0016-official-token-command-by-default.md)).
- Data through each service's REST `list`, Cloud Asset Inventory deferred ([0008](adr/0008-per-service-list-no-asset-inventory.md)).
- Routes as data in service modules, with user overrides ([0010](adr/0010-routes-as-data.md)).
- Application layers and a flat `services/` ([0011](adr/0011-project-structure.md)).
- CLI syntax, flags and the shape of routes ([0012](adr/0012-cli-syntax-and-routes.md)).
- Linux, macOS and Windows (Git Bash fully, cmd/PowerShell without TAB); CI on three systems with `ci` required before merge ([0013](adr/0013-supported-platforms.md)).
- gcw does not wrap or change gcloud ([0015](adr/0015-no-gcloud-shell-wrapper.md)).

Performance budgets: `gcw __complete` < 50 ms, `gcw <service> <resource>` with a cache hit < 150 ms until the browser is launched.

## Milestones

### M1: skeleton and context
- [x] `pyproject.toml` (uv, `gcw` entry point), `src/` layout with layer packages, pytest
- [x] `context/gcloud_config.py`: active configuration, `core/project`, `core/account`, `run/region`, `compute/region`, `compute/zone`, environment overrides; tests on a fake `CLOUDSDK_CONFIG`
- [x] `web/url.py` + `web/browser.py`
- [x] `context/resolve.py` + `cli/main.py`: `gcw` (dashboard), `gcw open`, `-n/--no-browser`, `-p`, `-c`, `--no-authuser`

### M2: routes
- [x] `Route` (in `web/route.py`) + registry in `services/__init__.py` (templates, required parameters, tabs); parser generated from the registry, global flags also after the command, `-l/--location` with aliases, `--tab`
- [x] `services/run.py`: Cloud Run (services, jobs)
- [x] `services/landing.py`: L0 start pages (55 services, hidden in `gcw --help`, with examples in the `epilog`); short aliases `-r/--region`, `-z/--zone`
- [x] `gcw services`: the list of supported services, kinds and tabs, in two sections (with routes / start pages only)
- [x] `cli/pager.py`: long output through `$PAGER` (`GCW_PAGER` → `PAGER` → `less`), only when stdout is a terminal; `gcw ls` will use it too
- [x] single-kind services in the registry and parser (`gcw secrets NAME`, ADR-0012): the module's `SINGLE_KIND` attribute
- [x] the remaining service modules with routes (no `list_*` yet): functions, compute, gke, sql, storage, secrets, artifacts, dataproc, composer, iam
- [x] URL tests for every route (`tests/test_services.py`)
- [ ] manual verification in the console (the Status column)

### M3: cache, auth, fetching
- [x] `api/auth.py`: token from `gcloud auth print-access-token --account` (ADR-0016), found with `shutil.which` (`gcloud.cmd` on Windows), remembered per process
- [x] `api/client.py`: GET JSON over `urllib`, `nextPageToken` pagination, `run_parallel` with a per-task error
- [ ] `GCW_FAST_TOKEN=1`: the `access_tokens.db` opt-in from ADR-0016 (deferred past the prototype)
- [x] `list_<kind>(context, token)` functions in the service modules for every kind, returning `Resource(name, location, extra)` from `cache/store.py`; `services.lister()` finds them. Checked with `gcw refresh` on a real project: Run services, Compute, SQL, Storage, Secrets, Artifact Registry and IAM answer as expected; Run jobs rejected `locations/-` (HTTP 400) and are now listed region by region (confirmed: the job is found). Still unverified: Functions and GKE (APIs disabled in that project), Dataproc and Composer (no resources there)
- [ ] Dataproc and Composer list one region only (`dataproc/region` / `composer/location`, else `compute/region`), because their APIs have no `locations/-`; consider listing all regions in the background later
- [x] `cache/store.py` + `cache/refresh.py`: atomic writes, 24 h soft TTL, `spawn_background` (detached `python -m gcw refresh --background`, 5-minute lock), `gcw refresh [SERVICE [KIND]]`, `gcw ls [SERVICE [KIND]]`; tests isolate the cache with `GCW_CACHE_DIR`
- [ ] start the background refresh when a command uses a stale or missing cache entry (with the lookup below)
- [ ] live lookup when missing from the cache, then added to it
- [ ] location of a named resource from the cache before `config`: `-l` → env → cache (with several hits for the same name, `config` breaks the tie) → `config`. Lists and start pages are unchanged, because there is no name there and `config` is the right answer
- [x] Windows in code: `shutil.which("gcloud")` (`gcloud.cmd`), `DETACHED_PROCESS` for the refresh process, cache directory `%LOCALAPPDATA%\gcw` (ADR-0013); not yet tried on a real Windows machine

### M4: completion and switching
- [ ] `__complete` + bash/zsh/fish scripts with descriptions
- [ ] completion for `-c` (configurations) and `-p` (projects from the cache)
- [ ] `gcw env` (`shell-init` rejected in ADR-0015)
- [ ] measuring the performance budgets + a test: after `__complete`, no `ssl` and no `urllib.request` in `sys.modules`

### M5: release
- [ ] README (installation with `uv tool install` / `pipx`, completion, adding routes, WSL: `BROWSER=wslview`)
- [ ] `~/.config/gcw/routes.toml`: user overrides

## Stage 2 (after the MVP)

- Wizard: a picker (fzf, if available) on the same cache as TAB.
- TAB completion in PowerShell: `Register-ArgumentCompleter` calling `gcw __complete` (ADR-0013).
- Cloud Asset Inventory as an optional speed-up with autodetection (worth revisiting).
- `gcloud … --web`: translating commands in gcloud syntax into URLs.
- A route generator based on `resources.yaml` / `resources.py` from the gcloud code.
- `gcw-<name>` plugins on PATH (modelled on gh extensions).
- `gcw last`: the URL from the output of the last gcloud command.
- A browser detached from the terminal, as in `gh`: our own launching (`$BROWSER` / `xdg-open` / `open` / `os.startfile`) with `start_new_session=True` and output to `/dev/null`. `webbrowser` through `xdg-open` attaches e.g. Vivaldi to the terminal (logs, a "hung" prompt).
- Moving open work to GitHub issues (ADR-0017).

## Verification

- `uv run pytest`: URLs, config parsing, cache, completion, all without network.
- Manually: `gcw <service> <resource> -n` compared with the URL from the console, then without `-n` (the right account through `authuser`).
- `CLOUDSDK_ACTIVE_CONFIG_NAME=other gcw -n`: configuration switching.
- `time gcw __complete run ""`: the < 50 ms budget.
