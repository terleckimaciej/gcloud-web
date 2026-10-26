# gcloud … --web for bash and zsh (ADR-0024), printed by `gcw web-flag bash|zsh`.
# Enable in ~/.bashrc or ~/.zshrc:  eval "$(gcw web-flag bash)"
#
# A gcloud command line containing --web opens its console page through
# `gcw gcloud`; every other one runs the real gcloud unchanged. gcloud's TAB
# completion is bound to the command name, so it keeps working.

gcloud() {
    local arg
    for arg in "$@"; do
        if [[ $arg == --web ]]; then
            gcw gcloud "$@"
            return
        fi
    done
    command gcloud "$@"
}
