# fish completion for gcw.
# Enable in ~/.config/fish/config.fish:  gcw completion fish | source
# Candidates come from `gcw __complete` as "value<TAB>description" lines,
# which fish shows with their descriptions. A line with an empty value is a
# group break, used by bash only, so it is dropped.

complete -c gcw -f -a '(gcw __complete -- (commandline -opc) (commandline -ct) 2>/dev/null | string match -v -r "^\t")'
