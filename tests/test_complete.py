"""Tests for TAB completion: ``gcw __complete`` candidates and ``gcw completion`` scripts.

The gcloud configuration and the cache are temporary (conftest); conftest's
``offline`` fixture also guarantees that completion makes no request and
starts no background refresh.
"""

import os
import shutil
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
    store.write(ACCOUNT, "work-prj", "container", "clusters", [Resource("prod", "europe-west1")])


def values(line: str) -> list[str]:
    """Return candidate values for a command line typed as one string (a trailing space means an empty word)."""
    words = line.split(" ")
    return [value for value, _ in candidates(words)]


def test_first_word_offers_services_commands_and_start_pages():
    """After ``gcw`` come services, gcw's own commands (described) and start pages."""
    ordered = candidates(["gcw", ""])
    assert [value for value, _ in ordered[:6]] == ["services", "cache", "open", "env", "completion", ""]
    found = dict(ordered)
    assert found["run"] == ""
    assert found["cache"] == "show or refresh the local resource cache"
    assert "bigquery" in found
    assert values("gcw ru") == ["run"]
    assert "" not in values("gcw c")


def test_kinds_are_plain():
    """Kinds of a service are offered without a description."""
    assert candidates(["gcw", "run", ""]) == [("services", ""), ("jobs", "")]


def test_names_come_from_the_cache_filtered_by_prefix():
    """Resource names are plain and filtered by the typed prefix."""
    assert candidates(["gcw", "run", "services", "api-"]) == [("api-worker", "")]


def test_name_in_several_locations_is_offered_once():
    """The same name in two locations is one candidate; ``-l`` picks the location."""
    store.write(ACCOUNT, "my-prj", "run", "jobs", [Resource("etl", "eu1"), Resource("etl", "us1")])
    assert candidates(["gcw", "run", "jobs", ""]) == [("etl", "")]


def test_single_kind_service_offers_names_right_away():
    """``gcw secrets <TAB>`` lists secrets, since the kind is never typed."""
    assert candidates(["gcw", "secrets", ""]) == [("db-password", "")]


def test_configuration_flag_switches_the_cached_project():
    """``-c work`` completes from the cache of that configuration's project."""
    assert values("gcw -c work container clusters ") == ["prod"]
    assert values("gcw container clusters ") == []


def test_project_flag_switches_the_cached_project():
    """``-p`` after the command works too."""
    assert values("gcw container clusters -p work-prj ") == ["prod"]


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
    assert capsys.readouterr().out == "db-password\t\n"


def test_complete_command_is_silent_on_errors(capsys):
    """A missing configuration yields no candidates and no traceback."""
    assert main(["__complete", "--", "gcw", "-c", "nope", "run", "services", ""]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_completion_prints_the_script(shell, capsys):
    """``gcw completion SHELL`` prints a script that calls ``gcw __complete``."""
    assert main(["completion", shell]) == 0
    assert "gcw __complete --" in capsys.readouterr().out


@pytest.mark.skipif(shutil.which("bash") is None or sys.platform == "win32", reason="needs bash")
@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("api\teu1 · p\n", ["api"]),
        ("api\teu1\napi-worker\teu2\n", ["api         (eu1)", "api-worker  (eu2)"]),
        ("services\tfirst\njobs\t\n", ["services", "jobs"]),
        ("cache\tc\nenv\te\n\t\n" + "".join(f"s{i:02}\n" for i in range(1, 11)),
         ["cache", "env", " ", *(f"s{i:02}" for i in range(1, 11))]),
        ("", []),
    ],
)
def test_bash_script_formats_candidates(output, expected, capsys):
    """bash gets ``name  (description)`` when all have one, a bare name when it inserts it,
    and a gap after a group break so the next group starts a new column (40 columns here)."""
    main(["completion", "bash"])
    script = capsys.readouterr().out
    run = (
        f"{script}\n"
        'gcw() { printf "%s" "$FAKE_OUTPUT"; }\n'
        "COLUMNS=40; COMP_WORDS=(gcw run services ''); COMP_CWORD=3\n"
        '_gcw_complete; for item in "${COMPREPLY[@]}"; do printf "%s\\n" "$item"; done\n'
    )
    result = subprocess.run(["bash", "--norc", "--noprofile", "-c", run], capture_output=True, text=True,
                            check=True, env={**os.environ, "FAKE_OUTPUT": output})
    # bash before 4.4 (macOS ships 3.2) has no `complete -o nosort`, so the script leaves out the gap.
    nosort = subprocess.run(["bash", "--norc", "--noprofile", "-c", "complete -o nosort -F f x"],
                            capture_output=True).returncode == 0
    if not nosort:
        expected = [item for item in expected if item.strip()]
    assert result.stdout.splitlines() == expected


def test_complete_path_stays_off_the_network_stack(gcloud_dir, cache_dir):
    """Answering a TAB imports no HTTP or TLS code (ADR-0011)."""
    code = (
        "import sys; from gcw.cli.main import main; main(['__complete', '--', 'gcw', 'run', 'services', ''])\n"
        "print(sorted(m for m in ('ssl', 'urllib.request') if m in sys.modules), file=sys.stderr)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stderr.strip() == "[]"
    assert result.stdout.startswith("api\t")
