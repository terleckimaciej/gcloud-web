# 0025. Releases on PyPI, driven by manual tags

- Status: Accepted
- Date: 2026-11-05

## Context

gcw installs from GitHub today (`pipx install git+https://github.com/terleckimaciej/gcloud-web`). The usual way to ship a Python CLI is PyPI, installed with `pipx install gcw` or `uv tool install gcw`; it also gives users a version to pin and to report in bugs. The name `gcw` is free on PyPI and already set in `pyproject.toml`.

A release is published to the world and cannot be taken back: PyPI never accepts the same version twice, even after a deletion. The process has to make a wrong or accidental release hard, without making a deliberate one slow. Long-lived API tokens in repository secrets are the usual weak point of publishing from CI.

## Decision

- gcw is published on PyPI as `gcw`.
- Releases are manual: bump `version` in `pyproject.toml`, add the version to `CHANGELOG.md`, merge, then push a tag `vX.Y.Z` on `master`.
- `.github/workflows/release.yml` runs on `v*` tags, builds with `uv build` and publishes through PyPI Trusted Publishing (OIDC). There are no PyPI API tokens.
- Safeguards:
  - the workflow fails before building when the tag does not equal the `pyproject.toml` version;
  - PyPI rejects a version that was already published;
  - the publish job runs in the GitHub environment `pypi`, which waits for the owner's approval.
- Versions stay 0.x while gcw is a prototype. A breaking change bumps the minor version, anything else the patch version.

## Consequences

- `pipx install gcw` and `uv tool install gcw` work, and `gcw --version` names a published release.
- No secret to leak or rotate: PyPI trusts only this repository's `release.yml` running in the `pypi` environment.
- Every release takes a version bump, a tag and an approval click; a stray tag stops at the version check or at the approval.
- The version lives in one place, `pyproject.toml`; the tag must follow it, not the other way round.
- Setup outside the repository: a pending Trusted Publisher on pypi.org and the `pypi` environment on GitHub.
