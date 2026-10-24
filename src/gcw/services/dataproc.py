"""Dataproc: console routes for clusters, serverless batches and jobs.

Commands::

    gcw dataproc                   list of clusters
    gcw dataproc clusters [NAME]   list of clusters, or one cluster (tabs below)
    gcw dataproc batches [ID]      list of batches, or one batch
    gcw dataproc jobs [ID]         list of jobs, or one job

Cluster and job pages take the region as a query parameter; ``gcw.web.url``
appends ``project`` to it. The region defaults to ``dataproc/region``.

The Dataproc API has no cross-region listing, so resources are listed in one
region only: ``dataproc/region``, else ``compute/region``; with neither set the
lists are empty. URL templates and endpoints are unverified until checked
against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://dataproc.googleapis.com/v1"

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


def list_clusters(context: Context, token: str) -> list[Resource]:
    """List clusters in the configured region."""
    from gcw.api.client import list_all

    region = _region(context)
    if region is None:
        return []
    items = list_all(f"{API}/projects/{context.project}/regions/{region}/clusters", token, "clusters")
    return [Resource(item["clusterName"], region) for item in items]


def list_batches(context: Context, token: str) -> list[Resource]:
    """List serverless batches in the configured region; names end with the batch ID."""
    from gcw.api.client import list_all

    region = _region(context)
    if region is None:
        return []
    items = list_all(f"{API}/projects/{context.project}/locations/{region}/batches", token, "batches")
    return [Resource(item["name"].rsplit("/", 1)[-1], region) for item in items]


def list_jobs(context: Context, token: str) -> list[Resource]:
    """List jobs in the configured region; the ID is in ``reference.jobId``."""
    from gcw.api.client import list_all

    region = _region(context)
    if region is None:
        return []
    items = list_all(f"{API}/projects/{context.project}/regions/{region}/jobs", token, "jobs")
    return [Resource(item["reference"]["jobId"], region) for item in items]


def _region(context: Context) -> str | None:
    """Return the region to list in: ``dataproc/region``, else ``compute/region``."""
    return context.config.get("dataproc", "region") or context.config.get("compute", "region")
