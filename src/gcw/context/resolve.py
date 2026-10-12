"""Resolve the context a command runs in: the gcloud configuration, account and project.

Combines CLI flags with the gcloud configuration, in the same order gcloud
uses: flag > environment variable > configuration file. Resource locations
(region, zone) will be resolved here as well once the resource cache exists.
"""

from dataclasses import dataclass

from gcw.context.gcloud_config import GcloudConfig, load_gcloud_config


@dataclass(frozen=True)
class Context:
    """Where a command runs.

    Attributes:
        config: The gcloud configuration in use; service modules read
            per-service properties from it (e.g. ``run/region``).
        account: Google account email, or ``None`` if gcloud has none.
        project: Project ID, or ``None`` if neither ``-p`` nor gcloud sets one.
    """

    config: GcloudConfig
    account: str | None
    project: str | None


def resolve_context(project: str | None = None, configuration: str | None = None) -> Context:
    """Build the context from CLI flags and the gcloud configuration.

    Args:
        project: Value of ``-p/--project``; wins over the configuration.
        configuration: Value of ``-c/--configuration``; ``None`` means the active one.

    Returns:
        The resolved context.

    Raises:
        UnknownConfigurationError: ``configuration`` names a configuration that does not exist.
    """
    config = load_gcloud_config(configuration)
    return Context(config=config, account=config.account, project=project or config.project)
