"""Tests for the ``list_*`` functions of the service modules.

``urlopen`` is replaced with a fake that answers by URL (without the query),
so each test states which endpoint a listing calls and what it makes of a
sample response. The sample responses follow the shapes documented by each API.
"""

import io
import json
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit

import pytest

from gcw.api import client
from gcw.cache.store import Resource
from gcw.context.gcloud_config import GcloudConfig
from gcw.context.resolve import Context
from gcw.services import SERVICES, lister

PROJECT = "my-prj"


def context(**properties: str) -> Context:
    """Return a context for ``my-prj`` with gcloud properties given as ``section_name=value``."""
    config = GcloudConfig("default", {tuple(key.split("_", 1)): value for key, value in properties.items()})
    return Context(config=config, account="me@example.com", project=PROJECT)


@pytest.fixture
def api(monkeypatch):
    """Fake ``urlopen`` answering from a ``{url: body}`` dict; unknown URLs give 404.

    Returns:
        The dict to fill; a body may be a list of pages for paginated endpoints,
        or an exception to raise.
    """
    responses: dict[str, object] = {}

    def fake_urlopen(request, timeout):
        """Return the next page queued for the request's URL."""
        url = urlsplit(request.full_url)._replace(query="").geturl()
        body = responses.get(url)
        if isinstance(body, list):
            body = body.pop(0)
        if body is None:
            raise HTTPError(url, 404, "Not Found", {}, io.BytesIO(b"{}"))
        if isinstance(body, Exception):
            raise body
        return io.BytesIO(json.dumps(body).encode())

    monkeypatch.setattr(client, "urlopen", fake_urlopen)
    return responses


def listing(service: str, kind: str, ctx: Context | None = None) -> list[Resource]:
    """Run the listing function of ``service``/``kind`` with a dummy token."""
    return lister(SERVICES[service], kind)(ctx or context(), "tok")


def test_run_services_across_regions(api):
    """Cloud Run names carry the region after ``locations``."""
    api["https://run.googleapis.com/v2/projects/my-prj/locations/-/services"] = {
        "services": [
            {"name": "projects/my-prj/locations/europe-west1/services/api"},
            {"name": "projects/my-prj/locations/us-central1/services/worker"},
        ]
    }
    assert listing("run", "services") == [Resource("api", "europe-west1"), Resource("worker", "us-central1")]


def test_run_jobs_follow_pagination(api):
    """Every page of a paginated list is fetched."""
    api["https://run.googleapis.com/v2/projects/my-prj/locations/-/jobs"] = [
        {"jobs": [{"name": "projects/my-prj/locations/eu1/jobs/a"}], "nextPageToken": "t"},
        {"jobs": [{"name": "projects/my-prj/locations/eu1/jobs/b"}]},
    ]
    assert [r.name for r in listing("run", "jobs")] == ["a", "b"]


def test_functions(api):
    """Functions are listed across regions with the v2 API."""
    api["https://cloudfunctions.googleapis.com/v2/projects/my-prj/locations/-/functions"] = {
        "functions": [{"name": "projects/my-prj/locations/eu1/functions/fn"}]
    }
    assert listing("functions", "functions") == [Resource("fn", "eu1")]


def test_compute_instances_from_aggregated_list(api):
    """Zones come from the keys of the aggregated response; empty zones are skipped."""
    api["https://compute.googleapis.com/compute/v1/projects/my-prj/aggregated/instances"] = {
        "items": {
            "zones/eu1-b": {"instances": [{"name": "vm1"}]},
            "zones/eu1-c": {"warning": {"code": "NO_RESULTS_ON_PAGE"}},
        }
    }
    assert listing("compute", "instances") == [Resource("vm1", "eu1-b")]


def test_gke_clusters_keep_zone_or_region(api):
    """Each cluster's own ``location`` is cached, zonal or regional."""
    api["https://container.googleapis.com/v1/projects/my-prj/locations/-/clusters"] = {
        "clusters": [{"name": "prod", "location": "europe-west1"}, {"name": "dev", "location": "europe-west1-b"}]
    }
    assert listing("gke", "clusters") == [Resource("prod", "europe-west1"), Resource("dev", "europe-west1-b")]


def test_sql_instances(api):
    """Cloud SQL instances keep their region for listings."""
    api["https://sqladmin.googleapis.com/v1/projects/my-prj/instances"] = {
        "items": [{"name": "main-db", "region": "europe-west1"}]
    }
    assert listing("sql", "instances") == [Resource("main-db", "europe-west1")]


def test_storage_buckets_lowercase_location(api):
    """Bucket locations are stored in lower case."""
    api["https://storage.googleapis.com/storage/v1/b"] = {"items": [{"name": "data", "location": "EUROPE-WEST1"}]}
    assert listing("storage", "buckets") == [Resource("data", "europe-west1")]


def test_secrets_are_global(api):
    """Secrets have no location; the name is the last path segment."""
    api["https://secretmanager.googleapis.com/v1/projects/my-prj/secrets"] = {
        "secrets": [{"name": "projects/123/secrets/db-password"}]
    }
    assert listing("secrets", "secrets") == [Resource("db-password")]


def test_artifact_repositories_per_location_with_format(api):
    """Repositories are listed per location; a failing location is skipped."""
    base = "https://artifactregistry.googleapis.com/v1/projects/my-prj/locations"
    api[base] = {"locations": [{"locationId": "europe"}, {"locationId": "us"}]}
    api[f"{base}/europe/repositories"] = {
        "repositories": [{"name": "projects/my-prj/locations/europe/repositories/images", "format": "DOCKER"}]
    }
    # No response for "us": the fake answers 404, as a failing location would.

    assert listing("artifacts", "repositories") == [Resource("images", "europe", {"format": "docker"})]


def test_artifact_repositories_fail_when_every_location_fails(api):
    """If no location answers, the error is raised instead of an empty list."""
    api["https://artifactregistry.googleapis.com/v1/projects/my-prj/locations"] = {"locations": [{"locationId": "us"}]}
    with pytest.raises(client.ApiError):
        listing("artifacts", "repositories")


def test_dataproc_uses_configured_region(api):
    """Dataproc lists in ``dataproc/region``; jobs take the ID from ``reference``."""
    base = "https://dataproc.googleapis.com/v1/projects/my-prj"
    api[f"{base}/regions/eu1/clusters"] = {"clusters": [{"clusterName": "etl"}]}
    api[f"{base}/locations/eu1/batches"] = {"batches": [{"name": "projects/my-prj/locations/eu1/batches/b-1"}]}
    api[f"{base}/regions/eu1/jobs"] = {"jobs": [{"reference": {"jobId": "job-1"}}]}
    ctx = context(dataproc_region="eu1")

    assert listing("dataproc", "clusters", ctx) == [Resource("etl", "eu1")]
    assert listing("dataproc", "batches", ctx) == [Resource("b-1", "eu1")]
    assert listing("dataproc", "jobs", ctx) == [Resource("job-1", "eu1")]


def test_dataproc_without_region_lists_nothing(api):
    """Without ``dataproc/region`` or ``compute/region`` no request is made."""
    assert listing("dataproc", "clusters") == []


def test_composer_keeps_airflow_uri(api):
    """Composer environments carry the Airflow UI address in ``extra``."""
    api["https://composer.googleapis.com/v1/projects/my-prj/locations/eu1/environments"] = {
        "environments": [
            {"name": "projects/my-prj/locations/eu1/environments/etl", "config": {"airflowUri": "https://a.example"}},
            {"name": "projects/my-prj/locations/eu1/environments/new", "config": {}},
        ]
    }
    assert listing("composer", "environments", context(compute_region="eu1")) == [
        Resource("etl", "eu1", {"airflow_uri": "https://a.example"}),
        Resource("new", "eu1"),
    ]


def test_iam_service_accounts_by_email(api):
    """Service accounts are cached by email."""
    api["https://iam.googleapis.com/v1/projects/my-prj/serviceAccounts"] = {
        "accounts": [{"email": "sa@my-prj.iam.gserviceaccount.com"}]
    }
    assert listing("iam", "service-accounts") == [Resource("sa@my-prj.iam.gserviceaccount.com")]


@pytest.mark.parametrize(
    ("service", "kind"), [(name, kind) for name, module in SERVICES.items() for kind in module.KINDS]
)
def test_every_kind_has_a_documented_lister(service, kind):
    """Each resource kind has its ``list_<kind>`` function, with a docstring."""
    function = lister(SERVICES[service], kind)
    assert callable(function) and function.__doc__


def test_registry_import_stays_off_the_network_stack():
    """Loading the registry imports no HTTP or TLS code (completion path, ADR-0011)."""
    code = "import sys, gcw.services; print(sorted(m for m in ('ssl', 'urllib.request') if m in sys.modules))"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "[]"
