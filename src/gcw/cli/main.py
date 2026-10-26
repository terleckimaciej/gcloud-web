"""Command-line entry point: argument parsing and command dispatch for ``gcw``.

Global flags choose the context (``-p``, ``-c``) and what happens with the
resulting URL (``-n``, ``--no-authuser``); they work before or after the
command. Commands::

    gcw                                  open the project dashboard
    gcw SERVICE [KIND [NAME]]            service overview, list of a kind, or one resource
        [-l LOCATION] [--tab TAB]
    gcw SERVICE [NAME]                   the same for a service with a single kind
    gcw SERVICE                          start page of a service that has no routes yet
    gcw open PATH                        open any console page no service command covers
    gcw gcloud GCLOUD_ARGS...            open the page of a gcloud read command (ADR-0020)
    gcw cache list [SERVICE [KIND]]      show the cached resources (alias: ls)
    gcw cache refresh [SERVICE [KIND]]   fetch resource names into the local cache
    gcw completion bash|zsh|fish         print the shell completion script
    gcw env CONFIGURATION                switch the gcloud configuration of this shell

The hidden ``gcw __complete -- WORDS...`` answers TAB for those scripts; it is
dispatched before the parser is built (see ``gcw.cli.complete``).

Service commands are generated from the two registries in ``gcw.services``:
modules with routes (``SERVICES``) and start pages (``LANDINGS``).
"""

import argparse
import sys
from types import ModuleType

from gcw.context.gcloud_config import UnknownConfigurationError
from gcw.context.resolve import Context, resolve_context
from gcw.services import LANDINGS, SERVICES, Landing, is_single_kind
from gcw.web.route import RouteError
from gcw.web.url import console_url

DASHBOARD_PATH = "home/dashboard"

# gcw's own commands with their one-line help, in the order of `gcw --help`.
OWN_COMMANDS = {
    "services": "list the supported services, kinds and tabs",
    "cache": "show or refresh the local resource cache",
    "open": "open a console page no service command covers",
    "env": "switch the gcloud configuration of this shell",
    "completion": "print the shell completion script",
    "gcloud": "open the page of a gcloud command, e.g. gcw gcloud run jobs describe nightly",
    "web-flag": "print the shell function that adds --web to gcloud",
}

# Shown at the end of `gcw --help`. The command list above it cannot carry every
# service (there are dozens of start pages), so the examples teach the shape of a
# command instead, one line per form: dashboard, resource, tab, list, start page,
# other project, raw path.
EXAMPLES = """\
examples:
  gcw                                project dashboard
  gcw run services api               the Cloud Run service "api"
  gcw run services api --tab logs    its logs tab
  gcw run jobs                       the list of Cloud Run jobs
  gcw secrets db-password            a secret (services with one kind omit it)
  gcw bigquery                       the BigQuery start page
  gcw pubsub -p other-project        Pub/Sub in another project
  gcw open logs/query -n             print the URL of any console path
  gcw cache refresh                  cache resource names for TAB completion
  gcw cache ls run                   show the cached Cloud Run resources
  eval "$(gcw env work)"             use the "work" configuration in this shell\
"""


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


class _Parser(argparse.ArgumentParser):
    """ArgumentParser whose error for an unknown command stays short.

    argparse lists every choice, which for ``COMMAND`` means about 70 names;
    other errors, such as an unknown kind, keep their short list of choices.
    """

    def error(self, message):
        """Replace the unknown-command message, then exit with argparse's usual code 2."""
        prefix = "argument COMMAND: invalid choice: "
        if message.startswith(prefix):
            command = message[len(prefix):].split(" (choose from", 1)[0]
            message = f"unknown command {command}; see `gcw --help` or `gcw services`"
        super().error(message)


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
    """Add ``gcw <service> [KIND [NAME]]`` for one service module from the registry.

    A service with a single kind gets ``gcw <service> [NAME]`` instead; its
    ``kind`` is always ``None`` after parsing and is implied by ``_service_path``.
    """
    # No help=: argparse would list it among gcw's own commands; _services_help lists it instead.
    command = commands.add_parser(module.NAME, description=module.HELP)
    _add_global_flags(command, with_defaults=False)
    if is_single_kind(module):
        command.set_defaults(kind=None)
    else:
        command.add_argument("kind", nargs="?", choices=list(module.KINDS), metavar="KIND",
                             help=f"resource kind: {', '.join(module.KINDS)}")
    command.add_argument("name", nargs="?", help="resource name; omit to open the list")
    # All six spellings are the same flag: a route needs either a region or a zone,
    # never both, so the user can type whichever word fits the service.
    command.add_argument("-l", "--location", "-r", "--region", "-z", "--zone", dest="location",
                         help="region or zone of the resource (default: from gcloud configuration)")
    command.add_argument("--tab", help="page tab of the resource")
    for name, link in getattr(module, "LINKS", {}).items():
        command.add_argument(f"--{name}", dest=f"link_{name}", action="store_true", help=link.help)
    command.set_defaults(service=module)


def _add_cache_commands(commands) -> None:
    """Add ``gcw cache list`` (alias ``ls``) and ``gcw cache refresh``.

    The cache is a noun among the other top-level nouns (services, ``open``,
    ``services``); its actions are subcommands, as in ``pip cache`` or
    ``uv cache`` (ADR-0018). Each takes the global flags and an optional
    ``SERVICE [KIND]`` filter. The action is stored in ``cache_action``,
    because argparse records an alias as typed (``ls``), not as ``list``.
    """
    cache = commands.add_parser("cache", description=OWN_COMMANDS["cache"])
    actions = cache.add_subparsers(dest="cache_command", metavar="ACTION", required=True)

    list_command = actions.add_parser("list", aliases=["ls"], help="show the cached resources",
                                      description="show the cached resources")
    _add_cache_filter(list_command)
    list_command.set_defaults(cache_action="list")

    refresh_command = actions.add_parser("refresh", help="fetch resource names into the cache",
                                         description="fetch resource names into the cache")
    _add_cache_filter(refresh_command)
    # Used by the detached process that refreshes a stale cache; not for users.
    refresh_command.add_argument("--background", action="store_true", help=argparse.SUPPRESS)
    refresh_command.set_defaults(cache_action="refresh")


def _add_cache_filter(command: argparse.ArgumentParser) -> None:
    """Add the global flags and the optional ``SERVICE [KIND]`` filter of a cache action."""
    _add_global_flags(command, with_defaults=False)
    command.add_argument("filter_service", nargs="?", choices=list(SERVICES), metavar="SERVICE",
                         help="only this service (default: all services with resources)")
    command.add_argument("filter_kind", nargs="?", metavar="KIND", help="only this resource kind of SERVICE")


def _add_landing_command(commands, name: str, landing: Landing) -> None:
    """Add ``gcw <service>`` for one service that only has a start page.

    These commands take no resource arguments, only the global flags. They are
    left out of the ``gcw --help`` command list (argparse lists a subparser only
    when it is given ``help``), because there are dozens of them; ``gcw
    services`` is where they are meant to be discovered. ``gcw <service>
    --help`` still works and shows the description.
    """
    command = commands.add_parser(name, description=landing.help)
    _add_global_flags(command, with_defaults=False)
    command.set_defaults(landing=landing)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with global flags and commands.

    Returns:
        The configured parser for the ``gcw`` command.
    """
    parser = _Parser(
        prog="gcw",
        usage="%(prog)s [FLAGS] [COMMAND ...]",
        description=_commands_help(),
        epilog=EXAMPLES,
        # Keep the line breaks and alignment of the command list and examples;
        # argparse rewraps text by default.
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action=_VersionAction, help="show the installed version and exit")
    _add_global_flags(parser, with_defaults=True)

    # help=SUPPRESS: argparse's own list would mix gcw's commands and the GCP
    # services in one flat section; _commands_help() lists them in two groups.
    # prog: without it, subcommand usage would start with the custom top-level usage above.
    commands = parser.add_subparsers(dest="command", metavar="COMMAND", help=argparse.SUPPRESS, prog="gcw")
    open_command = commands.add_parser("open", description="open any path after console.cloud.google.com/, with "
                                       "the project and account added; for a supported service use its "
                                       "command instead (`gcw run jobs`, not `gcw open run/jobs`)")
    _add_global_flags(open_command, with_defaults=False)
    open_command.add_argument("path", help="path after console.cloud.google.com/")
    # Parsed by gcw.cli.gcloud_syntax, not here (see main); registered for --help and the command list.
    gcloud_command = commands.add_parser(
        "gcloud",
        description="open the console page of a gcloud read command (describe, list, get-iam-policy): "
        "gcw gcloud run jobs describe nightly --region europe-west1 opens the job. Prints the matching "
        "gcw command to stderr. gcw's -n and --no-authuser go at the end, with the gcloud flags.",
    )
    gcloud_command.add_argument("words", nargs=argparse.REMAINDER, metavar="GCLOUD_ARGS",
                                help="a gcloud command line without the leading `gcloud`")
    web_flag = commands.add_parser(
        "web-flag",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="print a shell function named gcloud: a gcloud command line with --web opens its\n"
        "console page through `gcw gcloud`, any other runs gcloud unchanged (ADR-0024).\n\n"
        f"{_enable_help('web-flag')}\n\n"
        "Then open a new terminal and try: gcloud run jobs list --web",
    )
    web_flag.add_argument("shell", choices=["bash", "zsh", "fish"])
    web_flag.add_argument("--install", action="store_true",
                          help="add the line that loads the function to the shell's startup file")
    # Need no context, so they take no global flags.
    commands.add_parser("services", description=OWN_COMMANDS["services"])
    _add_cache_commands(commands)
    completion = commands.add_parser(
        "completion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"print the TAB completion script for gcw.\n\n{_enable_help('completion')}\n\n"
        "In zsh the line has to come after compinit; --install adds it at the end of ~/.zshrc.",
    )
    completion.add_argument("shell", choices=["bash", "zsh", "fish"])
    completion.add_argument("--install", action="store_true",
                            help="add the line that loads completion to the shell's startup file")
    env = commands.add_parser("env", description="print the command that switches the gcloud configuration of "
                              'the current shell only; use it as eval "$(gcw env CONFIGURATION)", '
                              "or `gcw env CONFIGURATION --shell fish | source`")
    env.add_argument("configuration", metavar="CONFIGURATION", help="name of a gcloud configuration")
    env.add_argument("--shell", choices=["bash", "zsh", "fish"], default="bash",
                     help="syntax of the printed command (default: bash, also right for zsh)")
    for module in SERVICES.values():
        _add_service_command(commands, module)
    for name, landing in LANDINGS.items():
        _add_landing_command(commands, name, landing)
    return parser


def _commands_help() -> str:
    """Return the description of ``gcw --help``: one command list in two groups.

    gcw's own commands and the GCP services are both commands, so they share one
    ``commands:`` heading; the groups only tell them apart. The dozens of start
    pages are left to ``gcw services``.
    """
    column = max(len(name) for name in [*OWN_COMMANDS, *SERVICES]) + 4
    lines = ["Open Google Cloud console pages from the terminal.", "", "COMMAND:", "  gcw's own:"]
    lines += [f"    {name:<{column}}{help_text}" for name, help_text in OWN_COMMANDS.items()]
    lines += ["", "  GCP services (gcw SERVICE [KIND [NAME]]):"]
    lines += [f"    {name:<{column}}{module.HELP}" for name, module in SERVICES.items()]
    lines += [
        "",
        f"  Many more services have a start page only, like `gcw bigquery` ({len(LANDINGS)} in all);",
        "  run `gcw services` for all of them, with their kinds and tabs.",
    ]
    return "\n".join(lines)


def _services_listing() -> str:
    """Return every service the CLI knows, in two groups.

    Services with routes come first, each followed by its resource kinds and
    their tabs, then the services that only have a start page. The split is the
    useful distinction here: it says whether ``gcw <service> <kind> <name>`` can
    reach a single resource, or only the service's own page.

    Returns:
        The listing as one string, ready for the pager.
    """
    column = max(len(name) for name in [*SERVICES, *LANDINGS]) + 4
    lines = ["services with resources:"]

    for name, module in sorted(SERVICES.items()):
        lines.append(f"  {name.ljust(column)}{module.HELP}")
        for kind, route in module.KINDS.items():
            tabs = "tabs: " + ", ".join(route.tabs) if route.tabs else ""
            # The kind of a single-kind service is never typed, so show where the name goes.
            label = "NAME" if is_single_kind(module) else kind
            lines.append(f"    {label.ljust(column - 2)}{tabs}".rstrip())

    lines.append("\nstart pages only:")
    lines += [f"  {name.ljust(column)}{landing.help}" for name, landing in sorted(LANDINGS.items())]
    return "\n".join(lines)


STARTUP_FILES = {"bash": "~/.bashrc", "zsh": "~/.zshrc", "fish": "~/.config/fish/config.fish"}


def _startup_line(command: str, shell: str) -> str:
    """Return the startup-file line that loads ``gcw <command> <shell>`` in every new shell."""
    if shell == "fish":
        return f"gcw {command} fish | source"
    return f'eval "$(gcw {command} {shell})"'


def _enable_help(command: str) -> str:
    """Explain in ``--help`` how to enable ``gcw completion`` or ``gcw web-flag`` for good."""
    runs = "\n".join(f"  gcw {command} {shell} --install" for shell in STARTUP_FILES)
    adds = "\n".join(f"  {_startup_line(command, shell):<40}{path}" for shell, path in STARTUP_FILES.items())
    return (
        f"To enable it in every new terminal, run once for your shell:\n\n{runs}\n\n"
        "--install appends one line to the shell's startup file, unless it is already there:\n\n"
        f"{adds}\n\n"
        "Without --install the script is only printed."
    )


def _startup_file(shell: str):
    """Return the startup file of ``shell``: ``~/.bashrc``, ``$ZDOTDIR/.zshrc`` or fish's ``config.fish``."""
    import os
    from pathlib import Path

    home = Path.home()
    if shell == "zsh":
        return Path(os.environ.get("ZDOTDIR") or home) / ".zshrc"
    if shell == "fish":
        return Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config") / "fish" / "config.fish"
    return home / ".bashrc"


def _install_startup_line(command: str, shell: str) -> int:
    """Append the line that loads ``gcw <command> <shell>`` to the shell's startup file, once.

    Returns:
        0; the message says whether the line was added or already there.
    """
    line = _startup_line(command, shell)
    path = _startup_file(shell)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in text.splitlines():
        print(f"already enabled: {path} has `{line}`")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as startup:
        startup.write(("\n" if text and not text.endswith("\n") else "") + line + "\n")
    print(f"added `{line}` to {path}; open a new terminal to use it")
    return 0


def _gcloud_command(words: list[str]) -> int:
    """Run ``gcw gcloud …``: translate a gcloud command line and run the gcw command it names.

    The translated command is printed to stderr, so the user sees the plain gcw
    spelling, then run through ``main`` like any other command (ADR-0020).

    Args:
        words: The gcloud command line after ``gcloud``.

    Returns:
        The exit code of the translated command, or 2 if it cannot be translated.
    """
    import shlex

    from gcw.cli.gcloud_syntax import TranslationError, translate

    try:
        translated = translate(words)
    except TranslationError as error:
        print(f"gcw: {error}", file=sys.stderr)
        return 2
    print(f"same as: {shlex.join(['gcw', *translated])}", file=sys.stderr)
    return main(translated)


def _service_path(args: argparse.Namespace, context: Context) -> str:
    """Return the console path for a service command.

    ``gcw run`` gives the service overview, ``gcw run services`` the list of
    services, and ``gcw run services api`` one resource. For a single-kind
    service, ``gcw secrets db-password`` is the resource of its only kind. A
    missing location comes from the resource cache or the gcloud configuration
    (see ``gcw.cli.lookup``). A link flag such as ``--airflow`` gives the
    absolute URL cached with the resource instead of a console path.

    Raises:
        RouteError: The resource page cannot be built (e.g. no location, unknown tab).
    """
    module = args.service
    kind = next(iter(module.KINDS)) if is_single_kind(module) and args.name else args.kind
    if kind is None:
        return module.LANDING
    route = module.KINDS[kind]
    if args.name is None:
        return route.list_path or module.LANDING
    name = route.strip_prefix(args.name)

    from gcw.cli.lookup import link_url, resource_location

    for link_name, link in getattr(module, "LINKS", {}).items():
        if getattr(args, f"link_{link_name}", False):
            if kind != link.kind:
                raise RouteError(f"--{link_name} applies to {module.NAME} {link.kind} only")
            return link_url(context, module.NAME, link, name)

    location = resource_location(context, module.NAME, kind, route, name, args.location)
    return route.build(name, location=location, tab=args.tab, project=context.project)


def _open_or_print(path: str, context: Context, *, no_browser: bool, with_authuser: bool) -> int:
    """Print the console URL for ``path`` or open it in the browser.

    Printed URLs never carry ``authuser``, so they are safe to share. Opened
    URLs carry it (unless disabled) so the console uses the gcloud account.
    An absolute URL (a page outside the console, e.g. Airflow) is used as is.
    If no browser can be launched, the URL is printed instead.

    Args:
        path: Console path, e.g. ``"home/dashboard"``, or an absolute URL.
        context: The resolved account and project.
        no_browser: ``-n`` was given: only print the URL.
        with_authuser: Add the ``authuser`` parameter when opening the browser.

    Returns:
        The process exit code.
    """
    external = path.startswith(("https://", "http://"))
    if context.project is None and not external:
        print(
            "gcw: warning: no project set (use -p or `gcloud config set project`); "
            "the console will show its last opened project",
            file=sys.stderr,
        )

    shareable_url = path if external else console_url(path, context.project)
    if no_browser:
        print(shareable_url)
        return 0

    from gcw.web.browser import open_url

    url = path if external else console_url(path, context.project, context.account if with_authuser else None)
    if not open_url(url):
        print("gcw: no browser available; open this URL manually:", file=sys.stderr)
        print(shareable_url)
        return 0
    if sys.stderr.isatty():
        print(f"Opening {url} in your browser.", file=sys.stderr)
    return 0


def _cache_command(args: argparse.Namespace, context: Context) -> int:
    """Run ``gcw cache list`` or ``gcw cache refresh``, which need a project but open no URL."""
    if context.project is None:
        print("gcw: no project set (use -p or `gcloud config set project`)", file=sys.stderr)
        return 2
    from gcw.cli.resources import ls_command, refresh_command

    if args.cache_action == "list":
        return ls_command(context, args.filter_service, args.filter_kind)
    return refresh_command(context, args.filter_service, args.filter_kind, background=args.background)


def _env_command(configuration: str, shell: str) -> int:
    """Print the command that makes ``configuration`` active in the calling shell only.

    gcloud honours ``$CLOUDSDK_ACTIVE_CONFIG_NAME`` over its global
    ``active_config`` file, so other terminals keep their configuration
    (ADR-0005). A program cannot change its parent shell's environment,
    hence the ``eval`` around the command.

    Returns:
        The exit code: 2 if the configuration does not exist.
    """
    import shlex

    from gcw.context.gcloud_config import list_configurations

    available = list_configurations()
    if configuration not in available:
        print(f"gcw: {UnknownConfigurationError(configuration, available)}", file=sys.stderr)
        return 2
    if shell == "fish":
        print(f"set -gx CLOUDSDK_ACTIVE_CONFIG_NAME {shlex.quote(configuration)}")
    else:
        print(f"export CLOUDSDK_ACTIVE_CONFIG_NAME={shlex.quote(configuration)}")
    if sys.stdout.isatty():
        usage = f"gcw env {configuration} --shell fish | source" if shell == "fish" else f'eval "$(gcw env {configuration})"'
        print(f"gcw: this only prints the command; to apply it, run: {usage}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name; defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code.
    """
    if argv is None:
        argv = sys.argv[1:]
    if argv[:1] == ["__complete"]:
        from gcw.cli.complete import run

        return run(argv[1:])
    # gcloud's flags (--region, --format, --web…) are not gcw's, so argparse never sees them.
    if argv[:1] == ["gcloud"] and argv[1:] not in (["-h"], ["--help"]):
        return _gcloud_command(argv[1:])

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "gcloud":
        parser.error("gcw flags go at the end of a gcloud command line, e.g. gcw gcloud run jobs list -n")
    if args.command in ("completion", "web-flag"):
        if args.install:
            return _install_startup_line(args.command, args.shell)
        from importlib.resources import files

        if args.command == "completion":
            script = f"gcw.{args.shell}"
        else:
            script = "web-flag.fish" if args.shell == "fish" else "web-flag.sh"
        print(files("gcw.cli").joinpath("shell", script).read_text(encoding="utf-8"), end="")
        return 0
    if args.command == "env":
        return _env_command(args.configuration, args.shell)
    if args.command == "services":
        # Pure information about the build; no gcloud context is needed or read.
        print(_services_listing())
        return 0
    if args.command in SERVICES and args.name is None:
        links = [name for name in getattr(args.service, "LINKS", {}) if getattr(args, f"link_{name}")]
        if links:
            parser.error(f"--{links[0]} requires a resource NAME")
        if args.location or args.tab:
            parser.error("--location and --tab require a resource NAME")
    if args.command == "cache" and args.filter_kind is not None:
        kinds = SERVICES[args.filter_service].KINDS
        if args.filter_kind not in kinds:
            parser.error(f"unknown kind {args.filter_kind!r} of {args.filter_service} (available: {', '.join(kinds)})")

    try:
        context = resolve_context(project=args.project, configuration=args.configuration)
        if args.command == "cache":
            return _cache_command(args, context)
        if args.command == "open":
            path = args.path
        elif args.command in SERVICES:
            path = _service_path(args, context)
        elif args.command in LANDINGS:
            path = LANDINGS[args.command].path
        else:
            path = DASHBOARD_PATH
    except (UnknownConfigurationError, RouteError) as error:
        print(f"gcw: {error}", file=sys.stderr)
        return 2

    return _open_or_print(path, context, no_browser=args.no_browser, with_authuser=not args.no_authuser)
