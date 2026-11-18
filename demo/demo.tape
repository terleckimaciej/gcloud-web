# Demo GIF for the README. Run it through demo/render.sh, which prepares the
# fake gcloud configuration and cache this tape relies on.

Require fish

Output demo/demo.gif

Set Shell "fish"
Set FontSize 20
Set Width 900
Set Height 420
Set Padding 20
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 100ms
Set Framerate 20

# Setup, not recorded: a clean fish (no config, no history, so no
# autosuggestions), a short green prompt, colours that make the typed command
# stand out (bold command, yellow flags, blue comments for the scene titles),
# a visible highlight on the menu entry that is selected, and gcw's completion
# and gcloud --web enabled.
Hide
Type "exec fish --no-config --private"
Enter
Type "set -g fish_greeting"
Enter
Type "function fish_prompt; set_color green; printf '$ '; set_color normal; end"
Enter
Type "set -g fish_color_command brgreen --bold; set -g fish_color_param brwhite; set -g fish_color_option yellow; set -g fish_color_comment blue"
Enter
Type "set -g fish_pager_color_selected_background --background=brblack; set -g fish_pager_color_selected_completion brwhite --bold"
Enter
Type "gcw completion fish | source"
Enter
Type "gcw web-flag fish | source"
Enter
Type "clear"
Enter
Show

# Scene titles are typed as shell comments, faster than the commands.
Type@35ms "# 1. gcw: its own syntax, TAB shows the options"
Enter
Sleep 600ms

# Scene 1: pick the kind and the resource from the menu: TAB lists, a second
# TAB enters the menu, arrows move, Enter accepts.
Type "gcw run "
Sleep 200ms
Tab
Sleep 1s
Tab
Sleep 400ms
Right
Sleep 500ms
Enter
Sleep 300ms
Tab
Sleep 1s
Tab
Sleep 400ms
Enter
Sleep 300ms

# Scene 2: the flags with their descriptions, then the tab of the page; the
# logs tab opens.
Type "--"
Sleep 200ms
Tab
Sleep 1500ms
Type "tab "
Sleep 300ms
Tab
Sleep 1s
Tab
Sleep 400ms
Enter
Sleep 500ms
Enter
Sleep 5s

# Scene 3: the same for a gcloud command with --web.
Hide
Ctrl+L
Show
Type@35ms "# 2. gcloud: add --web to any gcloud command"
Enter
Sleep 600ms
Type "gcloud run jobs describe nightly --web"
Sleep 600ms
Enter
Sleep 6s
