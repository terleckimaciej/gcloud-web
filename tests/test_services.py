"""Tests for the service modules: every route's URL, and single-kind service syntax.

Each route is exercised through the CLI with ``-n``, so the tests cover the
template, the parser generated from the registry and the final URL together.
"""

import pytest

from gcw.cli.main import main
from gcw.services import SERVICES, is_single_kind

CONSOLE = "https://console.cloud.google.com"


@pytest.fixture(autouse=True)
def gcloud_project(gcloud_dir):
    """Give every test an active gcloud configuration with a project."""
    configurations = gcloud_dir / "configurations"
    configurations.mkdir(parents=True)
    (configurations / "config_default").write_text("[core]\nproject = my-prj\n")


@pytest.mark.parametrize(
    ("argv", "path"),
    [
        (["functions", "fn", "-l", "eu1"], "functions/details/eu1/fn?project=my-prj"),
        (["compute", "instances", "vm", "-z", "eu1-b"],
         "compute/instancesDetail/zones/eu1-b/instances/vm?project=my-prj"),
        (["container", "clusters", "c1", "-l", "eu1"], "kubernetes/clusters/details/eu1/c1/details?project=my-prj"),
        (["container", "clusters", "c1", "-l", "eu1", "--tab", "nodes"],
         "kubernetes/clusters/details/eu1/c1/nodes?project=my-prj"),
        (["sql", "instances", "db"], "sql/instances/db/overview?project=my-prj"),
        (["sql", "instances", "db", "--tab", "backups"], "sql/instances/db/backups?project=my-prj"),
        (["storage", "buckets", "b"], "storage/browser/b?project=my-prj"),
        (["storage", "buckets", "b/exports/2026"], "storage/browser/b/exports/2026?project=my-prj"),
        (["storage", "buckets", "gs://b"], "storage/browser/b?project=my-prj"),
        (["storage", "buckets", "gs://b/exports/2026"], "storage/browser/b/exports/2026?project=my-prj"),
        (["secrets", "pw"], "security/secret-manager/secret/pw/versions?project=my-prj"),
        (["secrets", "pw", "--tab", "overview"], "security/secret-manager/secret/pw/overview?project=my-prj"),
        (["artifacts", "repositories", "r", "-l", "eu"], "artifacts/docker/my-prj/eu/r?project=my-prj"),
        (["dataproc", "clusters", "c", "-l", "eu1"], "dataproc/clusters/c/monitoring?region=eu1&project=my-prj"),
        (["dataproc", "batches", "b", "-l", "eu1"], "dataproc/batches/eu1/b?project=my-prj"),
        (["dataproc", "jobs", "j", "-l", "eu1"], "dataproc/jobs/j?region=eu1&project=my-prj"),
        (["composer", "environments", "etl", "-l", "eu1"],
         "composer/environments/detail/eu1/etl/monitoring?project=my-prj"),
        (["iam", "service-accounts", "sa@my-prj.iam.gserviceaccount.com"],
         "iam-admin/serviceaccounts/details/sa@my-prj.iam.gserviceaccount.com?project=my-prj"),
    ],
)
def test_resource_url(argv, path, capsys):
    """Every route builds the expected console URL for one resource."""
    assert main([*argv, "-n"]) == 0
    assert capsys.readouterr().out == f"{CONSOLE}/{path}\n"


@pytest.mark.parametrize(
    ("argv", "path"),
    [
        (["functions"], "functions/list"),
        (["secrets"], "security/secret-manager"),
        (["iam"], "iam-admin/iam"),
        (["iam", "service-accounts"], "iam-admin/serviceaccounts"),
        (["container", "clusters"], "kubernetes/list/overview"),
    ],
)
def test_overview_and_list_url(argv, path, capsys):
    """A service alone opens its overview; with a kind, its list."""
    assert main([*argv, "-n"]) == 0
    assert capsys.readouterr().out == f"{CONSOLE}/{path}?project=my-prj\n"


def test_zone_defaults_to_compute_zone(capsys, gcloud_dir):
    """Compute instances take their zone from ``compute/zone``."""
    (gcloud_dir / "configurations" / "config_default").write_text(
        "[core]\nproject = my-prj\n[compute]\nzone = eu1-c\n"
    )

    assert main(["compute", "instances", "vm", "-n"]) == 0
    assert "/zones/eu1-c/instances/vm?" in capsys.readouterr().out


def test_missing_zone_is_called_a_zone(capsys):
    """The error for a zonal route says "zone" and names the gcloud property."""
    assert main(["compute", "instances", "vm", "-n"]) == 2
    assert "missing zone (use -l/--location or `gcloud config set compute/zone`)" in capsys.readouterr().err


def test_single_kind_service_rejects_kind_word_as_extra_argument(capsys):
    """``gcw secrets secrets pw`` is two names, which the parser rejects."""
    with pytest.raises(SystemExit):
        main(["secrets", "secrets", "pw"])
    assert "unrecognized arguments: pw" in capsys.readouterr().err


def test_single_kind_service_shows_name_in_listing(capsys):
    """``gcw services`` shows ``NAME`` instead of the implied kind."""
    assert main(["services"]) == 0
    assert "    NAME          tabs: versions, overview, permissions, logs" in capsys.readouterr().out


@pytest.mark.parametrize("module", SERVICES.values(), ids=list(SERVICES))
def test_service_module_contract(module):
    """Every service module declares the attributes the registry relies on."""
    assert module.__doc__
    assert module.NAME and module.HELP and module.LANDING and module.KINDS
    if is_single_kind(module):
        assert len(module.KINDS) == 1
