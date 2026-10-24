# bash completion for gcw.
# Enable in ~/.bashrc:  eval "$(gcw completion bash)"
# Candidates come from `gcw __complete`, which reads only local files; bash
# cannot show descriptions, so only the values are used.

_gcw_complete() {
    local IFS=$'\n'
    local output
    output=$(gcw __complete -- "${COMP_WORDS[@]:0:COMP_CWORD+1}" 2>/dev/null) || return 0
    COMPREPLY=($(printf '%s\n' "$output" | cut -f1))
}

complete -F _gcw_complete gcw
