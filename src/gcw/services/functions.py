"""Cloud Functions: console route for functions.

Commands::

    gcw functions                  list of functions
    gcw functions NAME             one function

Functions are the only resource kind, so the kind is omitted (ADR-0012).
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

NAME = "functions"
HELP = "Cloud Functions"
LANDING = "functions/list"
SINGLE_KIND = True

KINDS = {
    "functions": Route(
        path="functions/details/{location}/{name}",
        list_path="functions/list",
        location_property=("functions", "region"),
    ),
}
