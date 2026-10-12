"""Command-line entry point: argument parsing and command dispatch for ``gcw``.

Global flags choose the context (``-p``, ``-c``) and what happens with the
resulting URL (``-n``, ``--no-authuser``); they work before or after the
command. Commands::

    gcw                                  open the project dashboard
    gcw open PATH                        open any console path, e.g. ``run/jobs``
    gcw SERVICE [KIND [NAME]]            service overview, list of a kind, or one resource
        [-l LOCATION] [--tab TAB]

Service commands are generated from the registry in ``gcw.services``.
"""

import argparse
import sys
from types import ModuleType

from gcw.context.gcloud_config import UnknownConfigurationError
from gcw.context.resolve import Context, resolve_context
from gcw.services import SERVICES
from gcw.web.route import RouteError
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


def _add_global_flags(parser: argparse.ArgumentParser, *, with_defaults: bool) -> None:
    """Add the flags that are accepted both before and after a command.

    The top-level parser defines their defaults. Command parsers add the same
    flags without defaults (``SUPPRESS``), so a flag omitted after the command
    does not overwrite a value given before it.

    Args:
        parser: Parser to extend.
        with_defaults: ``True`` for the top-level parser, ``False`` for command parsers.
    """
    defaults = {} if with_defaults else {"default": argparse.SUPPRESS}
    parser.add_argument("-p", "--project", help="project ID to use instead of the one from gcloud", **defaults)
    parser.add_argument(
        "-c", "--configuration", help="gcloud configuration to use instead of the active one", **defaults
    )
    parser.add_argument(
        "-n", "--no-browser", action="store_true", help="print the URL instead of opening the browser", **defaults
    )
    parser.add_argument(
        "--no-authuser",
        action="store_true",
        help="do not make the browser use the gcloud account (authuser parameter)",
        **defaults,
    )


def _add_service_command(commands, module: ModuleType) -> None:
    """Add ``gcw <service> [KIND [NAME]]`` for one service module from the registry."""
    command = commands.add_parser(module.NAME, help=module.HELP, description=module.HELP)
    _add_global_flags(command, with_defaults=False)
    command.add_argument("kind", nargs="?", choices=list(module.KINDS), metavar="KIND",
                         help=f"resource kind: {', '.join(module.KINDS)}")
    command.add_argument("name", nargs="?", help="resource name; omit to open the list")
    command.add_argument("-l", "--location", "--region", "--zone", dest="location",
                         help="region or zone of the resource (default: from gcloud configuration)")
    command.add_argument("--tab", help="page tab of the resource")
    command.set_defaults(service=module)


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
    _add_global_flags(parser, with_defaults=True)

    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    open_command = commands.add_parser("open", help="open any console path, e.g. run/jobs")
    _add_global_flags(open_command, with_defaults=False)
    open_command.add_argument("path", help="path after console.cloud.google.com/")
    for module in SERVICES.values():
        _add_service_command(commands, module)
    return parser


def _service_path(args: argparse.Namespace, context: Context) -> str:
    """Return the console path for a service command.

    ``gcw run`` gives the service overview, ``gcw run services`` the list of
    services, and ``gcw run services api`` one resource. A missing location is
    taken from the gcloud property declared by the route (e.g. ``run/region``).

    Raises:
        RouteError: The resource page cannot be built (e.g. no location, unknown tab).
    """
    module = args.service
    if args.kind is None:
        return module.LANDING
    route = module.KINDS[args.kind]
    if args.name is None:
        return route.list_path or module.LANDING

    location = args.location
    if location is None and route.location_property:
        location = context.config.get(*route.location_property)
    return route.build(args.name, location=location, tab=args.tab, project=context.project)


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
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in SERVICES and args.name is None and (args.location or args.tab):
        parser.error("--location and --tab require a resource NAME")

    try:
        context = resolve_context(project=args.project, configuration=args.configuration)
        if args.command == "open":
            path = args.path
        elif args.command in SERVICES:
            path = _service_path(args, context)
        else:
            path = DASHBOARD_PATH
    except (UnknownConfigurationError, RouteError) as error:
        print(f"gcw: {error}", file=sys.stderr)
        return 2

    return _open_or_print(path, context, no_browser=args.no_browser, with_authuser=not args.no_authuser)
