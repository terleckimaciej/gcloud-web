"""Cloud Run: console routes for services and jobs.

Commands::

    gcw run                        Cloud Run overview
    gcw run services [NAME]        list of services, or one service (tabs below)
    gcw run jobs [NAME]            list of jobs, or one job (tabs below)

Resource listing for completion will be added with the resource cache.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

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
