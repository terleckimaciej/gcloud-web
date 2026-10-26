# gcloud … --web for fish (ADR-0024), printed by `gcw web-flag fish`.
# Enable in ~/.config/fish/config.fish:  gcw web-flag fish | source
#
# A gcloud command line containing --web opens its console page through
# `gcw gcloud`; every other one runs the real gcloud unchanged. gcloud's TAB
# completion is bound to the command name, so it keeps working.

function gcloud --description 'gcloud; with --web, open the console page through gcw'
    if contains -- --web $argv
        gcw gcloud $argv
    else
        command gcloud $argv
    end
end
