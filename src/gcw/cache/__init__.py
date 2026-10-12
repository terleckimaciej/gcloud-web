"""Local resource cache: per account, project and resource type, refreshed in the background.

Completion reads only from here and never waits for the network.

Must not depend on ``cli`` or ``services``.
"""
