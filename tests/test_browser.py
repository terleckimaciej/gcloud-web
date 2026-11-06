"""Tests for opening a URL: which launcher is used and how it is started.

No test starts a real browser; ``subprocess.Popen`` and ``webbrowser.open`` are
replaced with recorders.
"""

import subprocess

import pytest

from gcw.web import browser

URL = "https://console.cloud.google.com/run?project=demo"


@pytest.fixture
def popen_calls(monkeypatch):
    """Replace ``subprocess.Popen`` with a recorder.

    Returns:
        The list of ``(command, options)`` pairs a launcher was started with.
    """
    calls = []

    def fake_popen(command, **options):
        """Record the call instead of starting a process."""
        calls.append((command, options))

    monkeypatch.setattr(browser.subprocess, "Popen", fake_popen)
    return calls


@pytest.fixture
def webbrowser_calls(monkeypatch):
    """Replace ``webbrowser.open`` with a recorder that reports success.

    Returns:
        The list of URLs passed to ``webbrowser.open``.
    """
    calls = []
    monkeypatch.setattr(browser.webbrowser, "open", lambda url: calls.append(url) or True)
    return calls


@pytest.fixture(autouse=True)
def linux_env(monkeypatch):
    """Start every test on Linux, outside WSL, with every launcher installed.

    The launcher depends on the platform and the environment, so without
    pinning them these tests would check whatever machine runs them. Tests that
    need another platform or a missing command set it for themselves.
    """
    for variable in ("BROWSER", "WSL_DISTRO_NAME"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(browser.sys, "platform", "linux")
    monkeypatch.setattr(browser.shutil, "which", lambda name: f"/usr/bin/{name}")


def test_linux_starts_xdg_open_detached(popen_calls, webbrowser_calls):
    """On Linux the browser's output is discarded and it runs in its own session."""
    assert browser.open_url(URL) is True

    command, options = popen_calls[0]
    assert command == ["/usr/bin/xdg-open", URL]
    assert options["stdin"] == options["stdout"] == options["stderr"] == subprocess.DEVNULL
    assert options["start_new_session"] is True
    assert webbrowser_calls == []


def test_wsl_uses_wslview(monkeypatch, popen_calls):
    """Under WSL the Windows browser is opened through ``wslview``."""
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")

    browser.open_url(URL)

    assert popen_calls[0][0] == ["/usr/bin/wslview", URL]


def test_wsl_without_wslview_falls_back_to_xdg_open(monkeypatch, popen_calls):
    """WSL without ``wslview`` installed still tries ``xdg-open``."""
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")
    monkeypatch.setattr(browser.shutil, "which", lambda name: None if name == "wslview" else f"/usr/bin/{name}")

    browser.open_url(URL)

    assert popen_calls[0][0] == ["/usr/bin/xdg-open", URL]


def test_browser_variable_is_left_to_webbrowser(monkeypatch, popen_calls, webbrowser_calls):
    """A ``$BROWSER`` the user set is honoured by ``webbrowser``, not overridden."""
    monkeypatch.setenv("BROWSER", "firefox")

    assert browser.open_url(URL) is True

    assert popen_calls == []
    assert webbrowser_calls == [URL]


@pytest.mark.parametrize("platform", ["darwin", "win32"])
def test_other_platforms_use_webbrowser(platform, monkeypatch, popen_calls, webbrowser_calls):
    """macOS and Windows hand the URL to the system, which starts the browser detached."""
    monkeypatch.setattr(browser.sys, "platform", platform)

    browser.open_url(URL)

    assert popen_calls == []
    assert webbrowser_calls == [URL]


def test_no_launcher_falls_back_to_webbrowser(monkeypatch, popen_calls):
    """Without ``xdg-open`` the result is ``webbrowser``'s, so over SSH the CLI prints the URL."""
    monkeypatch.setattr(browser.shutil, "which", lambda name: None)
    monkeypatch.setattr(browser.webbrowser, "open", lambda url: False)

    assert browser.open_url(URL) is False
    assert popen_calls == []


def test_launcher_that_cannot_start_falls_back_to_webbrowser(monkeypatch, webbrowser_calls):
    """If starting ``xdg-open`` fails, ``webbrowser`` gets its chance."""

    def explode(*args, **kwargs):
        """Fail the way a broken executable would."""
        raise OSError("boom")

    monkeypatch.setattr(browser.subprocess, "Popen", explode)

    assert browser.open_url(URL) is True
    assert webbrowser_calls == [URL]