# 0019. Service names follow gcloud's command groups

- Status: Accepted
- Date: 2026-10-24

## Context

[ADR-0012](0012-cli-syntax-and-routes.md) made gcw "gcloud without verbs" and took kind names from gcloud's collections, but said nothing about service names. Every service matched its gcloud group (`run`, `sql`, `storage`, `compute`…) except Google Kubernetes Engine, which shipped as `gcw gke` while gcloud calls it `gcloud container clusters`.

The point of mirroring gcloud is that a user turns `gcloud run services describe api` into `gcw run services api` by dropping the verb. A single product-named exception breaks that rule and has to be learned separately.

## Decision

- A service command is named after its gcloud command group, not after the product: `gcw container clusters`, not `gcw gke clusters`.
- This applies to every new service as well. A short product alias may be added later, but the gcloud name is always the canonical one.
- `gcw gke` is removed without an alias, since gcw has not been released.

## Consequences

- Any `gcloud <group> <kind> describe NAME` becomes `gcw <group> <kind> NAME`, with no exceptions to remember.
- `container` is less obvious than `gke` for someone who does not know gcloud; TAB completion and `gcw services` show it with its description ("Google Kubernetes Engine clusters").
- Cache files move from `gke.clusters.json` to `container.clusters.json`; the old file is ignored and the next refresh writes the new one.
