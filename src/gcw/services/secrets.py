"""Secret Manager: console route for secrets.

Commands::

    gcw secrets                    list of secrets
    gcw secrets NAME               one secret (tabs below)

Secrets are the only resource kind, so the kind is omitted (ADR-0012).
Secrets are global, so the route needs no location.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

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
