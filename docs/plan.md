# Plan: gcw ("gcloud web")

Where gcw is going. This document carries no status: what is done and what is open lives in [GitHub issues and milestones](https://github.com/terleckimaciej/gcloud-web/issues) ([ADR-0021](adr/0021-open-work-in-github-issues.md)). How gcw works is in [architecture.md](architecture.md), decisions in [adr/](adr/README.md).

## Goal

Open any Google Cloud console page from the terminal with one command, in the syntax of the gcloud CLI. Context (account, project, region) comes from the gcloud configuration, and TAB completes resource names instantly, from a local cache.

```
$ gcw run services ap<TAB>
api-gateway   api-worker
$ gcw run services api-gateway --tab logs   # the service's logs, no region needed
$ gcw sql instances main-db -n              # only print the URL
$ gcw storage buckets my-bucket/exports/2026
$ gcw -c work container clusters <TAB>      # clusters from the "work" configuration
$ gcw composer environments etl --airflow   # the environment's Airflow UI
$ gcw billing                               # a service's start page
```

## Scope

- Resource pages, their tabs and lists for the services people open most, with names in TAB; start pages for every other service.
- The context of gcloud: configurations, projects, regions and zones, the signed-in account.
- Linux, macOS and Windows; TAB completion in bash, zsh and fish.

What gcw deliberately does not do:

- **Change cloud resources.** gcw navigates, gcloud operates ([ADR-0004](adr/0004-navigation-only.md)).
- **Change gcloud.** gcw reads gcloud's configuration files and runs `gcloud auth print-access-token`; it writes nothing into gcloud's directory and reads none of its credential files ([ADR-0015](adr/0015-no-gcloud-shell-wrapper.md), [ADR-0023](adr/0023-no-token-database-opt-in.md)).
- **Guess URLs.** Every console URL template is checked by hand; a command gcw does not know fails with a pointer instead of opening a wrong page.

## Roadmap

- **[Milestone 0.1.0](https://github.com/terleckimaciej/gcloud-web/milestone/1): the first release on PyPI.** Console URLs verified by hand, `gcw gcloud …` and an opt-in `gcloud … --web` for turning gcloud commands into pages ([ADR-0020](adr/0020-gcloud-syntax-input.md)), a browser detached from the terminal, and the release process itself.
- **[Planned, not yet scheduled](https://github.com/terleckimaciej/gcloud-web/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement+no%3Amilestone):** more services at a lower cost per service (generic listing for standard Google APIs), Logs Explorer with a ready filter, user overrides of routes, PowerShell completion, Cloud Asset Inventory.
- **[Ideas](https://github.com/terleckimaciej/gcloud-web/issues?q=is%3Aissue+is%3Aopen+label%3Aidea):** proposals worth considering, not planned.
- **[Bugs](https://github.com/terleckimaciej/gcloud-web/issues?q=is%3Aissue+is%3Aopen+label%3Abug).**

Versions stay 0.x while the command syntax may still change; 1.0 comes once it has settled and gcw has been used beyond its author.
