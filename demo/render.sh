#!/usr/bin/env bash
# Regenerate demo/demo.gif from demo/demo.tape.
#
#     bash demo/render.sh
#
# The recording runs against a fake gcloud configuration and resource cache
# built in a temporary directory, so it needs no network, no real account and
# no browser, and shows no personal data. See demo/README.md.
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

missing=()
for tool in vhs ttyd ffmpeg fish uv; do
    command -v "$tool" >/dev/null || missing+=("$tool")
done
if ((${#missing[@]})); then
    echo "render.sh: missing ${missing[*]}; see demo/README.md for the install steps" >&2
    exit 1
fi

cd "$repo"
uv sync --quiet

# A gcloud configuration with a made-up project and no account: without one
# gcw adds no authuser parameter, so no email address, not even a fake one,
# shows in the printed URLs.
export CLOUDSDK_CONFIG="$work/gcloud"
mkdir -p "$CLOUDSDK_CONFIG/configurations"
printf 'default' >"$CLOUDSDK_CONFIG/active_config"
cat >"$CLOUDSDK_CONFIG/configurations/config_default" <<'EOF'
[core]
project = acme-demo

[run]
region = europe-west1
EOF

# The resource cache TAB completion reads. Entries are written now, so they
# are fresh; stale ones would make gcw refresh them in the background.
export GCW_CACHE_DIR="$work/cache"
uv run python - <<'PY'
from gcw.cache.store import Resource, write

account, project = None, "acme-demo"
region = "europe-west1"
write(account, project, "run", "services", [Resource(n, region) for n in ("api", "web", "worker")])
write(account, project, "run", "jobs", [Resource(n, region) for n in ("nightly", "cleanup-exports")])
PY

# `true` makes gcw think a browser started, so it prints "Opening <url> in
# your browser." without opening anything.
export BROWSER=true
export PATH="$repo/.venv/bin:$PATH"

vhs demo/demo.tape
