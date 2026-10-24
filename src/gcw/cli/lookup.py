"""Finding a named resource for a service command: its location and cached links.

``gcw run services api`` needs the service's region. It is resolved in this
order: ``-l``, then the ``$CLOUDSDK_<SECTION>_<NAME>`` override of the route's
property, then the resource cache (the configured value breaks ties when the
name exists in several locations), then the gcloud configuration.

A stale cache entry is used as is and refreshed in the background. A name that
is not cached triggers one live listing of its kind, whose result is cached.
Lookup problems (no credentials, API disabled) never fail the command; they
print a warning and the configuration is used instead. Not on the completion
path: imported lazily by ``gcw.cli.main``.
"""

import sys

from gcw.cache import refresh, store
from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.services import SERVICES, lister
from gcw.web.route import Link, Route, RouteError


def find_resources(context: Context, service: str, kind: str, name: str) -> list[Resource]:
    """Return the resources of ``kind`` called ``name``, from the cache or a live listing.

    Args:
        context: Account and project; without a project nothing is looked up.
        service: Service name, e.g. ``"run"``.
        kind: Resource kind, e.g. ``"services"``.
        name: Resource name; for buckets, a ``bucket/path`` matches the bucket.

    Returns:
        Matching resources; several when the name exists in more than one
        location, none when it is unknown or the lookup failed.
    """
    if context.project is None:
        return []
    wanted = name.split("/", 1)[0] if (service, kind) == ("storage", "buckets") else name

    entry = store.read(context.account, context.project, service, kind)
    if entry is not None:
        if entry.is_stale():
            refresh.spawn_background(context, service, kind)
        matches = [r for r in entry.resources if r.name == wanted]
        if matches:
            return matches

    results = _live_refresh(context, service, kind)
    if results is None:
        return []
    return [r for r in results if r.name == wanted]


def resource_location(context: Context, service: str, kind: str, route: Route, name: str, flag: str | None) -> str | None:
    """Return the location of a named resource, following the documented order.

    Args:
        context: The command's context.
        service: Service name.
        kind: Resource kind.
        route: The kind's route; its ``location_property`` names the gcloud property.
        name: Resource name.
        flag: Value of ``-l/--location``, if given.

    Returns:
        The location, or ``None`` when no source has one (the route then
        reports what is missing).

    Raises:
        RouteError: The name exists in several locations and the configured
            one is not among them.
    """
    if flag:
        return flag
    configured = context.config.get(*route.location_property) if route.location_property else None
    if route.location_property:
        from_env = context.config.from_environment(*route.location_property)
        if from_env:
            return from_env
    if not route.needs_location:
        return configured

    locations = sorted({r.location for r in find_resources(context, service, kind, name) if r.location})
    if len(locations) == 1:
        return locations[0]
    if len(locations) > 1:
        if configured in locations:
            return configured
        raise RouteError(f"{name} exists in several locations ({', '.join(locations)}); choose one with -l")
    return configured


def link_url(context: Context, service: str, link: Link, name: str) -> str:
    """Return the URL of a cached link, e.g. a Composer environment's Airflow UI.

    Raises:
        RouteError: The resource or its URL is not known, even after a live lookup.
    """
    for resource in find_resources(context, service, link.kind, name):
        url = resource.extra.get(link.extra_key)
        if url:
            return url
    raise RouteError(f"no address known for {name}; check the name or run `gcw cache refresh {service}`")


def _live_refresh(context: Context, service: str, kind: str) -> list[Resource] | None:
    """List one kind now, cache it and return it; ``None`` (with a warning) if that fails."""
    from gcw.api.auth import AuthError

    try:
        results = refresh.refresh(context, {(service, kind): lister(SERVICES[service], kind)})
    except AuthError as error:
        print(f"gcw: warning: cannot look up {kind}: {error}", file=sys.stderr)
        return None
    outcome = results[(service, kind)]
    if isinstance(outcome, Exception):
        print(f"gcw: warning: cannot look up {service} {kind}: {outcome}", file=sys.stderr)
        return None
    entry = store.read(context.account, context.project, service, kind)
    return entry.resources if entry else []
