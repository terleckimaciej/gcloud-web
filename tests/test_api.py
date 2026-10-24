"""Tests for the API layer: access tokens from gcloud and the REST client.

gcloud and the network are always faked: ``shutil.which`` and
``subprocess.run`` in ``gcw.api.auth``, ``urlopen`` in ``gcw.api.client``.
"""

import io
import json
import subprocess
from urllib.error import HTTPError, URLError

import pytest

from gcw.api import auth, client


@pytest.fixture(autouse=True)
def no_cached_tokens(monkeypatch):
    """Start every test without tokens remembered by earlier tests."""
    monkeypatch.setattr(auth, "_tokens", {})


@pytest.fixture
def gcloud(monkeypatch):
    """Fake a gcloud on PATH whose ``print-access-token`` result tests can set.

    Returns:
        A dict with ``result`` (the ``CompletedProcess`` to return) and
        ``calls`` (the commands that were run).
    """
    fake = {"result": subprocess.CompletedProcess([], 0, stdout="tok-123\n", stderr=""), "calls": []}
    monkeypatch.setattr(auth.shutil, "which", lambda name: "/usr/bin/gcloud")

    def fake_run(command, **kwargs):
        """Record the command and return the configured result."""
        fake["calls"].append(command)
        return fake["result"]

    monkeypatch.setattr(auth.subprocess, "run", fake_run)
    return fake


# auth


def test_token_comes_from_print_access_token_for_the_account(gcloud):
    """The token is gcloud's output, requested for the given account."""
    assert auth.access_token("me@example.com") == "tok-123"
    assert gcloud["calls"] == [
        ["/usr/bin/gcloud", "auth", "print-access-token", "--verbosity=error", "--account", "me@example.com"]
    ]


def test_token_is_fetched_once_per_account(gcloud):
    """Repeated calls for the same account reuse the token."""
    auth.access_token("me@example.com")
    auth.access_token("me@example.com")
    auth.access_token("other@example.com")
    assert len(gcloud["calls"]) == 2


def test_without_account_gcloud_picks_its_own(gcloud):
    """No ``--account`` is passed when the configuration has no account."""
    auth.access_token(None)
    assert "--account" not in gcloud["calls"][0]


def test_missing_gcloud_explains_how_to_install(monkeypatch):
    """Without gcloud on PATH the error says so."""
    monkeypatch.setattr(auth.shutil, "which", lambda name: None)
    with pytest.raises(auth.AuthError, match="gcloud not found on PATH"):
        auth.access_token("me@example.com")


def test_failed_command_points_to_gcloud_auth_login(gcloud):
    """A failing command reports gcloud's last error line and the fix."""
    gcloud["result"] = subprocess.CompletedProcess(
        [], 1, stdout="", stderr="WARNING: x\nERROR: Reauthentication required.\n"
    )
    with pytest.raises(auth.AuthError) as error:
        auth.access_token("me@example.com")
    assert str(error.value) == (
        "cannot get an access token for me@example.com (ERROR: Reauthentication required.); run `gcloud auth login`"
    )


def test_timeout_is_an_auth_error(monkeypatch):
    """A hanging gcloud becomes an ``AuthError``, not a traceback."""
    monkeypatch.setattr(auth.shutil, "which", lambda name: "gcloud")

    def hang(command, **kwargs):
        """Simulate a command that never finishes."""
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(auth.subprocess, "run", hang)
    with pytest.raises(auth.AuthError, match="timed out"):
        auth.access_token(None)


# client


class FakeResponse(io.BytesIO):
    """A response body usable as a context manager, like ``urlopen``'s result."""


@pytest.fixture
def http(monkeypatch):
    """Fake ``urlopen`` with a queue of JSON pages or exceptions.

    Returns:
        A dict with ``responses`` (bodies as dicts, or exceptions to raise, in
        order) and ``requests`` (the ``Request`` objects that were sent).
    """
    fake = {"responses": [], "requests": []}

    def fake_urlopen(request, timeout):
        """Record the request and return or raise the next queued response."""
        fake["requests"].append(request)
        response = fake["responses"].pop(0)
        if isinstance(response, Exception):
            raise response
        return FakeResponse(json.dumps(response).encode())

    monkeypatch.setattr(client, "urlopen", fake_urlopen)
    return fake


def test_get_json_sends_bearer_token_and_params(http):
    """The token goes in the ``Authorization`` header, params in the query."""
    http["responses"] = [{"ok": True}]

    assert client.get_json("https://x.googleapis.com/v1/things", "tok", {"filter": "a b"}) == {"ok": True}

    request = http["requests"][0]
    assert request.full_url == "https://x.googleapis.com/v1/things?filter=a+b"
    assert request.get_header("Authorization") == "Bearer tok"


def test_http_error_carries_status_and_google_message(http):
    """A Google error body becomes an ``ApiError`` with its message and status."""
    body = io.BytesIO(json.dumps({"error": {"message": "API not enabled"}}).encode())
    http["responses"] = [HTTPError("u", 403, "Forbidden", {}, body)]

    with pytest.raises(client.ApiError) as error:
        client.get_json("https://x.googleapis.com/v1/things", "tok")
    assert error.value.status == 403
    assert str(error.value) == "HTTP 403: API not enabled"


def test_network_error_has_no_status(http):
    """No response at all becomes an ``ApiError`` without a status."""
    http["responses"] = [URLError("no route to host")]

    with pytest.raises(client.ApiError) as error:
        client.get_json("https://x.googleapis.com/v1/things", "tok")
    assert error.value.status is None
    assert "no route to host" in str(error.value)


def test_list_all_follows_page_tokens(http):
    """Items from every page are joined; the page token is sent back."""
    http["responses"] = [
        {"things": [{"name": "a"}], "nextPageToken": "p2"},
        {"things": [{"name": "b"}]},
    ]

    items = client.list_all("https://x.googleapis.com/v1/things", "tok", "things", {"pageSize": "1"})

    assert [item["name"] for item in items] == ["a", "b"]
    assert http["requests"][1].full_url.endswith("?pageSize=1&pageToken=p2")


def test_list_all_handles_empty_list(http):
    """An endpoint with no resources omits the items field entirely."""
    http["responses"] = [{}]
    assert client.list_all("https://x.googleapis.com/v1/things", "tok", "things") == []


def test_run_parallel_keeps_results_and_errors_apart():
    """A failing task returns its exception without affecting the others."""

    def fail():
        """Raise like a disabled API would."""
        raise client.ApiError("HTTP 403: disabled", status=403)

    results = client.run_parallel({"ok": lambda: [1, 2], "bad": fail})

    assert results["ok"] == [1, 2]
    assert isinstance(results["bad"], client.ApiError)
