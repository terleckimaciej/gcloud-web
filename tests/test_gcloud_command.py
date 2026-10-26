"""Tests for ``gcw gcloud …``: a gcloud command line run as the gcw command it names (ADR-0020).

Every test uses ``-n``, so URLs are printed instead of opened; the gcloud
configuration and the cache are temporary (conftest).
"""

import pytest

from gcw.cache import store
from gcw.cache.store import Resource
from gcw.cli.main import main

ACCOUNT = "me@example.com"
CONSOLE = "https://console.cloud.google.com"


@pytest.fixture(autouse=True)
def gcloud_project(gcloud_dir):
    """An active configuration with an account and project ``my-prj``."""
    configurations = gcloud_dir / "configurations"
    configurations.mkdir(parents=True)
    (configurations / "config_default").write_text(f"[core]\naccount = {ACCOUNT}\nproject = my-prj\n")


def test_opens_the_same_page_as_the_gcw_command(capsys):
    """The gcloud spelling prints the URL of the matching gcw command, and names that command."""
    assert main("gcloud run jobs describe nightly --region europe-west1 --web -n".split()) == 0
    translated = capsys.readouterr()
    assert main("run jobs nightly --region europe-west1 -n".split()) == 0
    assert translated.out == capsys.readouterr().out
    assert translated.out == f"{CONSOLE}/run/jobs/details/europe-west1/nightly/executions?project=my-prj\n"
    assert "same as: gcw run jobs nightly --region europe-west1 -n" in translated.err


def test_location_comes_from_the_cache(capsys):
    """Without --region the job's location is found as in gcw."""
    store.write(ACCOUNT, "my-prj", "run", "jobs", [Resource("nightly", "europe-west1")])
    assert main("gcloud run jobs describe nightly -n".split()) == 0
    assert "/run/jobs/details/europe-west1/nightly/" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("gcloud", "path"),
    [
        ("gcloud run jobs list --region europe-west1 -n", "run/jobs?project=my-prj"),
        ("gcloud --web -n", "home/dashboard?project=my-prj"),
        ("gcloud storage ls gs://bucket/exports -n", "storage/browser/bucket/exports?project=my-prj"),
    ],
)
def test_lists_dashboard_and_buckets(gcloud, path, capsys):
    """Lists take no location, a bare `gcloud` is the dashboard, gs:// names open the folder."""
    assert main(gcloud.split()) == 0
    assert capsys.readouterr().out == f"{CONSOLE}/{path}\n"


def test_a_command_that_changes_resources_fails(capsys):
    """`update` is not translated; the error names the nearest page and the exit code is 2."""
    assert main("gcloud run jobs update nightly --memory 1Gi --web".split()) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "gcw: `gcloud run jobs update` is not a command gcw can open" in captured.err
    assert "Nearest page: gcw run jobs" in captured.err


def test_gcw_flags_before_gcloud_are_rejected(capsys):
    """`gcw -n gcloud …` is an error instead of silently dropping -n."""
    with pytest.raises(SystemExit) as exc:
        main("-n gcloud run jobs list".split())
    assert exc.value.code == 2
    assert "gcw flags go at the end" in capsys.readouterr().err


def test_help(capsys):
    """`gcw gcloud --help` describes the command instead of translating `--help`."""
    with pytest.raises(SystemExit) as exc:
        main(["gcloud", "--help"])
    assert exc.value.code == 0
    assert "gcloud read command" in capsys.readouterr().out
