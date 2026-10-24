"""Refreshing the resource cache: fetching in parallel, and doing it in the background.

``refresh`` fetches resources with the listing functions it is given (the
cache layer does not import ``services``; the CLI passes them in) and writes
every successful result. ``spawn_background`` runs ``gcw refresh`` as a
detached process, so a stale cache is refreshed without the user waiting
(ADR-0006). Never used on the completion path, which must not spawn processes.
"""

import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

from gcw.cache import store
from gcw.context.resolve import Context

# A background refresh normally takes seconds; a lock older than this belongs
# to a process that died, so a new refresh may start.
LOCK_SECONDS = 5 * 60

Lister = Callable[[Context, str], list[store.Resource]]


def refresh(context: Context, listers: dict[tuple[str, str], Lister]) -> dict[tuple[str, str], int | Exception]:
    """Fetch resources of the given kinds in parallel and cache each successful result.

    Args:
        context: Account and project to refresh; ``context.project`` must be set.
        listers: Listing functions keyed by ``(service, kind)``.

    Returns:
        For each key, the number of cached resources, or the exception that
        prevented fetching that kind (e.g. an API disabled in the project).

    Raises:
        AuthError: No access token is available, so nothing can be fetched.
    """
    from gcw.api.auth import access_token
    from gcw.api.client import run_parallel

    token = access_token(context.account)
    fetched = run_parallel({key: (lambda lister=lister: lister(context, token)) for key, lister in listers.items()})

    results: dict[tuple[str, str], int | Exception] = {}
    for (service, kind), resources in fetched.items():
        if isinstance(resources, Exception):
            results[(service, kind)] = resources
        else:
            store.write(context.account, context.project, service, kind, resources)
            results[(service, kind)] = len(resources)
    return results


def lock_path(account: str | None, project: str) -> Path:
    """Return the lock file that marks a background refresh of ``project`` in progress."""
    return store.cache_dir() / (account or store.NO_ACCOUNT) / project / ".refresh.lock"


def release_lock(account: str | None, project: str) -> None:
    """Remove the background refresh lock; called by the refresh process when it ends."""
    lock_path(account, project).unlink(missing_ok=True)


def spawn_background(context: Context, service: str | None = None, kind: str | None = None) -> bool:
    """Start ``gcw refresh --background`` as a detached process, unless one is running.

    The child gets the same gcloud configuration and project, has no terminal
    and outlives this process. It removes the lock when it finishes.

    Args:
        context: Account, project and configuration to refresh.
        service: Refresh only this service; ``None`` refreshes everything.
        kind: Refresh only this kind of ``service``.

    Returns:
        ``True`` if a process was started, ``False`` if a recent one holds the lock
        or the process could not be started.
    """
    lock = lock_path(context.account, context.project)
    try:
        if time.time() - lock.stat().st_mtime < LOCK_SECONDS:
            return False
    except OSError:
        pass  # no lock: nothing is running
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.touch()

    command = [sys.executable, "-m", "gcw", "refresh", "--background",
               "-c", context.config.name, "-p", context.project]
    command += [part for part in (service, kind) if part]
    options: dict = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        options["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    try:
        subprocess.Popen(command, **options)
    except OSError:
        lock.unlink(missing_ok=True)
        return False
    return True
