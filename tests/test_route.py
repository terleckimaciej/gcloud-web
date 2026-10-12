"""Tests for filling console route templates."""

import pytest

from gcw.web.route import Route, RouteError

RUN_SERVICE = Route(
    path="run/detail/{location}/{name}/{tab}",
    list_path="run",
    tabs=("metrics", "logs", "revisions"),
    location_property=("run", "region"),
)


def test_fills_name_location_and_default_tab():
    """Without ``tab``, the first allowed tab is used."""
    assert RUN_SERVICE.build("api", location="europe-west1") == "run/detail/europe-west1/api/metrics"


def test_uses_requested_tab():
    """An allowed tab replaces the default."""
    assert RUN_SERVICE.build("api", location="europe-west1", tab="logs") == "run/detail/europe-west1/api/logs"


def test_rejects_unknown_tab():
    """A tab outside ``tabs`` fails and lists the allowed ones."""
    with pytest.raises(RouteError, match="available: metrics, logs, revisions"):
        RUN_SERVICE.build("api", location="europe-west1", tab="nope")


def test_missing_location_explains_flag_and_gcloud_property():
    """A missing location names the flag and the gcloud property to set."""
    with pytest.raises(RouteError) as exc:
        RUN_SERVICE.build("api")

    assert str(exc.value) == "missing region (use -l/--location or `gcloud config set run/region`)"


def test_missing_zone_uses_location_label_without_property():
    """The message uses ``location_label`` and omits the gcloud hint without a property."""
    route = Route(path="compute/instancesDetail/zones/{location}/instances/{name}", location_label="zone")

    with pytest.raises(RouteError) as exc:
        route.build("vm-1")

    assert str(exc.value) == "missing zone (use -l/--location)"


def test_location_not_required_when_template_has_none():
    """Only placeholders present in the template are required."""
    route = Route(path="security/secret-manager/secret/{name}/versions")
    assert route.build("db-password") == "security/secret-manager/secret/db-password/versions"


def test_project_placeholder():
    """``{project}`` is filled when present and required when missing."""
    route = Route(path="artifacts/docker/{project}/{location}/{name}")

    assert route.build("images", location="europe", project="my-prj") == "artifacts/docker/my-prj/europe/images"
    with pytest.raises(RouteError, match="missing project"):
        route.build("images", location="europe")
