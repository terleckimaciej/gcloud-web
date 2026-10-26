# Architecture Decision Records

| # | Decision | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record decisions as ADRs | Accepted |
| [0002](0002-python-stdlib-only.md) | Python with a standard-library-only runtime | Accepted |
| [0003](0003-src-layout-uv.md) | `src/` layout and uv | Accepted |
| [0004](0004-navigation-only.md) | gcw navigates, gcloud operates | Accepted |
| [0005](0005-context-from-gcloud-config.md) | Context from gcloud configuration files | Accepted |
| [0006](0006-cache-never-blocks-completion.md) | Cache: completion never waits for the network | Accepted |
| [0007](0007-reuse-gcloud-auth.md) | Authentication shared with gcloud | Superseded by 0016 |
| [0008](0008-per-service-list-no-asset-inventory.md) | Each service's REST `list`, Cloud Asset Inventory deferred | Accepted |
| [0009](0009-gcloud-web-shell-wrapper.md) | `gcloud web` through a shell wrapper | Superseded by 0015 |
| [0010](0010-routes-as-data.md) | URL routes as data in service modules | Accepted, partially superseded by 0012 |
| [0011](0011-project-structure.md) | Project structure: layers + flat `services/` | Accepted, partially superseded by 0012 |
| [0012](0012-cli-syntax-and-routes.md) | CLI syntax, flags and the shape of routes | Accepted |
| [0013](0013-supported-platforms.md) | Supported platforms and CI | Accepted |
| [0014](0014-docs-in-repo.md) | Documentation in the repository | Accepted; open work in issues again through 0021 |
| [0015](0015-no-gcloud-shell-wrapper.md) | No shell wrapper around gcloud | Accepted, supersedes 0009; partially superseded by 0024 |
| [0016](0016-official-token-command-by-default.md) | Access tokens from the official gcloud command | Accepted, supersedes 0007; partially superseded by 0023 |
| [0017](0017-plan-checklists-until-issues.md) | Milestone checklists stay in the plan for now | Superseded by 0021 |
| [0018](0018-cache-commands.md) | Cache commands live under `gcw cache` | Accepted |
| [0019](0019-service-names-follow-gcloud.md) | Service names follow gcloud's command groups | Accepted |
| [0020](0020-gcloud-syntax-input.md) | gcloud command syntax as gcw input | Accepted |
| [0021](0021-open-work-in-github-issues.md) | Open work lives in GitHub issues; docs carry no status | Accepted, supersedes 0017 |
| [0022](0022-tab-budget-100ms.md) | TAB completion budget: 100 ms | Accepted |
| [0023](0023-no-token-database-opt-in.md) | No opt-in for reading `access_tokens.db` | Accepted, partially supersedes 0016 |
| [0024](0024-opt-in-gcloud-web-function.md) | gcw prints an opt-in `gcloud … --web` shell function | Accepted, partially supersedes 0015 |

New ADR: copy [template.md](template.md) and add a row to this table.
