# Architecture

How gcw works. This document changes together with the code it describes; open work is in [GitHub issues](https://github.com/terleckimaciej/gcloud-web/issues) ([ADR-0021](adr/0021-open-work-in-github-issues.md)). Decisions and their reasoning are in [adr/](adr/README.md).

## What happens on a command

`gcw run jobs nightly`:

1. `cli/main.py` parses the command. Its subcommands are generated from the service registry.
2. `context/` reads the account, project and regions from gcloud's configuration files, without running gcloud.
3. The service module's `Route` for `jobs` names the URL template and the gcloud property for the default location.
4. The location of a named resource comes from `-l`, then `$CLOUDSDK_<SECTION>_<NAME>`, then the cache, then the gcloud configuration. A name missing from the cache is looked up once, live, and cached (`cli/lookup.py`).
5. `web/` builds the console URL and opens the browser, or prints the URL with `-n`.

TAB is a separate, faster path: the shell script runs `gcw __complete -- WORDS…`, which `cli/main.py` hands to `cli/complete.py` before building the parser. It reads only the gcloud configuration files and the cache: no network, no subprocesses, no background refresh ([ADR-0006](adr/0006-cache-never-blocks-completion.md)).

`gcw gcloud …` is handled before the parser too, because gcloud's flags are not gcw's. `cli/gcloud_syntax.py` turns the gcloud words into gcw arguments: it drops the verb (only read verbs are accepted), keeps the context flags under their names, and drops location flags when no resource is named. `cli/main.py` prints the result to stderr and runs it as an ordinary command ([ADR-0020](adr/0020-gcloud-syntax-input.md)). The `gcloud` function printed by `gcw web-flag` only calls `gcw gcloud` for command lines with `--web` ([ADR-0024](adr/0024-opt-in-gcloud-web-function.md)).

## Layout

Layers as in [ADR-0011](adr/0011-project-structure.md); dependencies point down only: `cli` → `services` → (`api`, `cache`, `context`, `web`).

```
src/gcw/
  cli/
    main.py             # argparse; subcommands generated from the service registry
    complete.py         # __complete: candidates from the cache and config only
    gcloud_syntax.py    # gcw gcloud: a gcloud command line → gcw arguments (data tables)
    lookup.py           # finding a named resource's location; live lookup on a cache miss
    resources.py        # gcw cache list / refresh
    pager.py            # long output through $GCW_PAGER, $PAGER or less
    shell/              # bash/zsh/fish completion scripts and the gcloud … --web function
  context/
    gcloud_config.py    # reading gcloud's INI configuration files
    resolve.py          # flags, environment and configuration → Context
  cache/
    store.py            # <cache dir>/<account>/<project>/<service>.<kind>.json, atomic writes, 24 h soft TTL
    refresh.py          # refreshing entries; the detached background refresh process
  api/
    auth.py             # access token from `gcloud auth print-access-token`
    client.py           # minimal REST client over urllib: pagination, per-location listing, threads
  web/
    route.py            # Route: URL template, tabs, location; Link for extra pages (Airflow UI)
    url.py              # console URL: ?project=…[&authuser=…]
    browser.py          # opening the browser
  services/             # one module per GCP service: routes as data + list_<kind>()
    __init__.py         # the registry
    run.py functions.py compute.py container.py sql.py storage.py
    secrets.py artifacts.py dataproc.py composer.py iam.py
    landing.py          # start pages of services without resource routes
```

A service module declares `NAME`, `HELP`, `LANDING` and `KINDS` (kind → `Route`), and a `list_<kind>(context, token)` for every kind. Services with one kind set `SINGLE_KIND`, so the kind is never typed (`gcw secrets NAME`). Service and kind names are gcloud's ([ADR-0012](adr/0012-cli-syntax-and-routes.md), [ADR-0019](adr/0019-service-names-follow-gcloud.md)).

## Cache

Resource names and locations are cached per account, project, service and kind. The cache directory is `$GCW_CACHE_DIR`, else `%LOCALAPPDATA%\gcw` on Windows, else `$XDG_CACHE_HOME/gcw` or `~/.cache/gcw`.

- Entries are written atomically and never expire hard; an entry older than 24 hours is stale.
- Using a stale or empty entry starts a detached `python -m gcw cache refresh --background`, guarded by a five-minute lock, so no command waits for the network ([ADR-0006](adr/0006-cache-never-blocks-completion.md)).
- Lists come from each service's read-only REST `list` API ([ADR-0008](adr/0008-per-service-list-no-asset-inventory.md)). APIs disabled in a project are skipped.
- The access token comes from `gcloud auth print-access-token`, once per process ([ADR-0016](adr/0016-official-token-command-by-default.md), [ADR-0023](adr/0023-no-token-database-opt-in.md)).

## Console URLs

Levels: **L0** a service page, **L1** one resource, **L2** a tab of a resource page (`--tab`; the first tab is the default). Every template uses one `{location}` placeholder, a region or a zone depending on the service. Templates are checked by hand against the real console ([#19](https://github.com/terleckimaciej/gcloud-web/issues/19)).

| Command | Level | URL template |
|---|---|---|
| `gcw run services [svc] [--tab metrics\|logs\|revisions\|triggers\|yaml]` | L2 | list `run/services`, resource `run/detail/{location}/{name}/{tab}` |
| `gcw run jobs [job] [--tab executions\|logs\|triggers\|yaml]` | L2 | list `run/jobs`, resource `run/jobs/details/{location}/{name}/{tab}` |
| `gcw functions [fn]` | L1 | `functions/details/{location}/{name}` |
| `gcw compute instances [vm]` | L1 | `compute/instancesDetail/zones/{location}/instances/{name}` |
| `gcw container clusters [cluster] [--tab details\|nodes\|storage\|observability\|logs]` | L2 | `kubernetes/clusters/details/{location}/{name}/{tab}` |
| `gcw sql instances [inst] [--tab overview\|connections\|users\|databases\|backups\|replicas\|operations]` | L2 | `sql/instances/{name}/{tab}` |
| `gcw storage buckets [bucket[/path]]` | L1 | `storage/browser/{name}` |
| `gcw secrets [name] [--tab versions\|overview\|permissions\|logs]` | L2 | `security/secret-manager/secret/{name}/{tab}` |
| `gcw artifacts repositories [repo]` | L1 | `artifacts/docker/{project}/{location}/{name}`: Docker only; the cache records each repository's format, but the template does not use it yet |
| `gcw dataproc clusters [cluster] [--tab monitoring\|jobs\|vms\|configuration]` | L2 | `dataproc/clusters/{name}/{tab}?region={location}` |
| `gcw dataproc batches [id]` | L1 | `dataproc/batches/{location}/{name}` |
| `gcw dataproc jobs [id]` | L1 | `dataproc/jobs/{name}?region={location}` |
| `gcw composer environments [env] [--tab monitoring\|logs\|dags]` | L2 | `composer/environments/detail/{location}/{name}/{tab}` |
| `gcw composer environments env --airflow` | L1 | the Airflow UI address from the cache (`LINKS` in the module) |
| `gcw iam [service-accounts EMAIL]` | L0/L1 | `iam-admin/iam`, `iam-admin/serviceaccounts/details/{name}` |
| `gcw <service>` (55 start pages) | L0 | a static list in `services/landing.py` |

Every URL gets `?project={project}`; templates that already have a `?` are joined with `&`. `authuser={account}` is added only when opening the browser, so the console picks the right Google account when several are signed in. URLs printed by `-n` come without it, so they never contain an email address.

## Principles

- Standard-library-only runtime ([0002](adr/0002-python-stdlib-only.md)), `src/` layout and uv ([0003](adr/0003-src-layout-uv.md)).
- gcw navigates, gcloud operates: no command changes cloud resources ([0004](adr/0004-navigation-only.md)).
- Context from gcloud's configuration files ([0005](adr/0005-context-from-gcloud-config.md)); gcw does not wrap or change gcloud ([0015](adr/0015-no-gcloud-shell-wrapper.md)).
- Routes are data in service modules ([0010](adr/0010-routes-as-data.md)).
- Linux, macOS and Windows; CI on all three ([0013](adr/0013-supported-platforms.md)).

Performance budgets: `gcw __complete` under 100 ms ([0022](adr/0022-tab-budget-100ms.md)); `gcw <service> <kind> <name>` with a cache hit under 150 ms until the browser is launched.
