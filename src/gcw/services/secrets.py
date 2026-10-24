"""Secret Manager: console route for secrets.

Commands::

    gcw secrets                    list of secrets
    gcw secrets NAME               one secret (tabs below)

Secrets are the only resource kind, so the kind is omitted (ADR-0012).
Secrets are global, so the route needs no location. They are listed with the
Secret Manager API. URL templates and endpoints are unverified until checked
against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://secretmanager.googleapis.com/v1"

NAME = "secrets"
HELP = "Secret Manager secrets"
LANDING = "security/secret-manager"
SINGLE_KIND = True

KINDS = {
    "secrets": Route(
        path="security/secret-manager/secret/{name}/{tab}",
        list_path="security/secret-manager",
        tabs=("versions", "overview", "permissions", "logs"),
    ),
}


def list_secrets(context: Context, token: str) -> list[Resource]:
    """List secrets; names look like ``projects/<number>/secrets/<name>``."""
    from gcw.api.client import list_all

    items = list_all(f"{API}/projects/{context.project}/secrets", token, "secrets")
    return [Resource(item["name"].rsplit("/", 1)[-1]) for item in items]
