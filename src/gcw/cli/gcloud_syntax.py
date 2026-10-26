"""Translating a gcloud command line into gcw arguments (ADR-0020).

``gcw gcloud run jobs describe nightly --region europe-west1`` becomes
``gcw run jobs nightly --region europe-west1``: the service and kind are the
same words in both tools (ADR-0019), the verb is dropped, and the context
flags keep their names, because gcw accepts them as aliases.

Only commands that read are translated. A command that changes resources
(``update``, ``deploy``…), a sub-group gcw does not model, or an unknown
service or kind is an error naming the nearest page gcw knows, so ``--web``
never opens a page in place of an action.

The tables below are the whole translation; services need no attribute of
their own. Nothing here touches the network or the cache: the translated
arguments go through the normal command path.
"""

from gcw.services import LANDINGS, SERVICES, is_single_kind

# gcloud verbs that read; the value says what they open.
READ_VERBS = {"describe": "resource", "get-iam-policy": "resource", "list": "list"}

# Read commands placed right after the service, mapped to the kind they browse.
GROUP_COMMANDS = {("storage", "ls"): "buckets"}

# gcloud flags that gcw takes under the same name; each has a value.
CONTEXT_FLAGS = ("--project", "--configuration")
LOCATION_FLAGS = ("--region", "--zone", "--location")

# gcw's own flags, which gcloud does not have; they pass through unchanged.
# Every other flag, `--web` included, is dropped.
GCW_FLAGS = ("-n", "--no-browser", "--no-authuser")


class TranslationError(ValueError):
    """A gcloud command line has no page in gcw; the message names the nearest one."""


def translate(words: list[str]) -> list[str]:
    """Return the gcw arguments for a gcloud command line.

    Args:
        words: The command line after ``gcloud``, e.g.
            ``["run", "jobs", "describe", "nightly", "--region", "europe-west1"]``.

    Returns:
        Arguments for ``gcw``, e.g. ``["run", "jobs", "nightly", "--region", "europe-west1"]``.
        Location flags are kept only when a resource is named, because list
        and start pages take none.

    Raises:
        TranslationError: The command is not a read command gcw can open.
    """
    positional, flags = _split_at_first_flag(words)
    target, named = _target(positional)
    context, location, own = _kept_flags(flags)
    return target + context + (location if named else []) + own


def _split_at_first_flag(words: list[str]) -> tuple[list[str], list[str]]:
    """Split the words into those before the first flag and the rest.

    gcloud commands put service, kind, verb and name first in practice, and a
    bare word after a flag is usually that flag's value, so only the words
    before the first flag are read as positionals.
    """
    for index, word in enumerate(words):
        if word.startswith("-"):
            return words[:index], words[index:]
    return words, []


def _kept_flags(flags: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Pick the flags gcw keeps, as ready gcw arguments.

    A value comes after ``=`` or as the next word. Unknown flags, their values
    and ``--web`` are dropped.

    Returns:
        ``(context flags, location flags, gcw flags)``, e.g.
        ``(["--project", "p"], ["--region", "europe-west1"], ["-n"])``.
    """
    context: list[str] = []
    location: list[str] = []
    own: list[str] = []
    index = 0
    while index < len(flags):
        word = flags[index]
        index += 1
        if word in GCW_FLAGS:
            own.append(word)
            continue
        flag, has_value, value = word.partition("=")
        if flag not in CONTEXT_FLAGS + LOCATION_FLAGS:
            continue
        if not has_value and index < len(flags) and not flags[index].startswith("-"):
            value = flags[index]
            index += 1
        if value:
            (location if flag in LOCATION_FLAGS else context).extend([flag, value])
    return context, location, own


def _target(positional: list[str]) -> tuple[list[str], bool]:
    """Translate service, kind, verb and name into gcw's positionals.

    Returns:
        ``(gcw positionals, whether they end with a resource name)``, e.g.
        ``(["run", "jobs", "nightly"], True)`` or ``(["run", "jobs"], False)``.

    Raises:
        TranslationError: An unknown service or kind, or a word in the verb
            position that is not a read verb.
    """
    if not positional:
        return [], False
    service, rest = positional[0], positional[1:]
    if service in LANDINGS:
        return [service], False
    module = SERVICES.get(service)
    if module is None:
        raise _not_openable([service], [])

    group_kind = GROUP_COMMANDS.get((service, rest[0])) if rest else None
    if group_kind is not None:
        name = rest[1:2]
        return [service, group_kind, *name], bool(name)

    if is_single_kind(module):
        page = [service]
    else:
        if not rest:
            return [service], False
        if rest[0] not in module.KINDS:
            raise _not_openable([service, rest[0]], [service])
        page, rest = [service, rest[0]], rest[1:]

    if not rest:
        return page, False
    verb = rest[0]
    if verb not in READ_VERBS:
        raise _not_openable(page + [verb], page)
    if READ_VERBS[verb] == "list" or len(rest) < 2:
        return page, False
    return page + [rest[1]], True


def _not_openable(words: list[str], nearest: list[str]) -> TranslationError:
    """Build the error for a command gcw cannot open, pointing to the nearest page."""
    return TranslationError(
        f"`gcloud {' '.join(words)}` is not a command gcw can open; gcw only opens pages.\n"
        f"Run it with gcloud itself, without --web. Nearest page: gcw {' '.join(nearest)}".rstrip()
    )
