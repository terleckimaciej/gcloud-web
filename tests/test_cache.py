"""Tests for the resource cache: storage, refreshing, the background process, ``gcw refresh`` and ``gcw ls``.

The cache directory is a temporary one (``GCW_CACHE_DIR`` from conftest). The
access token and listing functions are faked, so nothing touches the network.
"""

import json
import sys
import time

import pytest

from gcw.api import auth
from gcw.api.client import ApiError
from gcw.cache import refresh, store
from gcw.cache.store import Resource
from gcw.cli.main import main
from gcw.context.gcloud_config import GcloudConfig
from gcw.context.resolve import Context
from gcw.services import run

ACCOUNT = "me@example.com"


@pytest.fixture(autouse=True)
def gcloud_project(gcloud_dir):
    """Give every test an active gcloud configuration with an account and project."""
    configurations = gcloud_dir / "configurations"
    configurations.mkdir(parents=True)
    (configurations / "config_default").write_text(f"[core]\naccount = {ACCOUNT}\nproject = my-prj\n")


@pytest.fixture
def token(monkeypatch):
    """Make ``access_token`` return a fixed token without running gcloud."""
    monkeypatch.setattr(auth, "access_token", lambda account=None: "tok")


def context(project: str = "my-prj") -> Context:
    """Return a context for the default configuration."""
    return Context(config=GcloudConfig("default"), account=ACCOUNT, project=project)


# store


def test_write_then_read_round_trip(cache_dir):
    """Written resources come back unchanged, from the documented path."""
    resources = [Resource("api", "eu1"), Resource("etl", "eu1", {"airflow_uri": "https://a"})]
    store.write(ACCOUNT, "my-prj", "run", "services", resources)

    entry = store.read(ACCOUNT, "my-prj", "run", "services")

    assert entry.resources == resources
    assert (cache_dir / ACCOUNT / "my-prj" / "run.services.json").is_file()
    assert not entry.is_stale()


def test_write_leaves_no_temporary_files(cache_dir):
    """The atomic write removes its temporary file."""
    store.write(ACCOUNT, "my-prj", "run", "services", [])
    assert [p.name for p in (cache_dir / ACCOUNT / "my-prj").iterdir()] == ["run.services.json"]


def test_missing_and_corrupt_entries_read_as_none(cache_dir):
    """No file, or an unreadable one, means nothing is cached."""
    assert store.read(ACCOUNT, "my-prj", "run", "services") is None

    path = store.entry_path(ACCOUNT, "my-prj", "run", "services")
    path.parent.mkdir(parents=True)
    path.write_text("{not json")
    assert store.read(ACCOUNT, "my-prj", "run", "services") is None


def test_entry_becomes_stale_after_soft_ttl():
    """An entry older than 24 hours is stale but still usable."""
    entry = store.CacheEntry([Resource("api")], fetched_at=1000.0)
    assert not entry.is_stale(now=1000.0 + store.SOFT_TTL_SECONDS)
    assert entry.is_stale(now=1001.0 + store.SOFT_TTL_SECONDS)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX default")
def test_cache_dir_default_follows_xdg(monkeypatch, tmp_path):
    """Without ``GCW_CACHE_DIR`` the cache lives in ``$XDG_CACHE_HOME/gcw``."""
    monkeypatch.delenv("GCW_CACHE_DIR")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert store.cache_dir() == tmp_path / "xdg" / "gcw"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows default")
def test_cache_dir_default_on_windows_is_localappdata(monkeypatch, tmp_path):
    """Without ``GCW_CACHE_DIR`` the cache lives in ``%LOCALAPPDATA%\\gcw`` (ADR-0013)."""
    monkeypatch.delenv("GCW_CACHE_DIR")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert store.cache_dir() == tmp_path / "local" / "gcw"


def test_cached_projects_lists_project_directories():
    """Projects with any cached kind are listed for the account."""
    store.write(ACCOUNT, "b-prj", "run", "jobs", [])
    store.write(ACCOUNT, "a-prj", "run", "jobs", [])
    assert store.cached_projects(ACCOUNT) == ["a-prj", "b-prj"]
    assert store.cached_projects("nobody@example.com") == []


# refresh


def test_refresh_caches_successes_and_reports_failures(token):
    """A failing kind is reported and does not prevent caching the others."""

    def disabled(context, token):
        """Fail like an API that is disabled in the project."""
        raise ApiError("HTTP 403: disabled", status=403)

    results = refresh.refresh(context(), {
        ("run", "services"): lambda context, token: [Resource("api", "eu1")],
        ("run", "jobs"): disabled,
    })

    assert results[("run", "services")] == 1
    assert isinstance(results[("run", "jobs")], ApiError)
    assert store.read(ACCOUNT, "my-prj", "run", "services").resources == [Resource("api", "eu1")]
    assert store.read(ACCOUNT, "my-prj", "run", "jobs") is None


def test_spawn_background_starts_one_detached_refresh(monkeypatch):
    """The child runs ``gcw refresh --background`` for the same context; a second spawn waits for the lock."""
    started = []
    monkeypatch.setattr(refresh.subprocess, "Popen", lambda command, **options: started.append((command, options)))

    assert refresh.spawn_background(context(), "run", "services") is True
    assert refresh.spawn_background(context(), "run", "services") is False

    command, options = started[0]
    assert len(started) == 1
    assert command[1:] == ["-m", "gcw", "refresh", "--background", "-c", "default", "-p", "my-prj", "run", "services"]
    assert options["stdout"] is refresh.subprocess.DEVNULL
    assert refresh.lock_path(ACCOUNT, "my-prj").exists()


def test_old_lock_does_not_block_a_new_refresh(monkeypatch):
    """A lock left by a process that died long ago is ignored."""
    monkeypatch.setattr(refresh.subprocess, "Popen", lambda command, **options: None)
    lock = refresh.lock_path(ACCOUNT, "my-prj")
    lock.parent.mkdir(parents=True)
    lock.touch()
    old = time.time() - refresh.LOCK_SECONDS - 1
    refresh.os.utime(lock, (old, old))

    assert refresh.spawn_background(context()) is True


# gcw refresh / gcw ls


@pytest.fixture
def fake_run_listing(monkeypatch, token):
    """Replace the Cloud Run listing functions with fixed results."""
    monkeypatch.setattr(run, "list_services", lambda context, token: [Resource("api", "eu1"), Resource("web", "us1")])
    monkeypatch.setattr(run, "list_jobs", lambda context, token: [Resource("nightly", "eu1")])


def test_refresh_command_reports_counts(capsys, fake_run_listing):
    """``gcw refresh run`` caches both kinds and prints how many of each."""
    assert main(["refresh", "run"]) == 0

    out = capsys.readouterr().out
    assert "Refreshed project my-prj:" in out
    assert "run services  2" in out and "run jobs      1" in out


def test_refresh_command_reports_skipped_kind_in_one_line(capsys, monkeypatch, token):
    """A failing kind shows the first sentence of its error; all failing means exit 1."""

    def disabled(context, token):
        """Fail with a long, multi-sentence API message."""
        raise ApiError("HTTP 403: Cloud Run Admin API has not been used. Enable it by visiting x.")

    monkeypatch.setattr(run, "list_services", disabled)

    assert main(["refresh", "run", "services"]) == 1
    assert "run services  skipped: HTTP 403: Cloud Run Admin API has not been used." in capsys.readouterr().out


def test_refresh_command_without_credentials(capsys, monkeypatch):
    """No token: a readable error and exit code 1."""

    def no_token(account=None):
        """Fail like gcloud without a session."""
        raise auth.AuthError("cannot get an access token; run `gcloud auth login`")

    monkeypatch.setattr(auth, "access_token", no_token)

    assert main(["refresh", "run"]) == 1
    assert "gcloud auth login" in capsys.readouterr().err


def test_background_refresh_is_silent_and_releases_lock(capsys, fake_run_listing):
    """``--background`` prints nothing and removes the lock when done."""
    lock = refresh.lock_path(ACCOUNT, "my-prj")
    lock.parent.mkdir(parents=True)
    lock.touch()

    assert main(["refresh", "--background", "run"]) == 0

    assert capsys.readouterr().out == ""
    assert not lock.exists()


def test_unknown_kind_filter_is_rejected(capsys):
    """A kind that the service does not have is a parser error."""
    with pytest.raises(SystemExit):
        main(["ls", "run", "buckets"])
    assert "unknown kind 'buckets' of run (available: services, jobs)" in capsys.readouterr().err


def test_ls_prints_cached_table(capsys, fake_run_listing):
    """``gcw ls`` shows name, location and kind of every cached resource."""
    main(["refresh", "run"])
    capsys.readouterr()

    assert main(["ls"]) == 0

    assert capsys.readouterr().out.splitlines() == [
        "NAME     LOCATION  KIND",
        "api      eu1       run services",
        "web      us1       run services",
        "nightly  eu1       run jobs",
    ]


def test_ls_with_empty_cache_suggests_refresh(capsys):
    """Nothing cached: exit 1 and a hint."""
    assert main(["ls"]) == 1
    assert "run `gcw refresh`" in capsys.readouterr().err


def test_ls_warns_about_stale_entries(capsys):
    """Entries older than the soft TTL are shown with a warning."""
    path = store.entry_path(ACCOUNT, "my-prj", "sql", "instances")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"fetched_at": 0, "resources": [{"name": "db", "location": "eu1"}]}))

    assert main(["ls", "sql"]) == 0
    captured = capsys.readouterr()
    assert "db" in captured.out
    assert "older than 24 hours" in captured.err
