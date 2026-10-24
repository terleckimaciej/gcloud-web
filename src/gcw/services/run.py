"""Cloud Run: console routes for services and jobs.

Commands::

    gcw run                        Cloud Run overview
    gcw run services [NAME]        list of services, or one service (tabs below)
    gcw run jobs [NAME]            list of jobs, or one job (tabs below)

Resources are listed with the Cloud Run Admin API v2. Services are listed
across all regions with ``locations/-``; jobs reject that (HTTP 400), so they
are listed region by region, with the regions taken from the v1 API. URL
templates are unverified until checked against the real console.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://run.googleapis.com/v2"
LOCATIONS = "https://run.googleapis.com/v1/projects/{project}/locations"

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
    """List Cloud Run services in all regions; names look like ``projects/p/locations/r/services/s``."""
    from gcw.api.client import list_all, path_segment

    items = list_all(f"{API}/projects/{context.project}/locations/-/services", token, "services")
    return [Resource(item["name"].rsplit("/", 1)[-1], path_segment(item["name"], "locations")) for item in items]


def list_jobs(context: Context, token: str) -> list[Resource]:
    """List Cloud Run jobs region by region, since jobs cannot be listed with ``locations/-``."""
    from gcw.api.client import list_per_location

    found = list_per_location(
        LOCATIONS.format(project=context.project),
        f"{API}/projects/{context.project}/locations/{{location}}/jobs",
        token,
        "jobs",
    )
    return [Resource(item["name"].rsplit("/", 1)[-1], location) for location, item in found]
