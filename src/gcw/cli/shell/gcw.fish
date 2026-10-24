# fish completion for gcw.
# Enable in ~/.config/fish/config.fish:  gcw completion fish | source
# Candidates come from `gcw __complete` as "value<TAB>description" lines,
# which fish shows with their descriptions.

complete -c gcw -f -a '(gcw __complete -- (commandline -opc) (commandline -ct) 2>/dev/null)'
