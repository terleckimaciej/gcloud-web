"""Tests for ``gcw env``: switching the gcloud configuration of the current shell only."""

import pytest

from gcw.cli.complete import candidates
from gcw.cli.main import main


@pytest.fixture(autouse=True)
def configurations(gcloud_dir):
    """Two gcloud configurations: ``default`` and ``work``."""
    directory = gcloud_dir / "configurations"
    directory.mkdir(parents=True)
    (directory / "config_default").write_text("[core]\nproject = my-prj\n")
    (directory / "config_work").write_text("[core]\nproject = work-prj\n")


def test_prints_export_for_bash_and_zsh(capsys):
    """The default output is a POSIX ``export`` meant for ``eval``."""
    assert main(["env", "work"]) == 0
    assert capsys.readouterr().out == "export CLOUDSDK_ACTIVE_CONFIG_NAME=work\n"


def test_prints_set_for_fish(capsys):
    """``--shell fish`` prints fish syntax."""
    assert main(["env", "work", "--shell", "fish"]) == 0
    assert capsys.readouterr().out == "set -gx CLOUDSDK_ACTIVE_CONFIG_NAME work\n"


def test_unknown_configuration_fails_with_choices(capsys):
    """A missing configuration prints nothing to evaluate and exits 2."""
    assert main(["env", "nope"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "available: default, work" in captured.err


def test_unusual_names_are_quoted(capsys, gcloud_dir):
    """A name with shell metacharacters is quoted, so ``eval`` cannot run it."""
    (gcloud_dir / "configurations" / "config_a;b").write_text("[core]\n")
    assert main(["env", "a;b"]) == 0
    assert capsys.readouterr().out == "export CLOUDSDK_ACTIVE_CONFIG_NAME='a;b'\n"


def test_completion_offers_configurations_and_shells():
    """``gcw env <TAB>`` lists configurations; ``--shell <TAB>`` lists shells."""
    assert candidates(["gcw", "env", ""]) == [("default", "my-prj"), ("work", "work-prj")]
    assert [value for value, _ in candidates(["gcw", "env", "work", "--shell", ""])] == ["bash", "zsh", "fish"]
