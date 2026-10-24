"""Shared pytest fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def gcloud_dir(tmp_path, monkeypatch):
    """Isolate every test from the real gcloud setup.

    Points ``$CLOUDSDK_CONFIG`` at an empty temporary directory and removes all
    other ``CLOUDSDK_*`` variables, so no test can read or depend on the
    developer's ``~/.config/gcloud`` or shell environment.

    Returns:
        The temporary gcloud configuration directory (not created yet).
    """
    for variable in list(os.environ):
        if variable.startswith("CLOUDSDK_"):
            monkeypatch.delenv(variable)
    directory = tmp_path / "gcloud"
    monkeypatch.setenv("CLOUDSDK_CONFIG", str(directory))
    return directory


@pytest.fixture(autouse=True)
def cache_dir(tmp_path, monkeypatch):
    """Isolate every test from the real gcw cache.

    Points ``$GCW_CACHE_DIR`` at a temporary directory (not created yet).

    Returns:
        The temporary cache directory.
    """
    directory = tmp_path / "gcw-cache"
    monkeypatch.setenv("GCW_CACHE_DIR", str(directory))
    return directory
