"""Paging long command output through the user's pager, the way git and gh do it.

Only informational commands (``gcw services``, later ``gcw ls``) page their
output. A printed URL never does: it is one line meant to be copied or piped.

Paging happens only when stdout is an interactive terminal, so redirecting or
piping (``gcw services | grep sql``) still produces plain text.

This module spawns a subprocess, so it must never be imported on the completion
path; ``cli.main`` imports it inside the command that needs it.
"""

import os
import shlex
import shutil
import subprocess
import sys

# Pager behaviour that makes a short listing usable: quit if it fits on one
# screen (F), keep colours (R), leave the text on screen after quitting (X).
# Only used when the user has no LESS of their own.
DEFAULT_LESS = "FRX"


def write_paged(text: str) -> None:
    """Write ``text`` to stdout, through a pager when stdout is a terminal.

    Falls back to a plain write whenever paging is not possible or not wanted:
    stdout is not a terminal, the user disabled the pager, the pager is not
    installed, or it cannot be started. Quitting the pager early is not an
    error either.

    Args:
        text: The complete output; a trailing newline is added if missing.
    """
    if not text.endswith("\n"):
        text += "\n"

    command = _pager_command() if _stdout_is_terminal() else None
    if command is None:
        sys.stdout.write(text)
        return

    try:
        subprocess.run(command, input=text, text=True, env=_pager_env(command), check=False)
    except (OSError, KeyboardInterrupt):
        # Pager missing, died, or closed before reading everything (`q` in less).
        pass


def _stdout_is_terminal() -> bool:
    """Return whether stdout is an interactive terminal.

    A function of its own rather than an inline ``sys.stdout.isatty()``, so that
    a test can state which of the two cases it exercises: pytest replaces
    ``sys.stdout`` between setting a test up and running it, which makes
    patching the stream itself unreliable.
    """
    return sys.stdout.isatty()


def _pager_command() -> list[str] | None:
    """Return the pager to run as an argument list, or ``None`` to page nothing.

    ``GCW_PAGER`` wins over ``PAGER``; an empty value or ``cat`` disables paging,
    as in git. Without either, ``less`` is used when installed.
    """
    if os.name == "nt":
        # cmd.exe quoting does not match shlex, so a PAGER set on Windows cannot
        # be split reliably; the built-in pager is enough there.
        return ["more"] if shutil.which("more") else None

    # An empty value is a deliberate "no pager", so it must not fall through to
    # the next variable the way an unset one does.
    configured = os.environ.get("GCW_PAGER")
    if configured is None:
        configured = os.environ.get("PAGER")
    if configured is None:
        configured = "less"
    if configured.strip() in ("", "cat"):
        return None
    command = shlex.split(configured)
    return command if command and shutil.which(command[0]) else None


def _pager_env(command: list[str]) -> dict[str, str]:
    """Return the environment for the pager, with sane ``less`` defaults.

    A ``LESS`` set by the user is left alone; only its absence is filled in.
    """
    env = dict(os.environ)
    if os.path.basename(command[0]) == "less":
        env.setdefault("LESS", DEFAULT_LESS)
    return env
