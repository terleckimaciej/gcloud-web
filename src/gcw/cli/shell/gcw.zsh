# zsh completion for gcw.
# Enable in ~/.zshrc, after compinit:  eval "$(gcw completion zsh)"
# Candidates come from `gcw __complete` as "value<TAB>description" lines,
# shown with their descriptions through _describe.

_gcw() {
    local -a lines candidates
    local line value description
    lines=("${(@f)$(gcw __complete -- "${(@)words[1,CURRENT]}" 2>/dev/null)}")
    for line in $lines; do
        [[ -z $line ]] && continue
        value=${line%%$'\t'*}
        description=${line#*$'\t'}
        value=${value//:/\\:}
        if [[ -n $description ]]; then
            candidates+=("$value:$description")
        else
            candidates+=("$value")
        fi
    done
    _describe -t values gcw candidates
}

compdef _gcw gcw
