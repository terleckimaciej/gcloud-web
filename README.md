# gcloud-web

[![CI](https://img.shields.io/github/actions/workflow/status/terleckimaciej/gcloud-web/ci.yml?branch=master&label=CI&logo=github)](https://github.com/terleckimaciej/gcloud-web/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

gcw opens any page of the Google Cloud console in your browser with one terminal command. It uses the same syntax as the gcloud CLI, so it works like adding a `--web` flag to a gcloud command: name a service or resource the way gcloud does, and its console page opens.

The terminal is great for running things and poor for exploring and looking at them. The console shows all of it well, but getting there means clicking your way through a console that is slow above all and has no custom keyboard shortcuts, which is both frustrating and a waste of time.

```
$ gcloud run services describe api --region europe-west1   # YAML in the terminal
$ gcw run services api                                     # gets opened in the web console
$ gcw run services api --tab logs                          # straight to its logs
$ gcloud run services describe api --web                   # the same page, as a flag of gcloud
```

Prefer gcloud's own syntax? Add `--web` to a gcloud command: see [Use it as `gcloud … --web`](#use-it-as-gcloud----web).

The project, account and region come from your gcloud configuration, and TAB completes resource names from a local cache, so you rarely type more than a few letters.

**gcw navigates, gcloud operates.** gcw only opens pages; it never changes cloud resources.

> Status: prototype. Console URL templates are drafts until checked against the real console; [#19](https://github.com/terleckimaciej/gcloud-web/issues/19) tracks which ones are verified.

**Documentation:** [Architecture](docs/architecture.md) · [Decisions](docs/adr/README.md) · [Issues](https://github.com/terleckimaciej/gcloud-web/issues) · [Plan](docs/plan.md)

## Contents

- [Installation](#installation)
  - [TAB completion](#tab-completion)
  - [gcloud --web (optional)](#gcloud---web-optional)
- [Usage](#usage)
- [Use it as `gcloud … --web`](#use-it-as-gcloud----web)
- [How resources are found](#how-resources-are-found)
- [Security](#security)
- [Platforms](#platforms)
- [Development](#development)
- [License](#license)

## Installation

You need the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) with `gcloud auth login` done, and Python 3.11+ on your system. gcw has no other dependencies.

gcw is not on PyPI yet, so install it from GitHub with [pipx](https://pipx.pypa.io/):

```
pipx install git+https://github.com/terleckimaciej/gcloud-web
```

pipx puts gcw in its own isolated environment and only the `gcw` command on your `PATH`, so nothing mixes with your other Python packages. If you use [uv](https://docs.astral.sh/uv/), `uv tool install git+https://github.com/terleckimaciej/gcloud-web` does the same.

### TAB completion

Run once for your shell, then open a new terminal:

```
gcw completion bash --install    # or zsh, fish
```

`--install` adds one line to the shell's startup file (`~/.bashrc`, `~/.zshrc` or `~/.config/fish/config.fish`), unless it is already there; `gcw completion --help` shows the line.

gcw's own commands and flags come with a short description; services, kinds and resource names are listed plain. Completion answers from the local cache, so it never waits for the network.

### gcloud --web (optional)

To open pages by adding `--web` to gcloud commands, run once for your shell, then open a new terminal:

```
gcw web-flag bash --install    # or zsh, fish
```

It adds one line to the shell's startup file, like completion. [Use it as `gcloud … --web`](#use-it-as-gcloud----web) explains what it does.

## Usage

A command names a **service**, a **kind** of resource and the resource's **name**, using the same words as gcloud without the verb:

| Word | What it is | Examples |
|---|---|---|
| service | a gcloud command group | `run`, `sql`, `storage`, `compute`, `container`, `composer` |
| kind | a resource type of that service | `services`, `jobs`, `instances`, `buckets`, `clusters` |
| name | your resource | `api`, `main-db`, `my-bucket/exports` (or `gs://my-bucket/exports`) |
| tab | a section of the resource's page | `logs`, `revisions`, `backups`, `nodes` |

Stop at any word to open a broader page:

```
gcw                                       the project dashboard
gcw run                                   Cloud Run overview
gcw run services                          the list of Cloud Run services
gcw run services api                      the service's page (first tab: metrics)
gcw run services api --tab logs           another tab of that page
gcw secrets db-password                   services with a single kind skip it: functions, secrets
gcw storage buckets my-bucket/exports     a folder in a bucket
gcw composer environments etl --airflow   the environment's Airflow UI
gcw bigquery                              start pages of about 50 more services
gcw open logs/query                       a page no service command covers, by its console path
```

`--tab` picks a section of a resource page; without it the first one opens. `gcw services` prints the full map: every supported service, its kinds and each kind's tabs. TAB completion offers the same choices one word at a time.

Global flags work before or after the command:

- `-p/--project`, `-c/--configuration`: use another project or gcloud configuration for one command.
- `-n/--no-browser`: print the URL instead of opening it (pipe it to `wl-copy`, `pbcopy` or `clip.exe`). Printed URLs never contain your email address.
- `--no-authuser`: do not tell the console which signed-in Google account to use.

Resource commands also take `-l/--location` (aliases `-r/--region`, `-z/--zone`); usually you do not need it, see below.

Other commands:

```
gcw cache list [SERVICE [KIND]]           cached resources (alias: ls)
gcw cache refresh [SERVICE [KIND]]        fetch resource names now
gcw env CONFIGURATION                     switch the gcloud configuration of this shell
gcw completion bash|zsh|fish [--install]  TAB completion (see Installation)
gcw gcloud GCLOUD_ARGS...                 the page of a gcloud command (see below)
gcw web-flag bash|zsh|fish [--install]    gcloud … --web (see below)
```

`gcw env` uses another configuration in one terminal only, without `gcloud config configurations activate` affecting every terminal:

```
eval "$(gcw env work)"                # bash, zsh
gcw env work --shell fish | source    # fish
```

## Use it as `gcloud … --web`

Use `--web` as a flag of the gcloud CLI: add it to a gcloud command and its console page opens. It needs a one-time setup, see [gcloud --web](#gcloud---web-optional) under Installation.

Everything works as in gcloud, with two shortcuts: you can leave out flags such as `--region`, because gcw finds the location in its cache or your configuration, and you can shorten the command to open a broader page.

```
$ gcloud run jobs describe nightly --region europe-west1 --web   # the job
$ gcloud run jobs describe nightly --web                         # the same job, region found by gcw
$ gcloud run jobs list --web                                     # the list of jobs
$ gcloud run jobs --web                                          # the same list, shortened
$ gcloud run --web                                               # Cloud Run overview
$ gcloud storage ls gs://my-bucket/exports --web                 # the folder
```

`--web` works on commands that read: `describe`, `list`, `get-iam-policy` and `storage ls`. A command that changes something (`update`, `deploy`, `delete`…) is neither run nor opened; gcw says so and names the nearest page. gcw prints the matching gcw command first, so you also learn the shorter spelling. Without `--web`, `gcloud` runs exactly as before.

On a `gcloud` line, TAB is gcloud's own completion, so you lose what gcw's TAB gives: resource names and tabs from gcw's local cache. To explore, use plain gcw with TAB; reach for `--web` when you already have the gcloud command in front of you (recomended).

Without the shell function (in scripts, PowerShell or cmd), put `gcw` in front instead: `gcw gcloud run jobs describe nightly --region europe-west1`. Add `-n` at the end to print the URL.

## How resources are found

gcw reads your account, project and default regions from gcloud's configuration in `~/.config/gcloud`. Resource names come from each service's read-only REST `list` API and are kept in gcw's own cache in `~/.cache/gcw` (`%LOCALAPPDATA%\gcw` on Windows; `GCW_CACHE_DIR` overrides it), per account and project.

- The cache fills itself: using a stale entry (older than 24 hours) or an empty cache starts a refresh in the background. `gcw cache refresh` refreshes on demand, e.g. right after creating a resource.
- A name that is not cached is looked up once, live, when you open it.
- The location of a named resource comes from `-l`, then `$CLOUDSDK_<SECTION>_<NAME>` (e.g. `CLOUDSDK_RUN_REGION`), then the cache, then your gcloud configuration.
- Services whose API is disabled in the project are skipped; `gcw cache refresh` says which. Dataproc and Composer are listed in the configured region only (`dataproc/region`, `composer/location`, else `compute/region`).

## Security

- gcw only reads gcloud's configuration files; it writes nothing there.
- `gcw web-flag` is opt-in. The `gcloud` shell function it adds handles only command lines with `--web`, a flag gcloud does not have; every other line runs gcloud unchanged.
- The access token comes from `gcloud auth print-access-token`, the official command; gcw does not read gcloud's credential store.
- API calls are read-only `list` requests, which need only the permissions you already use to see the resources in the console.
- The cache holds resource names, locations and, for Composer, the Airflow UI address. No secrets or secret values.

## Platforms

Tried by hand on Linux. macOS and Windows are covered by the automated tests on every change but not yet tried by hand. TAB completion works in bash, zsh and fish (on Windows, in Git Bash); in cmd and PowerShell every command works without completion. In WSL the browser runs on the Windows side, so you may need `export BROWSER=wslview`.

## Development

```
uv sync
uv run pytest
uv run gcw …
```

Tests never touch the network or your real gcloud configuration. Adding a service starts with a module in `src/gcw/services/` that declares its routes as data; see [Architecture](docs/architecture.md).

## License

gcw is licensed under the [Apache License 2.0](LICENSE).
