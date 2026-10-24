"""Cloud Composer: console route for environments.

Commands::

    gcw composer                           list of environments
    gcw composer environments [NAME]       list of environments, or one environment (tabs below)
    gcw composer environments NAME --airflow   the environment's Airflow web UI

The location defaults to ``composer/location``.

The Composer API has no cross-location listing, so environments are listed in
one location only: ``composer/location``, else ``compute/region``. Each cached
environment keeps its Airflow web UI address in ``extra["airflow_uri"]``. URL
templates and endpoints are unverified until checked against the real console
and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Link, Route

API = "https://composer.googleapis.com/v1"

NAME = "composer"
HELP = "Cloud Composer environments"
LANDING = "composer/environments"

KINDS = {
    "environments": Route(
        path="composer/environments/detail/{location}/{name}/{tab}",
        list_path="composer/environments",
        tabs=("monitoring", "logs", "dags"),
        location_property=("composer", "location"),
    ),
}

LINKS = {
    "airflow": Link(kind="environments", extra_key="airflow_uri", help="open the environment's Airflow web UI"),
}


def list_environments(context: Context, token: str) -> list[Resource]:
    """List environments in the configured location, with their Airflow UI address."""
    from gcw.api.client import list_all

    location = context.config.get("composer", "location") or context.config.get("compute", "region")
    if location is None:
        return []
    url = f"{API}/projects/{context.project}/locations/{location}/environments"
    return [
        Resource(
            item["name"].rsplit("/", 1)[-1],
            location,
            {"airflow_uri": uri} if (uri := item.get("config", {}).get("airflowUri")) else {},
        )
        for item in list_all(url, token, "environments")
    ]
