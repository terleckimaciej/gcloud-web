"""GCP services: one flat module per service, holding its console routes and resource listing.

Each module declares its routes as data and exposes ``list_*`` functions that
fetch resources for the cache. This package also builds the service registry
used by the CLI and completion.

May depend on ``api``, ``cache``, ``context`` and ``web``. Service modules must
keep top-level imports light, because completion loads the registry; import
HTTP code lazily inside ``list_*`` functions.

Every service module defines:

    NAME      command name, e.g. ``"run"`` for ``gcw run``
    HELP      one-line description shown in ``gcw --help``
    LANDING   console path opened by ``gcw <NAME>`` alone
    KINDS     resource kinds, ``{"services": Route(...), ...}``

and may define:

    SINGLE_KIND   ``True`` when the service has exactly one kind that the user
                  never types (``gcw secrets NAME``, ADR-0012); default ``False``

To add a service, create its module and append it to the tuple below.

Services that only have a start page live in ``landing`` instead, as entries of
``LANDINGS``. The two registries are disjoint: a name is either a full service
module or a landing page, never both (checked by the tests).
"""

from types import ModuleType

from gcw.services import (
    artifacts,
    composer,
    compute,
    dataproc,
    functions,
    gke,
    iam,
    run,
    secrets,
    sql,
    storage,
)
from gcw.services.landing import LANDINGS, Landing

SERVICES: dict[str, ModuleType] = {
    module.NAME: module
    for module in (run, functions, compute, gke, sql, storage, secrets, artifacts, dataproc, composer, iam)
}


def is_single_kind(module: ModuleType) -> bool:
    """Return whether the service's only resource kind is implied, as in ``gcw secrets NAME``."""
    return getattr(module, "SINGLE_KIND", False)


__all__ = ["LANDINGS", "SERVICES", "Landing", "is_single_kind"]
