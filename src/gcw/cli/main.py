"""Command-line entry point: argument parsing and command dispatch for ``gcw``.

Global flags choose the context (``-p``, ``-c``) and what happens with the
resulting URL (``-n``, ``--no-authuser``). Commands::

    gcw               open the project dashboard
    gcw open PATH     open any console path, e.g. ``run/jobs``

Subcommands for GCP services will be generated from the service registry in
``gcw.services``.
"""

import argparse
import sys

from gcw.context.gcloud_config import UnknownConfigurationError
from gcw.context.resolve import Context, resolve_context
from gcw.web.url import console_url

DASHBOARD_PATH = "home/dashboard"


class _VersionAction(argparse.Action):
    """Print the installed package version and exit.

    Unlike argparse's built-in ``version`` action, the version is looked up only
    when the flag is used, so ``importlib.metadata`` is never imported on the
    normal startup path.
    """

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None):
        """Register the flag as taking no arguments and storing nothing."""
        super().__init__(option_strings, dest=dest, default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        """Look up the version in the package metadata, print it and exit."""
        from importlib.metadata import PackageNotFoundError, version

        try:
            installed = version("gcw")
        except PackageNotFoundError:
            installed = "unknown (package not installed)"
        # parser.exit(message=...) would write to stderr; versions belong on stdout.
        print(f"{parser.prog} {installed}")
        parser.exit()


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with global flags and commands.

    Returns:
        The configured parser for the ``gcw`` command.
    """
    parser = argparse.ArgumentParser(
        prog="gcw",
        description="Open Google Cloud console pages from the terminal.",
    )
    parser.add_argument("--version", action=_VersionAction, help="show the installed version and exit")
    parser.add_argument("-p", "--project", help="project ID to use instead of the one from gcloud")
    parser.add_argument("-c", "--configuration", help="gcloud configuration to use instead of the active one")
    parser.add_argument(
        "-n", "--no-browser", action="store_true", help="print the URL instead of opening the browser"
    )
    parser.add_argument(
        "--no-authuser",
        action="store_true",
        help="do not make the browser use the gcloud account (authuser parameter)",
    )

    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    open_command = commands.add_parser("open", help="open any console path, e.g. run/jobs")
    open_command.add_argument("path", help="path after console.cloud.google.com/")
    return parser


def _open_or_print(path: str, context: Context, *, no_browser: bool, with_authuser: bool) -> int:
    """Print the console URL for ``path`` or open it in the browser.

    Printed URLs never carry ``authuser``, so they are safe to share. Opened
    URLs carry it (unless disabled) so the console uses the gcloud account.
    If no browser can be launched, the URL is printed instead.

    Args:
        path: Console path, e.g. ``"home/dashboard"``.
        context: The resolved account and project.
        no_browser: ``-n`` was given: only print the URL.
        with_authuser: Add the ``authuser`` parameter when opening the browser.

    Returns:
        The process exit code.
    """
    if context.project is None:
        print(
            "gcw: warning: no project set (use -p or `gcloud config set project`); "
            "the console will show its last opened project",
            file=sys.stderr,
        )

    shareable_url = console_url(path, context.project)
    if no_browser:
        print(shareable_url)
        return 0

    from gcw.web.browser import open_url

    url = console_url(path, context.project, context.account if with_authuser else None)
    if not open_url(url):
        print("gcw: no browser available; open this URL manually:", file=sys.stderr)
        print(shareable_url)
        return 0
    if sys.stderr.isatty():
        print(f"Opening {url} in your browser.", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name; defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code.
    """
    args = build_parser().parse_args(argv)
    try:
        context = resolve_context(project=args.project, configuration=args.configuration)
    except UnknownConfigurationError as error:
        print(f"gcw: {error}", file=sys.stderr)
        return 2

    path = args.path if args.command == "open" else DASHBOARD_PATH
    return _open_or_print(path, context, no_browser=args.no_browser, with_authuser=not args.no_authuser)
