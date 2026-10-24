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
    """List repositories in every location of the project.

    A location that fails is skipped; if every location fails, the first
    error is raised so the caller can report it.

    Raises:
        ApiError: The locations could not be listed, or no location answered.
    """
    from gcw.api.client import list_all, run_parallel

    project_path = f"{API}/projects/{context.project}"
    locations = [item["locationId"] for item in list_all(f"{project_path}/locations", token, "locations")]
    results = run_parallel({
        location: (lambda location=location: list_all(
            f"{project_path}/locations/{location}/repositories", token, "repositories"
        ))
        for location in locations
    })

    errors = [result for result in results.values() if isinstance(result, Exception)]
    if errors and len(errors) == len(results):
        raise errors[0]
    return [
        Resource(item["name"].rsplit("/", 1)[-1], location, {"format": item.get("format", "").lower()})
        for location, items in results.items()
        if not isinstance(items, Exception)
        for item in items
    ]
