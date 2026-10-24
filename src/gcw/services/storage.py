"""Cloud Storage: console route for buckets and folders inside them.

Commands::

    gcw storage                            list of buckets
    gcw storage buckets [BUCKET[/PATH]]    list of buckets, a bucket, or a folder in it

The name may carry a path after the bucket (``my-bucket/exports/2026``); the
console browser opens that folder directly. Buckets need no location; the
cached one is shown in listings only. Buckets are listed with the Cloud
Storage JSON API. URL templates and endpoints are unverified until checked
against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://storage.googleapis.com/storage/v1"

NAME = "storage"
HELP = "Cloud Storage buckets"
LANDING = "storage/browser"

KINDS = {
    "buckets": Route(
        path="storage/browser/{name}",
        list_path="storage/browser",
    ),
}


def list_buckets(context: Context, token: str) -> list[Resource]:
    """List buckets of the project; the API reports locations in upper case."""
    from gcw.api.client import list_all

    items = list_all(f"{API}/b", token, "items", {"project": context.project})
    return [Resource(item["name"], (item.get("location") or "").lower() or None) for item in items]
