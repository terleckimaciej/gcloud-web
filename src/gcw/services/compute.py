"""Compute Engine: console route for VM instances.

Commands::

    gcw compute                    Compute Engine overview
    gcw compute instances [NAME]   list of VM instances, or one instance

Instances are zonal: ``-l/--zone`` or the ``compute/zone`` property. They are
listed with the Compute Engine ``aggregated/instances`` endpoint, which covers
every zone in one paginated request. URL templates and endpoints are
unverified until checked against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://compute.googleapis.com/compute/v1"

NAME = "compute"
HELP = "Compute Engine VM instances"
LANDING = "compute/overview"

KINDS = {
    "instances": Route(
        path="compute/instancesDetail/zones/{location}/instances/{name}",
        list_path="compute/instances",
        location_label="zone",
        location_property=("compute", "zone"),
    ),
}


def list_instances(context: Context, token: str) -> list[Resource]:
    """List VM instances in all zones.

    Each page maps ``"zones/<zone>"`` to ``{"instances": [...]}``; zones
    without instances carry a warning instead and are skipped.
    """
    from gcw.api.client import iter_pages

    url = f"{API}/projects/{context.project}/aggregated/instances"
    return [
        Resource(instance["name"], scope.removeprefix("zones/"))
        for page in iter_pages(url, token, {"returnPartialSuccess": "true"})
        for scope, scoped in page.get("items", {}).items()
        for instance in scoped.get("instances", [])
    ]
