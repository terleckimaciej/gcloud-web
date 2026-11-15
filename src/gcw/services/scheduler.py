"""Cloud Scheduler: console route for jobs.

Commands::

    gcw scheduler                          list of jobs
    gcw scheduler jobs [NAME]              list of jobs, or one job

Jobs live in a location, which defaults to ``scheduler/location``. They are
listed per location, like gcloud does: first the project's locations, then
every location in parallel. URL templates and endpoints are unverified until
checked against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://cloudscheduler.googleapis.com/v1"

NAME = "scheduler"
HELP = "Cloud Scheduler jobs"
LANDING = "cloudscheduler"

KINDS = {
    "jobs": Route(
        path="cloudscheduler/jobs/edit/{location}/{name}",
        list_path="cloudscheduler",
        location_property=("scheduler", "location"),
    ),
}


def list_jobs(context: Context, token: str) -> list[Resource]:
    """List jobs in every location of the project; names end with the job ID.

    Raises:
        ApiError: The locations could not be listed, or no location answered.
    """
    from gcw.api.client import list_per_location

    project_path = f"{API}/projects/{context.project}"
    found = list_per_location(
        f"{project_path}/locations", f"{project_path}/locations/{{location}}/jobs", token, "jobs"
    )
    return [Resource(item["name"].rsplit("/", 1)[-1], location) for location, item in found]
