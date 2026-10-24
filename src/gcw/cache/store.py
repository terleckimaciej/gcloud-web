"""Resource cache entries and their storage.

A ``Resource`` is one cached resource: the flat ``{name, location, extra}``
record of ADR-0006. Service modules produce them in their ``list_*`` functions;
completion and the CLI read them back. This module is on the completion path,
so it imports nothing heavy.
"""

from dataclasses import dataclass, field
from typing import Any


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
