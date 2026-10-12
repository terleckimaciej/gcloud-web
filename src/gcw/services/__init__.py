"""GCP services: one flat module per service, holding its console routes and resource listing.

Each module declares its routes as data and exposes ``list_*`` functions that
fetch resources for the cache. This package also builds the service registry
used by the CLI and completion.

May depend on ``api``, ``cache``, ``context`` and ``web``. Service modules must
keep top-level imports light, because completion loads the registry; import
HTTP code lazily inside ``list_*`` functions.
"""
