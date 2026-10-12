"""Execution context: the active gcloud configuration, account, project, region and zone.

Reads gcloud's configuration files directly (no subprocess) and resolves values
in order: CLI flag > environment > config file > cache > live lookup.

Must not depend on ``cli`` or ``services``.
"""
