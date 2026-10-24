"""Google Kubernetes Engine: console route for clusters.

Commands::

    gcw gke                        GKE overview
    gcw gke clusters [NAME]        list of clusters, or one cluster (tabs below)

A cluster is either regional or zonal, so ``{location}`` may be either. The
default comes from ``compute/region``, since regional clusters are the usual
choice; the resource cache supplies the real location of a named cluster.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

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
