"""Resource cache entries and their storage on disk.

A ``Resource`` is one cached resource: the flat ``{name, location, extra}``
record of ADR-0006. Service modules produce them in their ``list_*`` functions;
completion and the CLI read them back.

Layout: one JSON file per account, project and resource kind::

    <cache dir>/<account>/<project>/<service>.<kind>.json
    {"fetched_at": <unix time>, "resources": [{"name": ..., "location": ..., "extra": {...}}]}

Entries never expire hard. After ``SOFT_TTL_SECONDS`` an entry is stale: it is
still used, and the caller starts a background refresh. Writes are atomic, so a
reader never sees a half-written file. This module is on the completion path,
so it imports nothing heavy.
"""

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SOFT_TTL_SECONDS = 24 * 60 * 60

# Directory name used when the gcloud configuration has no account.
NO_ACCOUNT = "_"


@dataclass(frozen=True)
class Resource:
    """One resource as stored in the cache.

    Attributes:
        name: Name the user types, e.g. a Cloud Run service name or a bucket.
        location: Region or zone, or ``None`` for global resources.
        extra: Service-specific details used to build URLs, e.g. a Composer
            environment's ``airflow_uri`` or a repository's ``format``.
    """

    name: str
    location: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        """Return the resource as a JSON-serialisable dict."""
        return {"name": self.name, "location": self.location, "extra": self.extra}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Resource":
        """Build a resource from a dict written by ``to_json``."""
        return cls(data["name"], data.get("location"), data.get("extra") or {})


@dataclass(frozen=True)
class CacheEntry:
    """The cached resources of one kind, with the time they were fetched.

    Attributes:
        resources: The resources, in the order the API returned them.
        fetched_at: Unix time of the fetch.
    """

    resources: list[Resource]
    fetched_at: float

    def is_stale(self, now: float | None = None) -> bool:
        """Return whether the entry is older than the soft TTL and should be refreshed."""
        return (now if now is not None else time.time()) - self.fetched_at > SOFT_TTL_SECONDS


def cache_dir() -> Path:
    """Return the root cache directory.

    ``$GCW_CACHE_DIR`` wins; otherwise ``%LOCALAPPDATA%\\gcw`` on Windows and
    ``$XDG_CACHE_HOME/gcw`` (default ``~/.cache/gcw``) elsewhere.
    """
    override = os.environ.get("GCW_CACHE_DIR")
    if override:
        return Path(override)
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "gcw"
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "gcw"


def entry_path(account: str | None, project: str, service: str, kind: str) -> Path:
    """Return the file that holds the resources of one kind."""
    return cache_dir() / (account or NO_ACCOUNT) / project / f"{service}.{kind}.json"


def read(account: str | None, project: str, service: str, kind: str) -> CacheEntry | None:
    """Read the cached resources of one kind.

    Returns:
        The entry, or ``None`` if nothing is cached or the file is unreadable
        (a corrupt file is treated as missing and gets rewritten on refresh).
    """
    try:
        data = json.loads(entry_path(account, project, service, kind).read_text(encoding="utf-8"))
        return CacheEntry([Resource.from_json(item) for item in data["resources"]], float(data["fetched_at"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def write(account: str | None, project: str, service: str, kind: str, resources: list[Resource]) -> None:
    """Replace the cached resources of one kind, atomically.

    The data goes to a temporary file in the same directory, which then
    replaces the entry in one step, so concurrent readers see either the old
    or the new list.
    """
    # Imported here: tempfile is slow to import and completion only reads.
    import tempfile

    path = entry_path(account, project, service, kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"fetched_at": time.time(), "resources": [r.to_json() for r in resources]})
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(body)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def cached_projects(account: str | None) -> list[str]:
    """Return the projects that have any cached resources for ``account``, sorted."""
    try:
        return sorted(entry.name for entry in (cache_dir() / (account or NO_ACCOUNT)).iterdir() if entry.is_dir())
    except OSError:
        return []
