"""Pub/Sub: console routes for topics and subscriptions.

Commands::

    gcw pubsub                             list of topics
    gcw pubsub topics [NAME]               list of topics, or one topic
    gcw pubsub subscriptions [NAME]        list of subscriptions, or one subscription

Pub/Sub resources are global, so the routes need no location. Both kinds are
listed with the Pub/Sub API under ``projects/{project}``. URL templates and
endpoints are unverified until checked against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://pubsub.googleapis.com/v1"

NAME = "pubsub"
HELP = "Pub/Sub topics and subscriptions"
LANDING = "cloudpubsub/topic/list"

KINDS = {
    "topics": Route(
        path="cloudpubsub/topic/detail/{name}",
        list_path="cloudpubsub/topic/list",
    ),
    "subscriptions": Route(
        path="cloudpubsub/subscription/detail/{name}",
        list_path="cloudpubsub/subscription/list",
    ),
}


def list_topics(context: Context, token: str) -> list[Resource]:
    """List topics; names look like ``projects/<project>/topics/<name>``."""
    return _list(context, token, "topics")


def list_subscriptions(context: Context, token: str) -> list[Resource]:
    """List subscriptions; names look like ``projects/<project>/subscriptions/<name>``."""
    return _list(context, token, "subscriptions")


def _list(context: Context, token: str, collection: str) -> list[Resource]:
    """List one Pub/Sub collection of the project and keep the last part of each name."""
    from gcw.api.client import list_all

    items = list_all(f"{API}/projects/{context.project}/{collection}", token, collection)
    return [Resource(item["name"].rsplit("/", 1)[-1]) for item in items]
