"""Tests for TAB completion: ``gcw __complete`` candidates and ``gcw completion`` scripts.

The gcloud configuration and the cache are temporary (conftest); conftest's
``offline`` fixture also guarantees that completion makes no request and
starts no background refresh.
"""

import subprocess
import sys

import pytest

from gcw.cache import store
from gcw.cache.store import Resource
from gcw.cli.complete import candidates
from gcw.cli.main import main

ACCOUNT = "me@example.com"


@pytest.fixture(autouse=True)
def gcloud_setup(gcloud_dir):
    """Two configurations, ``default`` (active, ``my-prj``) and ``work`` (``work-prj``), and a small cache."""
    configurations = gcloud_dir / "configurations"
    configurations.mkdir(parents=True)
    (configurations / "config_default").write_text(f"[core]\naccount = {ACCOUNT}\nproject = my-prj\n")
    (configurations / "config_work").write_text(f"[core]\naccount = {ACCOUNT}\nproject = work-prj\n")
    store.write(ACCOUNT, "my-prj", "run", "services", [Resource("api", "eu1"), Resource("api-worker", "eu2")])
    store.write(ACCOUNT, "my-prj", "secrets", "secrets", [Resource("db-password")])
    store.write(ACCOUNT, "work-prj", "gke", "clusters", [Resource("prod", "europe-west1")])


def values(line: str) -> list[str]:
    """Return candidate values for a command line typed as one string (a trailing space means an empty word)."""
    words = line.split(" ")
    return [value for value, _ in candidates(words)]


def test_first_word_offers_services_commands_and_start_pages():
    """After ``gcw`` come services with routes, built-in commands and start pages."""
    found = dict(candidates(["gcw", ""]))
    assert found["run"] == "Cloud Run services and jobs"
    assert found["cache"] == "show or refresh the local resource cache"
    assert "bigquery" in found
    assert values("gcw ru") == ["run"]


def test_kinds_show_how_many_are_cached():
    """Kinds of a service are offered with the number of cached resources."""
    assert candidates(["gcw", "run", ""]) == [("services", "2 cached"), ("jobs", "")]


def test_names_come_from_the_cache_with_location_and_project():
    """Resource names are described as ``location · project``, filtered by prefix."""
    assert candidates(["gcw", "run", "services", "api-"]) == [("api-worker", "eu2 · my-prj")]


def test_single_kind_service_offers_names_right_away():
    """``gcw secrets <TAB>`` lists secrets, since the kind is never typed."""
    assert candidates(["gcw", "secrets", ""]) == [("db-password", "my-prj")]


def test_configuration_flag_switches_the_cached_project():
    """``-c work`` completes from the cache of that configuration's project."""
    assert values("gcw -c work gke clusters ") == ["prod"]
    assert values("gcw gke clusters ") == []


def test_project_flag_switches_the_cached_project():
    """``-p`` after the command works too."""
    assert values("gcw gke clusters -p work-prj ") == ["prod"]


def test_configuration_values_are_described_by_project():
    """``-c <TAB>`` lists gcloud configurations with their projects."""
    assert candidates(["gcw", "-c", ""]) == [("default", "my-prj"), ("work", "work-prj")]


def test_project_values_include_cached_and_configured():
    """``-p <TAB>`` lists cached projects and marks the configured one."""
    assert candidates(["gcw", "-p", ""]) == [("my-prj", "configured"), ("work-prj", "cached")]


def test_tab_values_mark_the_default():
    """``--tab <TAB>`` lists the route's tabs; the first is the default."""
    found = candidates(["gcw", "run", "services", "api", "--tab", ""])
    assert found[0] == ("metrics", "default")
    assert ("logs", "") in found


def test_location_values_come_from_the_cache():
    """``-l <TAB>`` lists the locations of cached resources of that kind."""
    assert values("gcw run services api -l ") == ["eu1", "eu2"]


def test_flags_depend_on_the_command():
    """Resource flags appear for service commands; ``--airflow`` only for Composer."""
    assert "--tab" in values("gcw run services api --")
    assert "--airflow" not in values("gcw run services api --")
    assert "--airflow" in values("gcw composer environments etl --")
    assert values("gcw --no-b") == ["--no-browser"]


def test_cache_actions_services_and_kinds():
    """``gcw cache`` completes its actions, then a service, then its kinds."""
    assert values("gcw cache ") == ["list", "refresh"]
    assert "sql" in values("gcw cache refresh ")
    assert values("gcw cache ls run ") == ["services", "jobs"]


def test_completion_offers_shells():
    """``gcw completion <TAB>`` lists the supported shells."""
    assert values("gcw completion ") == ["bash", "zsh", "fish"]


def test_complete_command_prints_tab_separated_lines(capsys):
    """``gcw __complete -- WORDS`` prints ``value<TAB>description`` lines."""
    assert main(["__complete", "--", "gcw", "secrets", ""]) == 0
    assert capsys.readouterr().out == "db-password\tmy-prj\n"


def test_complete_command_is_silent_on_errors(capsys):
    """A missing configuration yields no candidates and no traceback."""
    assert main(["__complete", "--", "gcw", "-c", "nope", "run", "services", ""]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_completion_prints_the_script(shell, capsys):
    """``gcw completion SHELL`` prints a script that calls ``gcw __complete``."""
    assert main(["completion", shell]) == 0
    assert "gcw __complete --" in capsys.readouterr().out


def test_complete_path_stays_off_the_network_stack(gcloud_dir, cache_dir):
    """Answering a TAB imports no HTTP or TLS code (ADR-0011)."""
    code = (
        "import sys; from gcw.cli.main import main; main(['__complete', '--', 'gcw', 'run', 'services', ''])\n"
        "print(sorted(m for m in ('ssl', 'urllib.request') if m in sys.modules), file=sys.stderr)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stderr.strip() == "[]"
    assert result.stdout.startswith("api\t")
