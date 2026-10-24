"""Cloud Composer: console route for environments.

Commands::

    gcw composer                           list of environments
    gcw composer environments [NAME]       list of environments, or one environment (tabs below)

The location defaults to ``composer/location``.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

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
