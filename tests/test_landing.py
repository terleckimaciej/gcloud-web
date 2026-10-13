"""Tests for the landing pages: the table of data and the commands generated from it.

Covers what the table must guarantee (shape of every path, no name clashing
with a real service module) and how the generated commands behave (one URL per
entry, no resource arguments, global flags still work).

These tests only check the shape of the paths. Whether a path is the right page
in the real console cannot be tested offline and is verified by hand.
"""

import pytest

from gcw.cli.main import main
from gcw.services import LANDINGS, SERVICES
from gcw.web import browser

CONSOLE = "https://console.cloud.google.com"
ENTRIES = sorted(LANDINGS.items())
NAMES = [name for name, _ in ENTRIES]


@pytest.fixture(autouse=True)
def no_browser(monkeypatch):
    """Make sure a failing test can never open a real browser window."""
    monkeypatch.setattr(browser, "open_url", lambda url: True)


@pytest.fixture(autouse=True)
def gcloud_project(gcloud_dir):
    """Give every test an active gcloud configuration with a project."""
    configurations = gcloud_dir / "configurations"
    configurations.mkdir(parents=True)
    (configurations / "config_default").write_text("[core]\nproject = my-prj\n")


# The table itself


@pytest.mark.parametrize("name,landing", ENTRIES, ids=NAMES)
def test_path_is_a_bare_console_path(name, landing):
    """Paths are relative, without a query string: ``url.py`` adds ``?project=``."""
    assert landing.path, f"{name} has an empty path"
    assert not landing.path.startswith("/"), "paths are relative to the console root"
    assert not landing.path.startswith("http"), "paths are not full URLs"
    assert not set(landing.path) & set("?#"), "query and fragment are built by url.py"
    assert landing.path == landing.path.strip(), "paths must not be padded with whitespace"


@pytest.mark.parametrize("name,landing", ENTRIES, ids=NAMES)
def test_help_is_a_one_line_description(name, landing):
    """``gcw services`` prints one line per service, so the help text is one line."""
    assert landing.help, f"{name} has no help text"
    assert "\n" not in landing.help


def test_landings_do_not_clash_with_service_modules():
    """A name is either a service module or a landing page, never both.

    Both registries become commands of the same parser, so a duplicate would
    silently shadow the richer service command.
    """
    assert not set(LANDINGS) & set(SERVICES)


def test_no_service_shadows_a_built_in_command():
    """Service names must not collide with the CLI's own commands.

    ``add_parser`` would raise at startup, so this test turns a crash of every
    ``gcw`` invocation into one readable failure.
    """
    built_in = {"open", "services"}
    assert not (set(LANDINGS) | set(SERVICES)) & built_in


# The generated commands


@pytest.mark.parametrize("name,landing", ENTRIES, ids=NAMES)
def test_landing_command_prints_its_url(name, landing, capsys):
    """``gcw <service> -n`` prints the console URL of that service's start page."""
    assert main([name, "-n"]) == 0
    assert capsys.readouterr().out == f"{CONSOLE}/{landing.path}?project=my-prj\n"


def test_landing_command_takes_global_flags_after_it(capsys):
    """Global flags work after a landing command, as they do everywhere else."""
    assert main(["bigquery", "-n", "-p", "other-prj"]) == 0
    assert capsys.readouterr().out == f"{CONSOLE}/bigquery?project=other-prj\n"


@pytest.mark.parametrize("extra", [["topics"], ["--tab", "logs"], ["-l", "europe-west1"]])
def test_landing_command_takes_no_resource_arguments(extra, capsys):
    """A landing page has no resources, so kinds, tabs and locations are rejected.

    Resource arguments become available once a service gets its own module with
    routes (then its landing entry is replaced by that module).
    """
    with pytest.raises(SystemExit) as exc:
        main(["pubsub", *extra])

    assert exc.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_landing_commands_are_hidden_from_the_command_list(capsys):
    """``gcw --help`` stays readable: dozens of start pages are not listed there."""
    with pytest.raises(SystemExit):
        main(["--help"])

    help_text = capsys.readouterr().out
    assert "    bigquery" not in help_text
    assert "Many more services have a start page" in help_text


def test_landing_command_has_its_own_help(capsys):
    """``gcw <service> --help`` still describes the hidden command."""
    with pytest.raises(SystemExit):
        main(["bigquery", "--help"])

    assert LANDINGS["bigquery"].help in capsys.readouterr().out
