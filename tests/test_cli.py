"""Tests for the top-level CLI: commands, global flags and what happens with the URL.

The browser is always replaced with a fake, so no test opens anything.
"""

import pytest

from gcw.cli.main import main
from gcw.web import browser

DASHBOARD = "https://console.cloud.google.com/home/dashboard"


class UrlList(list):
    """A list that also accepts attributes (used for the ``available`` switch)."""


@pytest.fixture(autouse=True)
def opened(monkeypatch):
    """Replace the real browser with a fake that records URLs and reports success.

    Returns:
        The list of URLs the CLI tried to open; tests may set ``available``
        on it to ``False`` to simulate a missing browser.
    """
    urls = UrlList()
    urls.available = True

    def fake_open_url(url):
        """Record the URL and report whether a browser is "available"."""
        urls.append(url)
        return urls.available

    monkeypatch.setattr(browser, "open_url", fake_open_url)
    return urls


@pytest.fixture(autouse=True)
def gcloud_project(gcloud_dir):
    """Give every test an active gcloud configuration with an account and project."""
    configurations = gcloud_dir / "configurations"
    configurations.mkdir(parents=True)
    (configurations / "config_default").write_text("[core]\naccount = me@example.com\nproject = my-prj\n")


def test_version_prints_installed_version(capsys):
    """``--version`` prints the version from package metadata and exits cleanly."""
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    assert exc.value.code == 0
    assert capsys.readouterr().out == "gcw 0.1.0\n"


def test_no_browser_prints_dashboard_url_without_authuser(capsys, opened):
    """``gcw -n`` prints the shareable dashboard URL and opens nothing."""
    assert main(["-n"]) == 0

    assert capsys.readouterr().out == f"{DASHBOARD}?project=my-prj\n"
    assert opened == []


def test_open_command_uses_given_path(capsys):
    """``gcw -n open PATH`` builds the URL for that path."""
    assert main(["-n", "open", "run/jobs"]) == 0
    assert capsys.readouterr().out == "https://console.cloud.google.com/run/jobs?project=my-prj\n"


def test_project_flag_wins_over_configuration(capsys):
    """``-p`` replaces the project from the gcloud configuration."""
    assert main(["-n", "-p", "other-prj"]) == 0
    assert capsys.readouterr().out == f"{DASHBOARD}?project=other-prj\n"


def test_opens_browser_with_authuser(capsys, opened):
    """Without ``-n`` the URL is opened with the gcloud account as ``authuser``."""
    assert main([]) == 0

    assert opened == [f"{DASHBOARD}?project=my-prj&authuser=me%40example.com"]
    assert capsys.readouterr().out == ""


def test_no_authuser_flag_drops_account(opened):
    """``--no-authuser`` opens the URL without the ``authuser`` parameter."""
    assert main(["--no-authuser"]) == 0
    assert opened == [f"{DASHBOARD}?project=my-prj"]


def test_missing_browser_prints_shareable_url(capsys, opened):
    """If no browser can be launched, the URL is printed instead."""
    opened.available = False

    assert main([]) == 0

    captured = capsys.readouterr()
    assert captured.out == f"{DASHBOARD}?project=my-prj\n"
    assert "no browser available" in captured.err


def test_missing_project_warns_but_still_works(capsys, gcloud_dir):
    """Without any project, a warning is shown and the URL has no ``project``."""
    (gcloud_dir / "configurations" / "config_default").write_text("[core]\naccount = me@example.com\n")

    assert main(["-n"]) == 0

    captured = capsys.readouterr()
    assert captured.out == f"{DASHBOARD}\n"
    assert "no project set" in captured.err


def test_unknown_configuration_fails_with_exit_code_2(capsys):
    """``-c`` with a missing configuration reports the available ones."""
    assert main(["-c", "nope"]) == 2
    assert "available: default" in capsys.readouterr().err
