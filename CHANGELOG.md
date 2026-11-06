# Changelog

All notable changes to gcw are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [ADR-0025](docs/adr/0025-release-process.md): 0.x while gcw is a prototype, a breaking change bumps the minor version.

## [0.1.0] - Unreleased

First release.

### Added

- Open Google Cloud console pages from the terminal with gcloud's words: `gcw` (project dashboard), `gcw SERVICE`, `gcw SERVICE KIND`, `gcw SERVICE KIND NAME [--tab TAB]`, and `gcw open PATH` for any console path.
- Resource pages for Cloud Run, Cloud SQL, Cloud Storage, Compute Engine, GKE, Cloud Functions, Secret Manager, Artifact Registry, IAM service accounts, Dataproc and Composer (including its Airflow UI), and start pages of about 50 more services; `gcw services` prints the map.
- Context from gcloud's configuration: account, project and default regions, with `-p/--project`, `-c/--configuration` and `-l/--location` to override them for one command.
- A local cache of resource names and locations, filled from each service's read-only REST `list` API and refreshed in the background; `gcw cache list` and `gcw cache refresh`.
- TAB completion of commands, kinds, resource names and tabs from the cache in bash, zsh and fish: `gcw completion SHELL [--install]`.
- gcloud command syntax as input: `gcw gcloud GCLOUD_ARGS...`, and an opt-in `gcloud … --web` shell function from `gcw web-flag SHELL [--install]`.
- `gcw env CONFIGURATION` to use another gcloud configuration in one shell.
- `-n/--no-browser` to print the URL instead of opening it, and `--no-authuser`.
- Linux, macOS and Windows; no runtime dependencies besides Python 3.11+ and gcloud.

[0.1.0]: https://github.com/terleckimaciej/gcloud-web/releases/tag/v0.1.0
