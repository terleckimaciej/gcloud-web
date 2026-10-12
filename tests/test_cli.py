"""Tests for the top-level CLI entry point."""

import pytest

from gcw.cli.main import main


def test_version_prints_installed_version(capsys):
    """``--version`` prints the version from package metadata and exits cleanly."""
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    assert exc.value.code == 0
    assert capsys.readouterr().out == "gcw 0.1.0\n"


def test_no_arguments_prints_usage(capsys):
    """Running without arguments succeeds and shows usage."""
    assert main([]) == 0
    assert "usage: gcw" in capsys.readouterr().out
