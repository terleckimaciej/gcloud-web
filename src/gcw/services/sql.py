"""Cloud SQL: console route for instances.

Commands::

    gcw sql                        list of instances
    gcw sql instances [NAME]       list of instances, or one instance (tabs below)

Instance names are unique per project, so the route needs no location; the
cached region is shown in listings only. Instances are listed with the Cloud
SQL Admin API. URL templates and endpoints are unverified until checked
against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://sqladmin.googleapis.com/v1"

NAME = "sql"
HELP = "Cloud SQL instances"
LANDING = "sql/instances"

KINDS = {
    "instances": Route(
        path="sql/instances/{name}/{tab}",
        list_path="sql/instances",
        tabs=("overview", "connections", "users", "databases", "backups", "replicas", "operations"),
    ),
}


def list_instances(context: Context, token: str) -> list[Resource]:
    """List Cloud SQL instances of the project."""
    from gcw.api.client import list_all

    items = list_all(f"{API}/projects/{context.project}/instances", token, "items")
    return [Resource(item["name"], item.get("region")) for item in items]
