"""Console route templates: how to reach one kind of resource in the Cloud Console.

A ``Route`` is plain data declared by service modules (see ``gcw.services``).
Its ``path`` template uses these placeholders:

    {name}       resource name, e.g. a Cloud Run service
    {location}   region or zone, whichever the service uses
    {tab}        page tab; the first entry of ``tabs`` is the default
    {project}    project ID, for the few pages that need it in the path

This module only fills templates. Where the values come from (flags, gcloud
configuration, cache) is decided by the caller.
"""

import string
from dataclasses import dataclass


class RouteError(ValueError):
    """A route cannot be built from the given values; the message tells the user how to fix it."""


@dataclass(frozen=True)
class Route:
    """How to reach one kind of resource in the console.

    Attributes:
        path: Template of a single resource's page, e.g. ``"run/detail/{location}/{name}/{tab}"``.
        list_path: Page listing all resources of this kind; ``None`` if there is none.
        tabs: Allowed ``{tab}`` values; the first one is the default.
        location_label: What ``{location}`` means for this kind, used in messages
            (``"region"`` or ``"zone"``).
        location_property: gcloud property ``(section, name)`` that supplies the
            location when ``-l/--location`` is not given, e.g. ``("run", "region")``.
    """

    path: str
    list_path: str | None = None
    tabs: tuple[str, ...] = ()
    location_label: str = "region"
    location_property: tuple[str, str] | None = None

    def build(
        self,
        name: str,
        location: str | None = None,
        tab: str | None = None,
        project: str | None = None,
    ) -> str:
        """Fill the template and return the console path of one resource.

        Args:
            name: Resource name.
            location: Region or zone; required only if the template has ``{location}``.
            tab: Page tab; defaults to the first of ``tabs``.
            project: Project ID; required only if the template has ``{project}``.

        Returns:
            The console path, e.g. ``"run/detail/europe-west1/api/metrics"``.

        Raises:
            RouteError: ``tab`` is not allowed, or a value the template needs is missing.
        """
        if tab is not None and tab not in self.tabs:
            allowed = ", ".join(self.tabs) or "none"
            raise RouteError(f"unknown tab {tab!r} (available: {allowed})")

        values = {
            "name": name,
            "location": location,
            "tab": tab or (self.tabs[0] if self.tabs else None),
            "project": project,
        }
        for field in self._placeholders():
            if not values.get(field):
                raise RouteError(self._missing_message(field))
        return self.path.format(**values)

    def _placeholders(self) -> list[str]:
        """Return the placeholder names used in ``path``, in order."""
        return [field for _, field, _, _ in string.Formatter().parse(self.path) if field]

    def _missing_message(self, field: str) -> str:
        """Explain which value is missing and how the user can provide it."""
        if field == "location":
            hint = "use -l/--location"
            if self.location_property:
                hint += f" or `gcloud config set {'/'.join(self.location_property)}`"
            return f"missing {self.location_label} ({hint})"
        if field == "project":
            return "missing project (use -p or `gcloud config set project`)"
        return f"missing {field}"
