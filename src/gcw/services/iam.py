"""IAM: the project's permissions page and console route for service accounts.

Commands::

    gcw iam                                    IAM permissions of the project
    gcw iam service-accounts [EMAIL]           list of service accounts, or one account

Service accounts are global, so the route needs no location. They are listed
with the IAM API, by email. URL templates and endpoints are unverified until
checked against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://iam.googleapis.com/v1"

NAME = "iam"
HELP = "IAM permissions and service accounts"
LANDING = "iam-admin/iam"

KINDS = {
    "service-accounts": Route(
        path="iam-admin/serviceaccounts/details/{name}",
        list_path="iam-admin/serviceaccounts",
    ),
}


def list_service_accounts(context: Context, token: str) -> list[Resource]:
    """List service accounts of the project by email."""
    from gcw.api.client import list_all

    items = list_all(f"{API}/projects/{context.project}/serviceAccounts", token, "accounts")
    return [Resource(item["email"]) for item in items]
