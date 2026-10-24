"""Tests for resolving named resources: locations from the cache, live lookups and links.

Commands run through the CLI with ``-n``. The access token and listing
functions are faked; conftest's ``offline`` fixture records background
refreshes and fails on any real request.
"""

import json

import pytest

from gcw.api import auth
from gcw.api.client import ApiError
from gcw.cache import store
from gcw.cache.store import Resource
from gcw.cli.main import main
from gcw.services import composer, run, sql

ACCOUNT = "me@example.com"
CONSOLE = "https://console.cloud.google.com"


@pytest.fixture(autouse=True)
def gcloud_project(gcloud_dir):
    """Active configuration with an account, a project and ``run/region = us1``."""
    configurations = gcloud_dir / "configurations"
    configurations.mkdir(parents=True)
    (configurations / "config_default").write_text(
        f"[core]\naccount = {ACCOUNT}\nproject = my-prj\n[run]\nregion = us1\n"
    )


@pytest.fixture
def token(monkeypatch):
    """Make ``access_token`` return a fixed token without running gcloud."""
    monkeypatch.setattr(auth, "access_token", lambda account=None: "tok")


def cache(service: str, kind: str, *resources: Resource) -> None:
    """Put resources into the cache of ``my-prj``."""
    store.write(ACCOUNT, "my-prj", service, kind, list(resources))


def url(argv: list[str], capsys) -> str:
    """Run a command with ``-n`` and return the printed URL."""
    assert main([*argv, "-n"]) == 0
    return capsys.readouterr().out.strip()


# locations


def test_location_comes_from_cache_without_flag(capsys):
    """A cached service opens in its own region, not the configured one."""
    cache("run", "jobs", Resource("menu-courier", "europe-central2"))
    assert url(["run", "jobs", "menu-courier"], capsys) == (
        f"{CONSOLE}/run/jobs/details/europe-central2/menu-courier/executions?project=my-prj"
    )


def test_flag_wins_over_cache(capsys):
    """``-l`` is always used as given."""
    cache("run", "services", Resource("api", "eu1"))
    assert "/run/detail/eu2/api/" in url(["run", "services", "api", "-l", "eu2"], capsys)


def test_environment_override_wins_over_cache(capsys, monkeypatch):
    """``$CLOUDSDK_RUN_REGION`` is an explicit choice, so it beats the cache."""
    cache("run", "services", Resource("api", "eu1"))
    monkeypatch.setenv("CLOUDSDK_RUN_REGION", "eu3")
    assert "/run/detail/eu3/api/" in url(["run", "services", "api"], capsys)


def test_configured_region_breaks_a_tie(capsys):
    """The same name in two regions: the configured region wins if it is one of them."""
    cache("run", "services", Resource("api", "eu1"), Resource("api", "us1"))
    assert "/run/detail/us1/api/" in url(["run", "services", "api"], capsys)


def test_ambiguous_name_asks_for_a_location(capsys):
    """The same name in two regions, neither configured: exit 2 with the choices."""
    cache("run", "services", Resource("api", "eu1"), Resource("api", "eu2"))
    assert main(["run", "services", "api", "-n"]) == 2
    assert "api exists in several locations (eu1, eu2); choose one with -l" in capsys.readouterr().err


def test_unknown_name_is_looked_up_live_and_cached(capsys, monkeypatch, token):
    """A name missing from the cache triggers one live listing, which is then cached."""
    cache("run", "services", Resource("old", "eu1"))
    monkeypatch.setattr(run, "list_services", lambda context, token: [Resource("new", "eu2")])

    assert "/run/detail/eu2/new/" in url(["run", "services", "new"], capsys)
    assert store.read(ACCOUNT, "my-prj", "run", "services").resources == [Resource("new", "eu2")]


def test_failed_lookup_warns_and_uses_configuration(capsys):
    """Without credentials the configured region is used, with a warning."""
    assert main(["run", "services", "api", "-n"]) == 0

    captured = capsys.readouterr()
    assert "/run/detail/us1/api/" in captured.out
    assert "warning: cannot look up services: gcloud is not available in tests" in captured.err


def test_disabled_api_warns_and_uses_configuration(capsys, monkeypatch, token):
    """An API error during the lookup also falls back to the configuration."""

    def disabled(context, token):
        """Fail like a disabled API."""
        raise ApiError("HTTP 403: disabled", status=403)

    monkeypatch.setattr(run, "list_services", disabled)

    assert main(["run", "services", "api", "-n"]) == 0
    assert "warning: cannot look up run services: HTTP 403: disabled" in capsys.readouterr().err


def test_stale_entry_is_used_and_refreshed_in_background(capsys, offline):
    """An old entry still gives the location; a background refresh of that kind starts."""
    path = store.entry_path(ACCOUNT, "my-prj", "run", "services")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"fetched_at": 0, "resources": [{"name": "api", "location": "eu1"}]}))

    assert "/run/detail/eu1/api/" in url(["run", "services", "api"], capsys)
    assert offline == [("run", "services")]


def test_no_lookup_when_route_needs_no_location(capsys, monkeypatch):
    """Cloud SQL pages need no region, so nothing is listed."""

    def must_not_run(context, token):
        """Fail if the lookup happens."""
        raise AssertionError("lookup should not run")

    monkeypatch.setattr(sql, "list_instances", must_not_run)
    assert url(["sql", "instances", "db"], capsys) == f"{CONSOLE}/sql/instances/db/overview?project=my-prj"


# links


def test_airflow_opens_cached_ui(capsys, opened):
    """``--airflow`` opens the cached Airflow address as is, without project or authuser."""
    cache("composer", "environments", Resource("etl", "eu1", {"airflow_uri": "https://abc.composer.example"}))

    assert url(["composer", "environments", "etl", "--airflow"], capsys) == "https://abc.composer.example"
    assert main(["composer", "environments", "etl", "--airflow"]) == 0
    assert opened == ["https://abc.composer.example"]


def test_airflow_for_unknown_environment_fails(capsys, monkeypatch, token):
    """Without the address, even after a live lookup, the command fails with a hint."""
    monkeypatch.setattr(composer, "list_environments", lambda context, token: [])
    assert main(["composer", "environments", "etl", "--airflow", "-n"]) == 2
    assert "no address known for etl; check the name or run `gcw cache refresh composer`" in capsys.readouterr().err


def test_airflow_requires_a_name(capsys):
    """``--airflow`` without an environment is a parser error."""
    with pytest.raises(SystemExit):
        main(["composer", "environments", "--airflow"])
    assert "--airflow requires a resource NAME" in capsys.readouterr().err


@pytest.fixture
def opened(monkeypatch):
    """Replace the browser with a fake that records URLs."""
    from gcw.web import browser

    urls = []
    monkeypatch.setattr(browser, "open_url", lambda target: urls.append(target) or True)
    return urls
