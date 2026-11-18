# Demo GIF

`demo/demo.gif`, the animation at the top of the [README](../README.md), is generated, not recorded by hand. Regenerate it after any change to gcw's output or completion:

```
bash demo/render.sh
```

It takes about two minutes and rewrites `demo/demo.gif`.

## Requirements

- [VHS](https://github.com/charmbracelet/vhs), which needs [ttyd](https://github.com/tsl0922/ttyd) and [ffmpeg](https://ffmpeg.org) on your `PATH`
- [fish](https://fishshell.com), the shell the recording runs in: its menu shows the completion candidates with descriptions
- [uv](https://docs.astral.sh/uv/), to run gcw from the project environment

On macOS, `brew install vhs fish` installs everything but uv.

On Debian or Ubuntu, `ffmpeg`, `ttyd` and `fish` come from apt; VHS is a `.deb` from its GitHub releases:

```
sudo apt install ffmpeg ttyd fish
gh release download -R charmbracelet/vhs -p '*amd64.deb' -D /tmp/vhs
sudo apt install /tmp/vhs/vhs_*_amd64.deb
```

`render.sh` checks for the tools and names any that are missing.

## How it works

- `demo.tape` is the VHS script: the window, the theme, the typing speed and every key press.
- `render.sh` prepares what the script runs against, then calls `vhs demo/demo.tape`. It builds a fake gcloud configuration (a made-up project and no account) and a resource cache in a temporary directory, through `CLOUDSDK_CONFIG` and `GCW_CACHE_DIR`. So the recording needs no network or real account, your own configuration is not touched, and no personal data can appear in it.
- With no account in the configuration, gcw adds no `authuser` parameter, so the printed URLs contain no email address.
- `BROWSER=true` makes gcw believe a browser started: it prints `Opening <url> in your browser.` and nothing opens.
- The setup part of the tape runs between `Hide` and `Show`, so it is not in the GIF. It starts `fish --no-config --private`, a clean shell with no user configuration and no history (so no autosuggestions), and sets the prompt and colours.

## Changing the scenes

Edit `demo.tape` and run `render.sh` again. The GIF is shown on GitHub and PyPI in a column about 830 px wide, so keep the font large enough to read at that size, and keep the file under about 5 MB.

The resource names TAB offers come from the cache that `render.sh` writes. Add or rename a resource there, not in the tape.
