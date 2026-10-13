"""Tests for paging long output: when a pager is used, which one, and with what environment.

No test starts a real pager; ``subprocess.run`` is replaced with a recorder.
"""

import pytest

from gcw.cli import pager

TEXT = "one\ntwo\n"


@pytest.fixture
def run_calls(monkeypatch):
    """Replace ``subprocess.run`` with a recorder.

    Returns:
        The list of ``(command, input, env)`` triples the pager was started with.
    """
    calls = []

    def fake_run(command, *, input, text, env, check):
        """Record the call instead of starting a pager."""
        calls.append((command, input, env))

    monkeypatch.setattr(pager.subprocess, "run", fake_run)
    return calls


@pytest.fixture
def tty(monkeypatch):
    """Run the code under test as if stdout were an interactive terminal."""
    monkeypatch.setattr(pager, "_stdout_is_terminal", lambda: True)


@pytest.fixture(autouse=True)
def no_pager_env(monkeypatch):
    """Start every test from a known environment and on the POSIX branch.

    The pager chooses its branch from ``os.name``, so without pinning it these
    tests would check Windows behaviour on Windows and POSIX behaviour
    everywhere else. The branch is part of what is under test, not of the host:
    ``test_windows_uses_more`` sets ``nt`` for itself.
    """
    for variable in ("GCW_PAGER", "PAGER", "LESS"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(pager.os, "name", "posix")
    monkeypatch.setattr(pager.shutil, "which", lambda name: f"/usr/bin/{name}")


def test_plain_write_when_stdout_is_not_a_terminal(capsys, run_calls):
    """Piped or redirected output is never paged, so `gcw services | grep` works."""
    pager.write_paged(TEXT)

    assert capsys.readouterr().out == TEXT
    assert run_calls == []


def test_missing_final_newline_is_added(capsys):
    """Output always ends with a newline, whether paged or not."""
    pager.write_paged("one")
    assert capsys.readouterr().out == "one\n"


def test_terminal_output_goes_to_less(tty, capsys, run_calls):
    """On a terminal the text is fed to ``less`` instead of stdout."""
    pager.write_paged(TEXT)

    assert capsys.readouterr().out == ""
    command, text, _ = run_calls[0]
    assert command == ["less"]
    assert text == TEXT


def test_less_gets_default_options(tty, run_calls):
    """``less`` quits on short output and keeps it on screen (LESS=FRX)."""
    pager.write_paged(TEXT)
    assert run_calls[0][2]["LESS"] == pager.DEFAULT_LESS


def test_user_less_options_are_kept(tty, monkeypatch, run_calls):
    """A ``LESS`` the user set wins over our default."""
    monkeypatch.setenv("LESS", "S")

    pager.write_paged(TEXT)

    assert run_calls[0][2]["LESS"] == "S"


@pytest.mark.parametrize("variable", ["GCW_PAGER", "PAGER"])
def test_configured_pager_is_used_with_its_arguments(variable, tty, monkeypatch, run_calls):
    """``GCW_PAGER`` and ``PAGER`` may carry arguments and are split like a command line."""
    monkeypatch.setenv(variable, "bat --plain")

    pager.write_paged(TEXT)

    assert run_calls[0][0] == ["bat", "--plain"]


def test_gcw_pager_wins_over_pager(tty, monkeypatch, run_calls):
    """The tool-specific variable takes precedence, as in git and gh."""
    monkeypatch.setenv("PAGER", "bat")
    monkeypatch.setenv("GCW_PAGER", "most")

    pager.write_paged(TEXT)

    assert run_calls[0][0] == ["most"]


@pytest.mark.parametrize("value", ["cat", ""])
def test_pager_can_be_disabled(value, tty, monkeypatch, capsys, run_calls):
    """``PAGER=cat`` or an empty value turns paging off, as in git."""
    monkeypatch.setenv("PAGER", value)

    pager.write_paged(TEXT)

    assert capsys.readouterr().out == TEXT
    assert run_calls == []


def test_missing_pager_falls_back_to_plain_output(tty, monkeypatch, capsys, run_calls):
    """A pager that is not installed is not an error; the text is printed."""
    monkeypatch.setattr(pager.shutil, "which", lambda name: None)

    pager.write_paged(TEXT)

    assert capsys.readouterr().out == TEXT
    assert run_calls == []


def test_pager_that_cannot_start_is_not_an_error(tty, monkeypatch, capsys):
    """If starting the pager fails, the command still succeeds."""

    def explode(*args, **kwargs):
        """Fail the way a missing executable would."""
        raise OSError("boom")

    monkeypatch.setattr(pager.subprocess, "run", explode)

    pager.write_paged(TEXT)

    assert capsys.readouterr().out == ""


def test_windows_uses_more(tty, monkeypatch, run_calls):
    """On Windows the built-in pager is used and PAGER is ignored."""
    monkeypatch.setattr(pager.os, "name", "nt")
    monkeypatch.setenv("PAGER", "bat")

    pager.write_paged(TEXT)

    assert run_calls[0][0] == ["more"]
