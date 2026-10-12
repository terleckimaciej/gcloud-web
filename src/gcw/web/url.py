"""Build Google Cloud Console URLs from a console path and the current context.

Every gcw URL is ``https://console.cloud.google.com/<path>`` plus the
``project`` query parameter. The optional ``authuser`` parameter (an account
email) makes the console use the same Google account as gcloud when several
accounts are signed in to the browser; the CLI decides when to include it.
"""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CONSOLE_HOST = "console.cloud.google.com"


def console_url(path: str, project: str | None = None, account: str | None = None) -> str:
    """Return the full console URL for ``path`` with ``project`` and ``authuser`` added.

    ``path`` may already carry its own query (``dataproc/clusters/x?region=r``)
    or matrix parameters (``logs/query;query=...``); both are preserved.
    Parameters already present in ``path`` are never overwritten.

    Args:
        path: Console path such as ``"run"``; a leading ``/`` is optional.
        project: Project ID for the ``project`` parameter; omitted when ``None``.
        account: Google account email for the ``authuser`` parameter; omitted when ``None``.

    Returns:
        The absolute console URL.
    """
    parts = urlsplit(f"https://{CONSOLE_HOST}/{path.lstrip('/')}")
    params = parse_qsl(parts.query, keep_blank_values=True)
    present = {key for key, _ in params}
    for key, value in (("project", project), ("authuser", account)):
        if value and key not in present:
            params.append((key, value))
    return urlunsplit(parts._replace(query=urlencode(params)))
