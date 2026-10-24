"""Access tokens for Google APIs, taken from the gcloud CLI.

The token comes from the official ``gcloud auth print-access-token`` command
(ADR-0016), so gcw never reads gcloud's credential store. The command takes
about a second, which is acceptable because tokens are needed only off the
completion path: background cache refresh and live lookups.
"""

import shutil
import subprocess

_TIMEOUT_SECONDS = 60

# One token per account for the lifetime of the process. A refresh issues a
# dozen requests within seconds, far below the token's one-hour lifetime.
_tokens: dict[str | None, str] = {}


class AuthError(RuntimeError):
    """No access token is available; the message tells the user how to fix it."""


def access_token(account: str | None = None) -> str:
    """Return an OAuth access token for ``account``, as gcloud would use it.

    Args:
        account: Google account email (``core/account`` of the gcloud
            configuration in use); ``None`` lets gcloud pick its active account.

    Returns:
        The access token.

    Raises:
        AuthError: gcloud is not installed, has no credentials for the account,
            or the command failed or timed out.
    """
    if account not in _tokens:
        _tokens[account] = _token_from_gcloud(account)
    return _tokens[account]


def _token_from_gcloud(account: str | None) -> str:
    """Run ``gcloud auth print-access-token`` and return its output."""
    # which() also finds gcloud.cmd on Windows, which a bare "gcloud" would not.
    gcloud = shutil.which("gcloud")
    if gcloud is None:
        raise AuthError("gcloud not found on PATH; install the Google Cloud CLI and run `gcloud auth login`")

    command = [gcloud, "auth", "print-access-token", "--verbosity=error"]
    if account:
        command += ["--account", account]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        raise AuthError(f"`gcloud auth print-access-token` timed out after {_TIMEOUT_SECONDS} s") from None

    token = result.stdout.strip()
    if result.returncode != 0 or not token:
        reason = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "no token returned"
        who = f" for {account}" if account else ""
        raise AuthError(f"cannot get an access token{who} ({reason}); run `gcloud auth login`")
    return token
