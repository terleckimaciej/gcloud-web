"""Tests for building console URLs."""

from gcw.web.url import console_url


def test_adds_project():
    """The project becomes the ``project`` query parameter."""
    assert console_url("run", project="my-prj") == "https://console.cloud.google.com/run?project=my-prj"


def test_adds_authuser_when_account_given():
    """An account becomes the ``authuser`` parameter, after ``project``."""
    assert (
        console_url("run", project="my-prj", account="me@example.com")
        == "https://console.cloud.google.com/run?project=my-prj&authuser=me%40example.com"
    )


def test_omits_missing_values():
    """Parameters without a value are left out entirely."""
    assert console_url("home/dashboard") == "https://console.cloud.google.com/home/dashboard"


def test_leading_slash_is_optional():
    """``/run`` and ``run`` produce the same URL."""
    assert console_url("/run", project="p") == console_url("run", project="p")


def test_keeps_existing_query_parameters():
    """A path with its own query keeps it and gets the context appended."""
    assert (
        console_url("dataproc/clusters/c1/monitoring?region=europe-west1", project="p")
        == "https://console.cloud.google.com/dataproc/clusters/c1/monitoring?region=europe-west1&project=p"
    )


def test_does_not_override_project_already_in_path():
    """A ``project`` already present in the path wins over the context."""
    assert console_url("run?project=from-path", project="from-context").endswith("run?project=from-path")


def test_keeps_matrix_parameters():
    """Semicolon parameters used by Logs Explorer stay in the path."""
    url = console_url("logs/query;query=severity%3DERROR", project="p")
    assert url == "https://console.cloud.google.com/logs/query;query=severity%3DERROR?project=p"
