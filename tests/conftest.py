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


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Keep every test away from gcloud, the network and background processes.

    Access tokens fail as if gcloud were missing, any HTTP request fails the
    test, and background refreshes are recorded instead of started. Tests of
    those pieces restore the real functions themselves.

    Returns:
        The ``(service, kind)`` pairs passed to ``spawn_background``, in order.
    """
    from gcw.api import auth, client
    from gcw.cache import refresh

    def no_gcloud(account):
        """Fail like a machine without gcloud."""
        raise auth.AuthError("gcloud is not available in tests")

    def no_network(request, timeout):
        """Fail the test on any request that was not faked."""
        raise AssertionError(f"unexpected network request: {request.full_url}")

    spawned = []

    def record_spawn(context, service=None, kind=None):
        """Record the background refresh instead of starting a process."""
        spawned.append((service, kind))
        return True

    monkeypatch.setattr(auth, "_token_from_gcloud", no_gcloud)
    monkeypatch.setattr(client, "urlopen", no_network)
    monkeypatch.setattr(refresh, "spawn_background", record_spawn)
    return spawned
