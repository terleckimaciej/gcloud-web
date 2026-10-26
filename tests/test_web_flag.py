"""Tests for ``gcw web-flag``: the opt-in ``gcloud … --web`` shell function (ADR-0024).

The function is run in a real shell, with a fake ``gcloud`` program on PATH and
``gcw`` replaced by a shell function, so nothing real is called.
"""

import os
import shutil
import subprocess
import sys

import pytest

from gcw.cli.main import main

# How to run a command string in each shell, and how to define the fake gcw there.
SHELLS = {
    "bash": (["bash", "--norc", "--noprofile", "-c"], 'gcw() { echo "gcw $*"; }'),
    "zsh": (["zsh", "-f", "-c"], 'gcw() { echo "gcw $*"; }'),
    "fish": (["fish", "--no-config", "-c"], "function gcw; echo gcw $argv; end"),
}


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_prints_the_function(shell, capsys):
    """Each shell gets a `gcloud` function that sends --web lines to `gcw gcloud`."""
    assert main(["web-flag", shell]) == 0
    script = capsys.readouterr().out
    assert "gcw gcloud" in script
    assert "command gcloud" in script


def test_help_explains_install(capsys):
    """`gcw web-flag --help` names the --install commands and the lines they add."""
    with pytest.raises(SystemExit):
        main(["web-flag", "--help"])
    out = capsys.readouterr().out
    assert out.startswith("usage: gcw web-flag")
    assert "gcw web-flag bash --install" in out
    assert 'eval "$(gcw web-flag bash)"' in out
    assert "~/.config/fish/config.fish" in out


def test_subcommand_usage_starts_with_the_command(capsys):
    """Subcommand help shows `gcw run …`, not the top-level usage in front of it."""
    with pytest.raises(SystemExit):
        main(["run", "--help"])
    assert capsys.readouterr().out.startswith("usage: gcw run")


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A fake home directory with no shell configuration in it."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("ZDOTDIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    return tmp_path


def test_install_appends_the_line_once(home, capsys):
    """--install adds the eval line to ~/.bashrc and does not add it a second time."""
    (home / ".bashrc").write_text("alias ll='ls -l'")
    assert main(["web-flag", "bash", "--install"]) == 0
    assert main(["web-flag", "bash", "--install"]) == 0
    assert (home / ".bashrc").read_text() == "alias ll='ls -l'\neval \"$(gcw web-flag bash)\"\n"
    out = capsys.readouterr().out
    assert "added `eval \"$(gcw web-flag bash)\"`" in out
    assert "already enabled" in out


def test_install_creates_fish_config(home):
    """fish's config file and its directories are created when missing."""
    assert main(["web-flag", "fish", "--install"]) == 0
    assert (home / ".config" / "fish" / "config.fish").read_text() == "gcw web-flag fish | source\n"


def test_install_follows_zdotdir(home, monkeypatch):
    """zsh reads ~/.zshrc from $ZDOTDIR when it is set."""
    monkeypatch.setenv("ZDOTDIR", str(home / "zsh"))
    assert main(["completion", "zsh", "--install"]) == 0
    assert (home / "zsh" / ".zshrc").read_text() == 'eval "$(gcw completion zsh)"\n'


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX shells and a fake gcloud script")
@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_web_goes_to_gcw_and_the_rest_to_gcloud(shell, tmp_path, capsys):
    """With --web the line goes to `gcw gcloud`; without it, to the real gcloud."""
    command, fake_gcw = SHELLS[shell]
    if shutil.which(command[0]) is None:
        pytest.skip(f"{shell} is not installed")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_gcloud = bin_dir / "gcloud"
    fake_gcloud.write_text('#!/bin/sh\necho "real gcloud $*"\n')
    fake_gcloud.chmod(0o755)

    main(["web-flag", shell])
    script = capsys.readouterr().out
    run = f"{script}\n{fake_gcw}\ngcloud run jobs list\ngcloud run jobs describe nightly --web\n"
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run([*command, run], capture_output=True, text=True, check=True, env=env)
    assert result.stdout.splitlines() == [
        "real gcloud run jobs list",
        "gcw gcloud run jobs describe nightly --web",
    ]
