# Recording the README demo GIF

The README's first-screen GIF (`docs/demo.gif`) is the project's visual
elevator pitch. This page tells you how to (re)record it.

## 0. Sanitise your shell BEFORE you hit record

The recording will be pushed to a public repo. Strip anything that ties
the frames to a specific machine or human:

```bash
# In the terminal you'll record in — not your default shell!
export PS1='$ '            # bash
# or, for zsh:
export PROMPT='$ '         # zsh
unset RPROMPT              # kill any right-hand prompt
clear && tput reset        # wipe scrollback + screen
```

Also worth checking:

- Window title — most terminals show `user@host`. Set
  `DISABLE_AUTO_TITLE=true` (oh-my-zsh) or run `printf '\e]0;demo\a'`.
- Hostname in the prompt — covered by `PS1='$ '` above.
- Open files / sidebar / status bar — close every tab unrelated to the demo.
- macOS menu bar — record a cropped region, not the full screen.

If you forget any of these, redo the take. Burned-in usernames in a GIF
are forever.

## 1. Recommended: `vhs` (deterministic, scriptable)

[vhs](https://github.com/charmbracelet/vhs) takes a `.tape` script and
renders a GIF. No live typing, no shaky takes.

```bash
brew install vhs              # one-time
cd /path/to/summary-doctor
vhs docs/demo.tape            # produces docs/demo.gif
```

The tape file is checked in at [`docs/demo.tape`](./demo.tape). Edit it
to change commands, timing, theme or dimensions; re-run `vhs` to
regenerate. Target length is roughly 25-30 seconds at ~1.2 MB.

## 2. Fallback: `asciinema` + `agg`

If `vhs` is unavailable:

```bash
brew install asciinema agg
asciinema rec docs/demo.cast  # Ctrl-D to stop
agg docs/demo.cast docs/demo.gif --theme monokai --font-size 14
```

Trim long pauses with `asciinema cat docs/demo.cast | …` or re-record;
`agg` does not edit.

## 3. Wire it into the README

Add this as the first visual block of [`README.md`](../README.md):

```markdown
![summary-doctor in action](docs/demo.gif)
```

Keep the file under ~2 MB so GitHub renders it inline. If it grows
beyond that, host the GIF as a GitHub release asset and link the
release-asset URL instead.
