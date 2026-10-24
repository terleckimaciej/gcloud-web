"""Google Kubernetes Engine: console route for clusters.

Commands::

    gcw gke                        GKE overview
    gcw gke clusters [NAME]        list of clusters, or one cluster (tabs below)

A cluster is either regional or zonal, so ``{location}`` may be either. The
default comes from ``compute/region``, since regional clusters are the usual
choice; the resource cache supplies the real location of a named cluster.
Clusters are listed with the GKE API across all locations (``locations/-``).
URL templates and endpoints are unverified until checked against the real
console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://container.googleapis.com/v1"

NAME = "gke"
HELP = "Google Kubernetes Engine clusters"
LANDING = "kubernetes/list/overview"

KINDS = {
    "clusters": Route(
        path="kubernetes/clusters/details/{location}/{name}/{tab}",
        list_path="kubernetes/list/overview",
        tabs=("details", "nodes", "storage", "observability", "logs"),
        location_label="location",
        location_property=("compute", "region"),
    ),
}


def list_clusters(context: Context, token: str) -> list[Resource]:
    """List clusters in all locations; each carries its zone or region in ``location``."""
    from gcw.api.client import get_json

    page = get_json(f"{API}/projects/{context.project}/locations/-/clusters", token)
    return [Resource(cluster["name"], cluster.get("location")) for cluster in page.get("clusters", [])]
