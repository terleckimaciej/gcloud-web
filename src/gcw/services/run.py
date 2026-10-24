"""Cloud Run: console routes for services and jobs.

Commands::

    gcw run                        Cloud Run overview
    gcw run services [NAME]        list of services, or one service (tabs below)
    gcw run jobs [NAME]            list of jobs, or one job (tabs below)

Resources are listed with the Cloud Run Admin API v2 across all regions
(``locations/-``). URL templates and endpoints are unverified until checked
against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://run.googleapis.com/v2"

NAME = "run"
HELP = "Cloud Run services and jobs"
LANDING = "run"

KINDS = {
    "services": Route(
        path="run/detail/{location}/{name}/{tab}",
        list_path="run/services",
        tabs=("metrics", "logs", "revisions", "triggers", "yaml"),
        location_property=("run", "region"),
    ),
    "jobs": Route(
        path="run/jobs/details/{location}/{name}/{tab}",
        list_path="run/jobs",
        tabs=("executions", "logs", "triggers", "yaml"),
        location_property=("run", "region"),
    ),
}


def list_services(context: Context, token: str) -> list[Resource]:
    """List Cloud Run services in all regions of the project."""
    return _list(context, token, "services")


def list_jobs(context: Context, token: str) -> list[Resource]:
    """List Cloud Run jobs in all regions of the project."""
    return _list(context, token, "jobs")


def _list(context: Context, token: str, collection: str) -> list[Resource]:
    """List one collection; names look like ``projects/p/locations/r/services/s``."""
    from gcw.api.client import list_all, path_segment

    items = list_all(f"{API}/projects/{context.project}/locations/-/{collection}", token, collection)
    return [Resource(item["name"].rsplit("/", 1)[-1], path_segment(item["name"], "locations")) for item in items]
