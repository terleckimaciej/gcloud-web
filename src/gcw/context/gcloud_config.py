"""Read the gcloud CLI configuration (configurations and their properties) directly from its files.

Mirrors how gcloud itself resolves values, so gcw always agrees with gcloud
about the current account and project:

1. which configuration is active: ``$CLOUDSDK_ACTIVE_CONFIG_NAME``, then the
   ``active_config`` file, then ``"default"``;
2. property values: ``$CLOUDSDK_<SECTION>_<NAME>``, then the configuration file.

CLI flags (``-c``, ``-p``) are applied on top of this by ``gcw.context.resolve``.
This module only reads; it never writes gcloud's files.

Layout of the gcloud configuration directory (``$CLOUDSDK_CONFIG`` or
``~/.config/gcloud``)::

    active_config                   name of the active configuration
    configurations/config_<name>    INI file, e.g. "[core]" with "project = my-project"
"""

import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIGURATION = "default"


class UnknownConfigurationError(LookupError):
    """Raised when an explicitly requested gcloud configuration does not exist."""

    def __init__(self, name: str, available: list[str]):
        """Store the missing name and the configurations that do exist."""
        self.name = name
        self.available = available
        listed = ", ".join(available) or "none"
        super().__init__(f"gcloud configuration {name!r} not found (available: {listed})")


@dataclass(frozen=True)
class GcloudConfig:
    """Properties of one gcloud configuration.

    Any property is available through ``get(section, name)``. Only ``account``
    and ``project`` get shortcuts, because every command needs them and they are
    unambiguous; regions are per service (``run/region``, ``compute/zone``, ...),
    so service modules ask for the one they need.

    Environment overrides are applied when a value is read, so a property that
    exists only as ``$CLOUDSDK_<SECTION>_<NAME>`` is visible too.

    Attributes:
        name: Configuration name, e.g. ``"default"``.
        properties: Values from the configuration file, keyed by ``(section, name)``.
    """

    name: str
    properties: dict[tuple[str, str], str] = field(default_factory=dict)

    def get(self, section: str, name: str) -> str | None:
        """Return a property value, preferring ``$CLOUDSDK_<SECTION>_<NAME>`` over the file.

        Args:
            section: Property section, e.g. ``"core"`` or ``"run"``.
            name: Property name within the section, e.g. ``"project"``.

        Returns:
            The value, or ``None`` when the property is unset or empty.
        """
        from_env = os.environ.get(f"CLOUDSDK_{section}_{name}".upper())
        value = from_env if from_env is not None else self.properties.get((section, name))
        return value or None

    @property
    def account(self) -> str | None:
        """The ``core/account`` property: the Google account gcloud acts as."""
        return self.get("core", "account")

    @property
    def project(self) -> str | None:
        """The ``core/project`` property: the default project ID."""
        return self.get("core", "project")


def config_dir() -> Path:
    """Return the gcloud configuration directory.

    ``$CLOUDSDK_CONFIG`` wins; otherwise ``%APPDATA%\\gcloud`` on Windows and
    ``~/.config/gcloud`` elsewhere, as in gcloud.
    """
    override = os.environ.get("CLOUDSDK_CONFIG")
    if override:
        return Path(override)
    if os.name == "nt" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "gcloud"
    return Path.home() / ".config" / "gcloud"


def active_configuration_name(directory: Path | None = None) -> str:
    """Return the name of the active configuration.

    Order: ``$CLOUDSDK_ACTIVE_CONFIG_NAME``, the ``active_config`` file, ``"default"``.

    Args:
        directory: gcloud configuration directory; defaults to ``config_dir()``.
    """
    from_env = os.environ.get("CLOUDSDK_ACTIVE_CONFIG_NAME")
    if from_env:
        return from_env
    try:
        name = ((directory or config_dir()) / "active_config").read_text(encoding="utf-8").strip()
    except OSError:
        name = ""
    return name or DEFAULT_CONFIGURATION


def list_configurations(directory: Path | None = None) -> list[str]:
    """Return the names of all gcloud configurations, sorted.

    Args:
        directory: gcloud configuration directory; defaults to ``config_dir()``.

    Returns:
        Configuration names, or an empty list when there are none (or no gcloud).
    """
    configurations = (directory or config_dir()) / "configurations"
    try:
        entries = list(configurations.iterdir())
    except OSError:
        return []
    return sorted(
        entry.name.removeprefix("config_")
        for entry in entries
        if entry.is_file() and entry.name.startswith("config_")
    )


def load_gcloud_config(name: str | None = None, directory: Path | None = None) -> GcloudConfig:
    """Load a gcloud configuration by name, or the active one.

    Args:
        name: Configuration to load (the ``-c`` flag); ``None`` means the active one.
        directory: gcloud configuration directory; defaults to ``config_dir()``.

    Returns:
        The configuration. If the *active* configuration has no file (e.g. gcloud
        is not installed), an empty configuration is returned instead of failing.

    Raises:
        UnknownConfigurationError: ``name`` was given and no such configuration exists.
    """
    directory = directory or config_dir()
    explicit = name is not None
    name = name if explicit else active_configuration_name(directory)

    # gcloud values may contain "%", so interpolation must be off.
    parser = configparser.ConfigParser(interpolation=None)
    path = directory / "configurations" / f"config_{name}"
    try:
        with path.open(encoding="utf-8") as config_file:
            parser.read_file(config_file)
    except FileNotFoundError:
        if explicit:
            raise UnknownConfigurationError(name, list_configurations(directory)) from None
        return GcloudConfig(name)

    properties = {
        (section, key): value for section in parser.sections() for key, value in parser.items(section)
    }
    return GcloudConfig(name, properties)
