"""Open a console URL in the user's default browser.

On Linux the browser is started through ``xdg-open`` (``wslview`` under WSL)
with its output discarded and in a new session, so nothing the browser prints
lands in the terminal after gcw has returned. Everywhere else, and when
``$BROWSER`` is set, the standard ``webbrowser`` module does the work.
"""

import os
import shutil
import subprocess
import sys
import webbrowser


def open_url(url: str) -> bool:
    """Open ``url`` in the default browser.

    Returns:
        ``True`` if a browser was launched, ``False`` if none is available
        (e.g. over SSH), so the caller can print the URL instead.
    """
    launcher = _linux_launcher()
    if launcher is not None:
        try:
            subprocess.Popen(
                [launcher, url],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except OSError:
            pass  # fall back to webbrowser
    return webbrowser.open(url)


def _linux_launcher() -> str | None:
    """Return the path of the command that opens URLs on Linux.

    ``webbrowser`` also uses ``xdg-open`` on Linux, but lets the browser
    inherit the terminal's stdout and stderr; gcw starts it itself to discard
    them.

    Returns:
        The path of ``wslview`` under WSL, else of ``xdg-open``; ``None``
        outside Linux, when ``$BROWSER`` is set, or when neither command is
        installed, leaving the choice to ``webbrowser``.
    """
    if not sys.platform.startswith("linux") or os.environ.get("BROWSER"):
        return None
    if os.environ.get("WSL_DISTRO_NAME"):
        wslview = shutil.which("wslview")
        if wslview:
            return wslview
    return shutil.which("xdg-open")
