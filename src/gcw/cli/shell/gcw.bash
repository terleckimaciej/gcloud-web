# bash completion for gcw.
# Enable in ~/.bashrc:  eval "$(gcw completion bash)"
# Candidates come from `gcw __complete`, which reads only local files.
#
# bash has no field for descriptions, so, like gh's completion, a list where
# every candidate has one is shown as "name  (description)" with the names
# padded to one column; a single candidate is the bare name, which bash
# inserts. Names never contain spaces, so the common prefix bash inserts stays
# inside the names. A list where only some candidates have a description is
# shown as plain names, so it packs into columns.
#
# An empty value marks a group break (after gcw's own commands): blank entries
# fill the rest of that column, so the next group starts a new one. This needs
# `complete -o nosort` (bash 4.4+); older bash sorts the list, so no gap there.
# Written for bash 3.2 (macOS): no negative indices, no mapfile.

_gcw_complete() {
    local output
    output=$(gcw __complete -- "${COMP_WORDS[@]:0:COMP_CWORD+1}" 2>/dev/null) || return 0
    local -a values=() descriptions=()
    local line value width=0 described=0 group_break=0
    while IFS= read -r line; do
        [[ -n $line ]] || continue
        value=${line%%$'\t'*}
        if [[ -z $value ]]; then
            group_break=${#values[@]}
            continue
        fi
        values+=("$value")
        if [[ $line == *$'\t'?* ]]; then
            descriptions+=("${line#*$'\t'}")
            described=$((described + 1))
        else
            descriptions+=("")
        fi
        (( ${#value} > width )) && width=${#value}
    done <<< "$output"
    local count=${#values[@]} i entry
    COMPREPLY=()
    if (( count == 1 )); then
        COMPREPLY=("${values[0]}")
    elif (( count > 0 && described == count )); then
        for i in "${!values[@]}"; do
            printf -v entry '%-*s  (%s)' "$width" "${values[i]}" "${descriptions[i]}"
            COMPREPLY+=("$entry")
        done
    else
        COMPREPLY=("${values[@]}")
        if [[ -n $_gcw_nosort ]] && (( group_break > 0 && group_break < count )); then
            _gcw_add_gap "$group_break" "$width"
        fi
    fi
    return 0
}

# Insert blank entries after the first $1 entries of COMPREPLY so the rest
# starts a new column. Mirrors readline's layout: a column is the longest
# entry ($2) plus two, filled top to bottom.
_gcw_add_gap() {
    local first=$1 width=$2
    local count=${#COMPREPLY[@]} screen=${COLUMNS:-80}
    local columns=$(( screen / (width + 2) ))
    (( columns > 1 && columns * (width + 2) == screen )) && columns=$((columns - 1))
    (( columns >= 2 )) || return 0
    local rows=$first
    while (( (rows + count - first + columns - 1) / columns > rows )); do
        rows=$((rows + 1))
    done
    (( (rows + count - first + columns - 1) / columns == rows )) || return 0
    local gap=$((rows - first))
    (( gap <= width )) || return 0
    local -a blanks=()
    local i blank
    for (( i = 1; i <= gap; i++ )); do
        printf -v blank '%*s' "$i" ''
        blanks+=("$blank")
    done
    COMPREPLY=("${COMPREPLY[@]:0:first}" "${blanks[@]}" "${COMPREPLY[@]:first}")
}

if complete -o nosort -F _gcw_complete gcw 2>/dev/null; then
    _gcw_nosort=1
else
    complete -F _gcw_complete gcw
fi
