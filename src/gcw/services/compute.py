"""Compute Engine: console route for VM instances.

Commands::

    gcw compute                    Compute Engine overview
    gcw compute instances [NAME]   list of VM instances, or one instance

Instances are zonal: ``-l/--zone`` or the ``compute/zone`` property.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

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
