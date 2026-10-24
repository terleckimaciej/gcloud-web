"""Artifact Registry: console route for repositories.

Commands::

    gcw artifacts                          list of repositories
    gcw artifacts repositories [NAME]      list of repositories, or one repository

The console path contains the repository format; the template assumes Docker,
the most common one. The location defaults to ``artifacts/location``.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

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
