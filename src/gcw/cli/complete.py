"""TAB completion backend: ``gcw __complete -- WORDS...``, called by the shell scripts in ``shell/``.

The shell passes every word of the command line, starting with ``gcw`` and
ending with the word under the cursor (empty after a space). The answer is one
candidate per line, ``value<TAB>description``; fish shows the description as
is, zsh through ``_describe``, bash drops it.

Candidates come only from the gcloud configuration files and the resource
cache: this path never touches the network, never starts a process and never
triggers a background refresh (ADR-0006, AGENTS.md), so a TAB is answered in
tens of milliseconds even when the cache is empty or stale.
"""

import sys

from gcw.cache import store
from gcw.context.gcloud_config import UnknownConfigurationError, list_configurations, load_gcloud_config
from gcw.services import LANDINGS, SERVICES, is_single_kind

# Flags that take a value; the value is the next word.
VALUE_FLAGS = {"-p", "--project", "-c", "--configuration", "-l", "--location", "-r", "--region",
               "-z", "--zone", "--tab"}
LOCATION_FLAGS = {"-l", "--location", "-r", "--region", "-z", "--zone"}

GLOBAL_FLAGS = [
    ("--project", "project ID to use instead of the one from gcloud"),
    ("--configuration", "gcloud configuration to use"),
    ("--no-browser", "print the URL instead of opening the browser"),
    ("--no-authuser", "do not pass the gcloud account to the browser"),
]
RESOURCE_FLAGS = [
    ("--location", "region or zone of the resource"),
    ("--tab", "page tab of the resource"),
]

COMMANDS = {
    "open": "open any console path",
    "services": "list the supported services, kinds and tabs",
    "cache": "show or refresh the local resource cache",
    "completion": "print the shell completion script",
}
CACHE_ACTIONS = {"list": "show the cached resources", "refresh": "fetch resource names into the cache"}
SHELLS = {"bash": "", "zsh": "", "fish": ""}

Candidate = tuple[str, str]


def run(argv: list[str]) -> int:
    """Print completion candidates for ``gcw __complete -- WORDS...``; always exits 0.

    Any failure prints nothing, so a broken cache or configuration never
    disturbs the user's shell.
    """
    words = argv[1:] if argv[:1] == ["--"] else argv
    try:
        found = candidates(words)
    except Exception:  # completion must never print a traceback into the shell
        return 0
    sys.stdout.write("".join(f"{value}\t{description}\n" for value, description in found))
    return 0


def candidates(words: list[str]) -> list[Candidate]:
    """Return the candidates for the last word of a ``gcw`` command line.

    Args:
        words: The command line as the shell split it: ``["gcw", ..., current]``.

    Returns:
        ``(value, description)`` pairs that start with the current word.
    """
    if len(words) < 2:
        return []
    current, previous = words[-1], words[-2]
    positional, options = _parse(words[1:-1])
    found = _for_flag_value(previous, positional, options) if previous in VALUE_FLAGS else None
    if found is None:
        found = _flags(positional) if current.startswith("-") else _positional(positional, options)
    return [(value, description) for value, description in found if value.startswith(current)]


def _parse(done: list[str]) -> tuple[list[str], dict[str, str]]:
    """Split the completed words into positional arguments and flag values."""
    positional: list[str] = []
    options: dict[str, str] = {}
    index = 0
    while index < len(done):
        word = done[index]
        if word in VALUE_FLAGS and index + 1 < len(done):
            options[word] = done[index + 1]
            index += 2
            continue
        if not word.startswith("-"):
            positional.append(word)
        index += 1
    return positional, options


def _context(options: dict[str, str]) -> tuple[str | None, str | None, str | None]:
    """Return ``(account, project, configured project)`` for the flags on the line."""
    configuration = options.get("-c") or options.get("--configuration")
    try:
        config = load_gcloud_config(configuration)
    except UnknownConfigurationError:
        return None, None, None
    project = options.get("-p") or options.get("--project") or config.project
    return config.account, project, config.project


def _positional(positional: list[str], options: dict[str, str]) -> list[Candidate]:
    """Candidates for the next positional word: command, kind, name, cache action or shell."""
    if not positional:
        return (
            [(name, module.HELP) for name, module in sorted(SERVICES.items())]
            + list(COMMANDS.items())
            + [(name, landing.help) for name, landing in sorted(LANDINGS.items())]
        )
    command, rest = positional[0], positional[1:]
    if command == "completion":
        return list(SHELLS.items()) if not rest else []
    if command == "cache":
        if not rest:
            return list(CACHE_ACTIONS.items())
        if len(rest) == 1:
            return [(name, module.HELP) for name, module in sorted(SERVICES.items())]
        if len(rest) == 2 and rest[1] in SERVICES:
            return [(kind, "") for kind in SERVICES[rest[1]].KINDS]
        return []
    module = SERVICES.get(command)
    if module is None:
        return []
    if is_single_kind(module):
        return _names(module, next(iter(module.KINDS)), options) if not rest else []
    if not rest:
        return [(kind, _cached_count(module, kind, options)) for kind in module.KINDS]
    if len(rest) == 1 and rest[0] in module.KINDS:
        return _names(module, rest[0], options)
    return []


def _names(module, kind: str, options: dict[str, str]) -> list[Candidate]:
    """Cached resource names of one kind, described as ``location · project``."""
    account, project, _ = _context(options)
    entry = store.read(account, project, module.NAME, kind) if project else None
    if entry is None:
        return []
    return [(r.name, " · ".join(part for part in (r.location, project) if part)) for r in entry.resources]


def _cached_count(module, kind: str, options: dict[str, str]) -> str:
    """Describe a kind by how many of its resources are cached, if any."""
    account, project, _ = _context(options)
    entry = store.read(account, project, module.NAME, kind) if project else None
    return f"{len(entry.resources)} cached" if entry else ""


def _for_flag_value(flag: str, positional: list[str], options: dict[str, str]) -> list[Candidate]:
    """Candidates for the value of ``flag``: configurations, projects, locations or tabs."""
    if flag in ("-c", "--configuration"):
        return [(name, load_gcloud_config(name).project or "") for name in list_configurations()]
    if flag in ("-p", "--project"):
        account, _, configured = _context(options)
        projects = set(store.cached_projects(account)) | ({configured} if configured else set())
        return [(project, "configured" if project == configured else "cached") for project in sorted(projects)]
    module, kind = _service_kind(positional)
    if module is None or kind is None:
        return []
    if flag == "--tab":
        return [(tab, "default" if index == 0 else "") for index, tab in enumerate(module.KINDS[kind].tabs)]
    if flag in LOCATION_FLAGS:
        account, project, _ = _context(options)
        entry = store.read(account, project, module.NAME, kind) if project else None
        locations = sorted({r.location for r in entry.resources if r.location}) if entry else []
        return [(location, "") for location in locations]
    return []


def _flags(positional: list[str]) -> list[Candidate]:
    """Flags that fit the command on the line."""
    flags = list(GLOBAL_FLAGS)
    module, _ = _service_kind(positional)
    if module is not None:
        flags += RESOURCE_FLAGS
        flags += [(f"--{name}", link.help) for name, link in getattr(module, "LINKS", {}).items()]
    return flags


def _service_kind(positional: list[str]):
    """Return ``(module, kind)`` of a service command on the line; either may be ``None``."""
    module = SERVICES.get(positional[0]) if positional else None
    if module is None:
        return None, None
    if is_single_kind(module):
        return module, next(iter(module.KINDS))
    kind = positional[1] if len(positional) > 1 and positional[1] in module.KINDS else None
    return module, kind
