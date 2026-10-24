"""Cloud Functions: console route for functions.

Commands::

    gcw functions                  list of functions
    gcw functions NAME             one function

Functions are the only resource kind, so the kind is omitted (ADR-0012).
They are listed with the Cloud Functions API v2 across all regions
(``locations/-``). URL templates and endpoints are unverified until checked
against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://cloudfunctions.googleapis.com/v2"

NAME = "functions"
HELP = "Cloud Functions"
LANDING = "functions/list"
SINGLE_KIND = True

KINDS = {
    "functions": Route(
        path="functions/details/{location}/{name}",
        list_path="functions/list",
        location_property=("functions", "region"),
    ),
}


def list_functions(context: Context, token: str) -> list[Resource]:
    """List functions in all regions; names look like ``projects/p/locations/r/functions/f``."""
    from gcw.api.client import list_all, path_segment

    items = list_all(f"{API}/projects/{context.project}/locations/-/functions", token, "functions")
    return [Resource(item["name"].rsplit("/", 1)[-1], path_segment(item["name"], "locations")) for item in items]
