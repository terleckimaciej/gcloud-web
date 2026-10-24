# 0012. CLI syntax, flags and the shape of routes

- Status: Accepted, partially supersedes 0010 (placeholders, default tab) and 0011 (location of `Route`, `--copy`)
- Date: 2026-10-13

## Context

Implementing M1 and M2 involved several user-visible decisions that were either not recorded or changed earlier ADRs:
- how to name the resource kind and the resource;
- how to give a region or zone;
- what `-n` prints;
- when to add `authuser`;
- where route logic lives.

The model is gcloud, which names the resource kind explicitly when there are several (`gcloud run services describe`) and omits it when there is one (`gcloud secrets describe`). This works because its second word is a verb. gcw has no verbs, because its only action is "open".

## Decision

### Service command syntax

```
gcw <service>                       service overview (LANDING)
gcw <service> <kind>                list of resources of that kind (list_path)
gcw <service> <kind> <name>         one resource
gcw <service> <name>                one resource of a service with a single kind
```

- **Service with several kinds:** the kind is always explicit (`gcw run services api`, `gcw run jobs nightly`). There is no default kind, so a resource name is never mistaken for a kind.
- **Service with a single kind:** the kind is omitted (`gcw secrets db-password`), as in gcloud. The rule applies to the whole service, not to a single invocation, so the second word is unambiguous.
- **Kind names** are gcloud's collection names (`services`, `instances`, `clusters`, `buckets`…). Short aliases can be added later.
- **Sub-resources** are tabs (`--tab versions`), not separate kinds.

### Flags

- `-l/--location` with the aliases `--region` and `--zone`. It is one flag; the service knows whether it means a region or a zone. The default comes from the gcloud property named by the route (e.g. `run/region`), and from M3 also from the cache.
- `--tab`: the tab of the resource page. The default is the first allowed one. `--tab` or `-l` without a resource name is an error.
- The global flags `-p/--project`, `-c/--configuration`, `-n/--no-browser` and `--no-authuser` work before and after the command.
- `-n/--no-browser` (named as in `gh browse`) only prints the URL.
- No `--copy`: `gcw -n | wl-copy` (or `clip.exe`, `pbcopy`) is enough for the clipboard.

### `authuser`

A URL opened in the browser gets `authuser=<gcloud account>`, so the console uses the right Google account when several are signed in. A URL printed by `-n` comes **without** `authuser`, so it does not reveal an email address and is fit for sharing. `--no-authuser` drops the parameter when opening as well.

### Routes

- `Route` lives in `gcw/web/route.py`, because it is "template → URL path" logic, which is the scope of the `web` layer. In `services/__init__.py` it would create an import cycle with the service modules.
- A template has one location placeholder, `{location}`, instead of `{region}` and `{zone}`. The `location_label` field ("region" or "zone") is used only in messages.
- The default tab is the first entry of `tabs`, without a separate field.
- `Route` fields: `path`, `list_path`, `tabs`, `location_label`, `location_property`.
- A missing value raises `RouteError` with a hint, e.g. "missing region (use -l/--location or `gcloud config set run/region`)". The CLI then exits with code 2.

## Consequences

- The syntax is predictable: like gcloud, just without verbs.
- TAB (M4) suggests kinds after `gcw <service> `, or, for single-kind services, names right away.
- When a single-kind service gains a second kind, its syntax switches to an explicit kind. That is a breaking change, and a rare one, because sub-resources are tabs.
- The parser and registry have to handle single-kind services. For now the only service is Cloud Run (two kinds), so this comes with the first single-kind service.
