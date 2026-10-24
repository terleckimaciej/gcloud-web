"""Artifact Registry: console route for repositories.

Commands::

    gcw artifacts                          list of repositories
    gcw artifacts repositories [NAME]      list of repositories, or one repository

The console path contains the repository format; the template assumes Docker,
the most common one; the cache records each repository's real format in
``extra["format"]``. The location defaults to ``artifacts/location``.

Repositories are listed per location, like gcloud does: first the project's
locations, then every location in parallel. URL templates and endpoints are
unverified until checked against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://artifactregistry.googleapis.com/v1"

NAME = "artifacts"
HELP = "Artifact Registry repositories"
LANDING = "artifacts"

KINDS = {
    "repositories": Route(
        path="artifacts/docker/{project}/{location}/{name}",
        list_path="artifacts",
        location_property=("artifacts", "location"),
    ),
}


def list_repositories(context: Context, token: str) -> list[Resource]:
    """List repositories in every location of the project, with their format.

    Raises:
        ApiError: The locations could not be listed, or no location answered.
    """
    from gcw.api.client import list_per_location

    project_path = f"{API}/projects/{context.project}"
    found = list_per_location(
        f"{project_path}/locations", f"{project_path}/locations/{{location}}/repositories", token, "repositories"
    )
    return [
        Resource(item["name"].rsplit("/", 1)[-1], location, {"format": item.get("format", "").lower()})
        for location, item in found
    ]
