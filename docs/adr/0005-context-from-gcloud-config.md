# 0005. Context from gcloud configuration files

- Status: Accepted
- Date: 2026-10-11

## Context

The account, project and region are already stored in gcloud configurations. Calling `gcloud config get-value` costs about 1 s; reading the INI files costs about 1 ms. Switching with `gcloud config configurations activate` is global, across all terminals.

## Decision

- Read the files directly: `$CLOUDSDK_CONFIG` or `~/.config/gcloud`, then `active_config` and `configurations/config_<name>`.
- Precedence: CLI flag > environment (`CLOUDSDK_ACTIVE_CONFIG_NAME`, `CLOUDSDK_CORE_PROJECT`, `CLOUDSDK_CORE_ACCOUNT`…) > configuration file > cache > live lookup.
- Switching: `-c/--configuration` and `-p/--project` for a single command, `gcw env <config>` for the current shell.

## Consequences

No configuration of our own, and gcw always agrees with gcloud. The INI format has been stable for years. If it ever changes, the fallback is `gcloud config list --format=json`.
