"""Cloud SQL: console route for instances.

Commands::

    gcw sql                        list of instances
    gcw sql instances [NAME]       list of instances, or one instance (tabs below)

Instance names are unique per project, so the route needs no location.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

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
