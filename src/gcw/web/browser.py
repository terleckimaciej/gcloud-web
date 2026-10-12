"""Open a console URL in the user's default browser."""

import webbrowser


def open_url(url: str) -> bool:
    """Open ``url`` in the default browser.

    Uses the standard ``webbrowser`` module, which respects ``$BROWSER`` and
    works on Linux, macOS and Windows (including Git Bash).

    Returns:
        ``True`` if a browser was launched, ``False`` if none is available
        (e.g. over SSH), so the caller can print the URL instead.
    """
    return webbrowser.open(url)
