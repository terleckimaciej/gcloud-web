"""Dataproc: console routes for clusters, serverless batches and jobs.

Commands::

    gcw dataproc                   list of clusters
    gcw dataproc clusters [NAME]   list of clusters, or one cluster (tabs below)
    gcw dataproc batches [ID]      list of batches, or one batch
    gcw dataproc jobs [ID]         list of jobs, or one job

Cluster and job pages take the region as a query parameter; ``gcw.web.url``
appends ``project`` to it. The region defaults to ``dataproc/region``.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

NAME = "dataproc"
HELP = "Dataproc clusters, batches and jobs"
LANDING = "dataproc/clusters"

KINDS = {
    "clusters": Route(
        path="dataproc/clusters/{name}/{tab}?region={location}",
        list_path="dataproc/clusters",
        tabs=("monitoring", "jobs", "vms", "configuration"),
        location_property=("dataproc", "region"),
    ),
    "batches": Route(
        path="dataproc/batches/{location}/{name}",
        list_path="dataproc/batches",
        location_property=("dataproc", "region"),
    ),
    "jobs": Route(
        path="dataproc/jobs/{name}?region={location}",
        list_path="dataproc/jobs",
        location_property=("dataproc", "region"),
    ),
}
