"""Tests for reading the gcloud configuration from its files."""

import pytest

from gcw.context.gcloud_config import (
    UnknownConfigurationError,
    active_configuration_name,
    config_dir,
    list_configurations,
    load_gcloud_config,
)


def write_config(directory, name, content):
    """Create ``configurations/config_<name>`` with the given INI content."""
    configurations = directory / "configurations"
    configurations.mkdir(parents=True, exist_ok=True)
    (configurations / f"config_{name}").write_text(content)


def set_active(directory, name):
    """Write the ``active_config`` file."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "active_config").write_text(f"{name}\n")


def test_config_dir_comes_from_cloudsdk_config(gcloud_dir):
    """``$CLOUDSDK_CONFIG`` selects the configuration directory."""
    assert config_dir() == gcloud_dir


def test_active_configuration_is_read_from_file(gcloud_dir):
    """The ``active_config`` file names the active configuration."""
    set_active(gcloud_dir, "work")
    assert active_configuration_name() == "work"


def test_active_configuration_env_beats_file(gcloud_dir, monkeypatch):
    """``$CLOUDSDK_ACTIVE_CONFIG_NAME`` overrides the ``active_config`` file."""
    set_active(gcloud_dir, "work")
    monkeypatch.setenv("CLOUDSDK_ACTIVE_CONFIG_NAME", "private")
    assert active_configuration_name() == "private"


def test_active_configuration_defaults_to_default(gcloud_dir):
    """Without env or file, the active configuration is ``default``."""
    assert active_configuration_name() == "default"


def test_loads_properties_of_active_configuration(gcloud_dir):
    """Properties from all sections of the active configuration are readable."""
    set_active(gcloud_dir, "work")
    write_config(gcloud_dir, "work", "[core]\naccount = me@example.com\nproject = work-prj\n[run]\nregion = europe-west1\n")

    config = load_gcloud_config()

    assert config.name == "work"
    assert config.account == "me@example.com"
    assert config.project == "work-prj"
    assert config.get("run", "region") == "europe-west1"
    assert config.get("compute", "zone") is None


def test_env_property_beats_file(gcloud_dir, monkeypatch):
    """``$CLOUDSDK_<SECTION>_<NAME>`` overrides the value from the file."""
    write_config(gcloud_dir, "default", "[core]\nproject = from-file\n")
    monkeypatch.setenv("CLOUDSDK_CORE_PROJECT", "from-env")
    assert load_gcloud_config().project == "from-env"


def test_env_only_property_is_visible(gcloud_dir, monkeypatch):
    """A property set only in the environment is still returned."""
    write_config(gcloud_dir, "default", "[core]\nproject = p\n")
    monkeypatch.setenv("CLOUDSDK_RUN_REGION", "us-central1")
    assert load_gcloud_config().get("run", "region") == "us-central1"


def test_empty_value_counts_as_unset(gcloud_dir):
    """An empty value in the file is reported as ``None``."""
    write_config(gcloud_dir, "default", "[core]\nproject =\n")
    assert load_gcloud_config().project is None


def test_percent_sign_is_not_interpolated(gcloud_dir):
    """Values containing ``%`` are read verbatim."""
    write_config(gcloud_dir, "default", "[core]\ncustom = 100%\n")
    assert load_gcloud_config().get("core", "custom") == "100%"


def test_explicit_name_ignores_active_configuration(gcloud_dir):
    """A configuration requested by name (``-c``) wins over the active one."""
    set_active(gcloud_dir, "work")
    write_config(gcloud_dir, "work", "[core]\nproject = work-prj\n")
    write_config(gcloud_dir, "private", "[core]\nproject = private-prj\n")

    config = load_gcloud_config("private")

    assert config.name == "private"
    assert config.project == "private-prj"


def test_unknown_explicit_name_raises_with_available_names(gcloud_dir):
    """Requesting a missing configuration fails and lists the existing ones."""
    write_config(gcloud_dir, "work", "")
    write_config(gcloud_dir, "default", "")

    with pytest.raises(UnknownConfigurationError) as exc:
        load_gcloud_config("nope")

    assert exc.value.available == ["default", "work"]


def test_missing_gcloud_gives_empty_active_configuration(gcloud_dir):
    """Without any gcloud files, loading the active configuration does not fail."""
    config = load_gcloud_config()

    assert config.name == "default"
    assert config.project is None
    assert config.account is None


def test_list_configurations_sorted_and_ignores_other_files(gcloud_dir):
    """Only ``config_*`` files are listed, sorted by name."""
    write_config(gcloud_dir, "work", "")
    write_config(gcloud_dir, "default", "")
    (gcloud_dir / "configurations" / "notes.txt").write_text("")

    assert list_configurations() == ["default", "work"]


def test_list_configurations_empty_without_gcloud(gcloud_dir):
    """Without a configurations directory, the list is empty."""
    assert list_configurations() == []
