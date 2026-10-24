"""IAM: the project's permissions page and console route for service accounts.

Commands::

    gcw iam                                    IAM permissions of the project
    gcw iam service-accounts [EMAIL]           list of service accounts, or one account

Service accounts are global, so the route needs no location.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

NAME = "iam"
HELP = "IAM permissions and service accounts"
LANDING = "iam-admin/iam"

KINDS = {
    "service-accounts": Route(
        path="iam-admin/serviceaccounts/details/{name}",
        list_path="iam-admin/serviceaccounts",
    ),
}
