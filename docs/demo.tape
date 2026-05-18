# vhs tape — renders docs/demo.gif for the README first screen.
# Run from repo root:   vhs docs/demo.tape
# Target length ~28s. See docs/RECORDING-GIF.md for the sanitisation checklist.

Output docs/demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 800
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms
Set PlaybackSpeed 1.0
Set Padding 20

# Neutral prompt — no username, no hostname, no cwd.
Hide
Type "export PS1='$ '"      Enter
Type "export PYTHONPATH=src" Enter
Type "clear"                 Enter
Show

# ---- title card -----------------------------------------------------------
Type "# summary-doctor — citations, not verdicts."
Sleep 1500ms
Enter
Sleep 500ms

# ---- demo 1: reversal ------------------------------------------------------
Type "# demo 1 · reversal (the summary flips the source's conclusion)"
Enter
Sleep 600ms
Type "python3 -m summary_doctor demos/01-reversal-en/summary.txt --original demos/01-reversal-en/source.txt --lang en --mock"
Sleep 400ms
Enter
Sleep 3500ms

# ---- demo 3: positive control ---------------------------------------------
Type "# demo 3 · positive control · faithful summary should score 0%"
Enter
Sleep 600ms
Type "python3 -m summary_doctor demos/03-faithful-en/summary.txt --original demos/03-faithful-en/source.txt --lang en --mock"
Sleep 400ms
Enter
Sleep 3500ms

# ---- one-shot recap --------------------------------------------------------
Type "# all three demos in one go"
Enter
Sleep 500ms
Type "bash demos/run-demo.sh"
Sleep 300ms
Enter
Sleep 6000ms

# tail card
Sleep 1500ms
