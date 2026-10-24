"""Minimal REST client for Google APIs on the standard library.

Only what resource listing needs (ADR-0008): authenticated GET requests that
return JSON, pagination over ``nextPageToken``, and running independent
requests in parallel threads. Imported lazily by ``list_*`` functions, never
on the completion path, because ``urllib.request`` pulls in ``ssl``.
"""

import json
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_TIMEOUT_SECONDS = 30
_MAX_WORKERS = 8

K = TypeVar("K")
T = TypeVar("T")


class ApiError(RuntimeError):
    """A Google API request failed.

    Attributes:
        status: HTTP status code, or ``None`` when no response was received
            (network error, timeout).
    """

    def __init__(self, message: str, status: int | None = None):
        """Store the status code next to the message."""
        super().__init__(message)
        self.status = status


def get_json(url: str, token: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    """Send an authenticated GET request and return the decoded JSON body.

    Args:
        url: Full API URL, e.g. ``"https://run.googleapis.com/v2/projects/p/locations/-/services"``.
        token: OAuth access token (see ``gcw.api.auth``).
        params: Query parameters to append.

    Returns:
        The response body; an empty dict for an empty body.

    Raises:
        ApiError: The server answered with an error status, or no answer arrived.
    """
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            body = response.read()
    except HTTPError as error:
        raise ApiError(_error_message(error), status=error.code) from None
    except (URLError, TimeoutError) as error:
        raise ApiError(f"request to {url} failed: {getattr(error, 'reason', error)}") from None
    return json.loads(body) if body else {}


def iter_pages(url: str, token: str, params: dict[str, str] | None = None) -> Iterator[dict[str, Any]]:
    """Yield every page of a paginated endpoint, following ``nextPageToken``.

    Args:
        url: Full URL of the endpoint.
        token: OAuth access token.
        params: Extra query parameters sent with every page.

    Yields:
        Each decoded page, in order.

    Raises:
        ApiError: Any page request failed.
    """
    page_params = dict(params or {})
    while True:
        page = get_json(url, token, page_params)
        yield page
        next_token = page.get("nextPageToken")
        if not next_token:
            return
        page_params["pageToken"] = next_token


def list_all(url: str, token: str, items_key: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Fetch every page of a ``list`` endpoint and return all items.

    Args:
        url: Full URL of the list endpoint.
        token: OAuth access token.
        items_key: Field holding the items in each page, e.g. ``"services"``.
        params: Extra query parameters sent with every page.

    Returns:
        Items from all pages, in order.

    Raises:
        ApiError: Any page request failed.
    """
    return [item for page in iter_pages(url, token, params) for item in page.get(items_key, [])]


def list_per_location(
    locations_url: str, list_url: str, token: str, items_key: str
) -> list[tuple[str, dict[str, Any]]]:
    """List a collection in every location, for APIs that cannot aggregate with ``locations/-``.

    First fetches the locations, then lists each one in parallel. A location
    that fails is skipped; if every location fails, the first error is raised.

    Args:
        locations_url: Endpoint listing the locations; items have ``locationId``.
        list_url: Endpoint listing the collection, with a ``{location}`` placeholder.
        token: OAuth access token.
        items_key: Field holding the items in each page of ``list_url``.

    Returns:
        ``(location, item)`` pairs for every item found.

    Raises:
        ApiError: The locations could not be listed, or no location answered.
    """
    locations = [item["locationId"] for item in list_all(locations_url, token, "locations")]
    results = run_parallel({
        location: (lambda location=location: list_all(list_url.format(location=location), token, items_key))
        for location in locations
    })
    errors = [result for result in results.values() if isinstance(result, Exception)]
    if errors and len(errors) == len(results):
        raise errors[0]
    return [
        (location, item)
        for location, items in results.items()
        if not isinstance(items, Exception)
        for item in items
    ]


def path_segment(resource_name: str, collection: str) -> str | None:
    """Return the value that follows ``collection`` in a resource name.

    Example: ``path_segment("projects/p/locations/eu1/services/api", "locations")``
    returns ``"eu1"``. Also works on self links such as
    ``"https://.../zones/eu1-b"``.

    Returns:
        The segment, or ``None`` if ``collection`` is not in the name.
    """
    parts = resource_name.split("/")
    for index, part in enumerate(parts[:-1]):
        if part == collection:
            return parts[index + 1]
    return None


def run_parallel(tasks: dict[K, Callable[[], T]]) -> dict[K, T | Exception]:
    """Run independent tasks in threads and collect each result or exception.

    A failing task does not stop the others: its exception is returned in
    place of a result, so the caller can report it and keep the rest.

    Args:
        tasks: Callables keyed by a name the caller chooses.

    Returns:
        For each key, the task's return value or the exception it raised.
    """
    if not tasks:
        return {}
    with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(tasks))) as pool:
        futures = {key: pool.submit(task) for key, task in tasks.items()}
    results: dict[K, T | Exception] = {}
    for key, future in futures.items():
        error = future.exception()
        results[key] = error if error is not None else future.result()
    return results


def _error_message(error: HTTPError) -> str:
    """Return the message from a Google API error body, or the HTTP reason."""
    try:
        detail = json.loads(error.read())["error"]["message"]
    except (ValueError, KeyError, TypeError):
        detail = error.reason
    return f"HTTP {error.code}: {detail}"
