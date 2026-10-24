"""Cloud Storage: console route for buckets and folders inside them.

Commands::

    gcw storage                            list of buckets
    gcw storage buckets [BUCKET[/PATH]]    list of buckets, a bucket, or a folder in it

The name may carry a path after the bucket (``my-bucket/exports/2026``); the
console browser opens that folder directly. Buckets need no location.
URL templates are unverified until checked against the real console.
"""

from gcw.web.route import Route

NAME = "storage"
HELP = "Cloud Storage buckets"
LANDING = "storage/browser"

KINDS = {
    "buckets": Route(
        path="storage/browser/{name}",
        list_path="storage/browser",
    ),
}
