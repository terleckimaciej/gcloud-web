"""The ``gcw refresh`` and ``gcw ls`` commands: filling the resource cache and showing it.

Both take an optional ``SERVICE [KIND]`` filter; without it they cover every
kind of every service in ``gcw.services``. Imported lazily by ``gcw.cli.main``,
since neither command is on the completion path.
"""

import sys

from gcw.cache import store
from gcw.context.resolve import Context
from gcw.services import SERVICES, lister


def targets(service: str | None, kind: str | None) -> list[tuple[str, str]]:
    """Return the ``(service, kind)`` pairs selected by the command's filter.

    Args:
        service: Service name, or ``None`` for all services.
        kind: Kind of ``service``, or ``None`` for all its kinds. The parser
            has already checked that it belongs to the service.
    """
    names = [service] if service else list(SERVICES)
    return [(name, k) for name in names for k in SERVICES[name].KINDS if kind in (None, k)]


def refresh_command(context: Context, service: str | None, kind: str | None, *, background: bool) -> int:
    """Fetch the selected kinds into the cache and report the outcome per kind.

    Args:
        context: Account and project to refresh.
        service: Service filter, or ``None``.
        kind: Kind filter, or ``None``.
        background: Run by ``spawn_background``: print nothing and release the
            refresh lock at the end.

    Returns:
        The exit code: 0 if at least one kind was fetched, 1 otherwise.
    """
    from gcw.api.auth import AuthError
    from gcw.cache.refresh import refresh, release_lock

    selected = targets(service, kind)
    try:
        results = refresh(context, {(s, k): lister(SERVICES[s], k) for s, k in selected})
    except AuthError as error:
        if not background:
            print(f"gcw: {error}", file=sys.stderr)
        return 1
    finally:
        if background:
            release_lock(context.account, context.project)

    if not background:
        print(f"Refreshed project {context.project}:")
        width = max(len(f"{s} {k}") for s, k in selected) + 2
        for (s, k), result in results.items():
            outcome = f"skipped: {_short(result)}" if isinstance(result, Exception) else str(result)
            print(f"  {f'{s} {k}'.ljust(width)}{outcome}")
    return 0 if any(not isinstance(result, Exception) for result in results.values()) else 1


def ls_command(context: Context, service: str | None, kind: str | None) -> int:
    """Print the cached resources of the selected kinds as a table, through the pager.

    Returns:
        The exit code: 0 if anything is cached, 1 if nothing is (with a hint to refresh).
    """
    from gcw.cli.pager import write_paged

    rows: list[tuple[str, str, str]] = []
    stale = False
    for s, k in targets(service, kind):
        entry = store.read(context.account, context.project, s, k)
        if entry is None:
            continue
        stale = stale or entry.is_stale()
        rows += [(r.name, r.location or "-", f"{s} {k}") for r in entry.resources]

    if not rows:
        print(f"gcw: no cached resources for project {context.project}; run `gcw refresh`", file=sys.stderr)
        return 1
    header = ("NAME", "LOCATION", "KIND")
    widths = [max(len(row[i]) for row in [header, *rows]) for i in range(2)]
    lines = [f"{a.ljust(widths[0])}  {b.ljust(widths[1])}  {c}" for a, b, c in [header, *rows]]
    write_paged("\n".join(lines) + "\n")
    if stale:
        print("gcw: some of these are older than 24 hours; run `gcw refresh` to update", file=sys.stderr)
    return 0


def _short(error: Exception) -> str:
    """Return the first sentence of an error message, for a one-line report."""
    message = str(error).splitlines()[0] if str(error) else type(error).__name__
    first, dot, _ = message.partition(". ")
    return first + ("." if dot else "")
