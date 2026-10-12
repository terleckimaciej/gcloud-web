"""Command-line entry point: argument parsing and command dispatch for ``gcw``.

Global flags live here. Subcommands for GCP services will be generated from
the service registry in ``gcw.services``.
"""

import argparse


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
    """Build the top-level argument parser.

    Returns:
        The configured parser for the ``gcw`` command.
    """
    parser = argparse.ArgumentParser(
        prog="gcw",
        description="Open Google Cloud console pages from the terminal.",
    )
    parser.add_argument("--version", action=_VersionAction, help="show the installed version and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name; defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code.
    """
    parser = build_parser()
    parser.parse_args(argv)
    # No commands yet: show usage until the dashboard command lands.
    parser.print_help()
    return 0
