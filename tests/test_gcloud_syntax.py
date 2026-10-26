"""Tests for translating gcloud command lines into gcw arguments (ADR-0020)."""

import pytest

from gcw.cli.gcloud_syntax import TranslationError, translate


@pytest.mark.parametrize(
    ("gcloud", "gcw"),
    [
        # The table in issue #18.
        ("run jobs describe nightly --region europe-west1 --web", "run jobs nightly --region europe-west1"),
        ("run jobs describe nightly --web", "run jobs nightly"),
        ("run jobs list --web", "run jobs"),
        ("run jobs describe --web", "run jobs"),
        ("run jobs --web", "run jobs"),
        ("run --web", "run"),
        ("--web", ""),
        # Single-kind services skip the kind.
        ("secrets describe db-password", "secrets db-password"),
        ("secrets get-iam-policy db-password", "secrets db-password"),
        ("functions describe fn --region europe-west1", "functions fn --region europe-west1"),
        ("functions list", "functions"),
        # Other services and flag names.
        ("container clusters describe prod --zone europe-west1-b", "container clusters prod --zone europe-west1-b"),
        ("artifacts repositories describe images --location europe", "artifacts repositories images --location europe"),
        ("iam service-accounts describe sa@p.iam.gserviceaccount.com",
         "iam service-accounts sa@p.iam.gserviceaccount.com"),
        # Storage: the group-level `ls` and gs:// names, stripped later by the route.
        ("storage ls gs://bucket/exports", "storage buckets gs://bucket/exports"),
        ("storage ls", "storage buckets"),
        ("storage buckets describe gs://bucket", "storage buckets gs://bucket"),
        # Start pages open whatever follows.
        ("pubsub topics list --web", "pubsub"),
    ],
)
def test_read_commands_translate(gcloud, gcw):
    """Read commands drop the verb and keep service, kind, name and location."""
    assert translate(gcloud.split()) == gcw.split()


def test_flags_with_equals_and_unknown_flags():
    """``--flag=value`` works; unknown flags and the words after them are ignored."""
    words = "sql instances describe db --format json --project=p --configuration work --quiet".split()
    assert translate(words) == ["sql", "instances", "db", "--project", "p", "--configuration", "work"]


def test_gcw_flags_pass_through():
    """``-n`` and ``--no-authuser`` are gcw's own and reach gcw."""
    assert translate("run jobs describe nightly --web -n --no-authuser".split()) == [
        "run", "jobs", "nightly", "-n", "--no-authuser",
    ]


@pytest.mark.parametrize(
    "gcloud",
    ["run jobs list --region europe-west1", "functions list --region europe-west1", "pubsub topics list --region x"],
)
def test_location_is_dropped_without_a_name(gcloud):
    """List and start pages take no location, so gcw would reject it there."""
    assert "--region" not in translate(gcloud.split())


def test_project_is_kept_on_list_pages():
    """``--project`` applies to every page, not only to named resources."""
    assert translate("run jobs list --project p".split()) == ["run", "jobs", "--project", "p"]


@pytest.mark.parametrize(
    ("gcloud", "command", "nearest"),
    [
        ("run jobs update nightly --memory 1Gi", "gcloud run jobs update", "gcw run jobs"),
        ("run jobs executions list", "gcloud run jobs executions", "gcw run jobs"),
        ("secrets versions access latest --secret pw", "gcloud secrets versions", "gcw secrets"),
        ("run deploy api --source .", "gcloud run deploy", "gcw run"),
        ("compute ssh vm --zone europe-west1-b", "gcloud compute ssh", "gcw compute"),
        ("nosuch things list", "gcloud nosuch", "gcw"),
    ],
)
def test_other_commands_fail_with_the_nearest_page(gcloud, command, nearest):
    """Commands that change resources, sub-groups and unknown words are errors, never guesses."""
    with pytest.raises(TranslationError) as error:
        translate(gcloud.split())
    message = str(error.value)
    assert f"`{command}` is not a command gcw can open" in message
    assert message.endswith(f"Nearest page: {nearest}")
