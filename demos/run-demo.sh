#!/usr/bin/env bash
# summary-doctor · scripted walk-through of the three bundled demos.
# All runs use --mock, so no API key is required. Re-run as often as you like.

set -u

# ---------- styling ----------------------------------------------------------
if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
  BOLD=$(tput bold); DIM=$(tput dim); RESET=$(tput sgr0)
  CYAN=$(tput setaf 6); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1)
else
  BOLD=""; DIM=""; RESET=""; CYAN=""; GREEN=""; YELLOW=""; RED=""
fi

ts()  { date +"%H:%M:%S"; }
hr()  { printf "${DIM}%s${RESET}\n" "────────────────────────────────────────────────────────────"; }
say() { printf "${DIM}[%s]${RESET} %s\n" "$(ts)" "$*"; }

# ---------- locate repo + entry point ---------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if command -v summary-doctor >/dev/null 2>&1; then
  RUNNER=(summary-doctor)
else
  export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
  RUNNER=(python3 -m summary_doctor)
fi

OUT_DIR="$(mktemp -d -t summary-doctor-demo-XXXXXX)"
trap 'rm -rf "$OUT_DIR"' EXIT

# ---------- helpers ----------------------------------------------------------
run_demo () {
  local n="$1" tag="$2" lang="$3" dir="$4" headline_color="$5"
  local summary="$dir/summary.txt" source="$dir/source.txt"
  local out="$OUT_DIR/demo-${n}.md"

  hr
  printf "${BOLD}${CYAN}>> Demo %s: %s${RESET}\n" "$n" "$tag"
  say "summary : $summary"
  say "source  : $source"
  say "running : ${RUNNER[*]} ... --lang $lang --mock"
  echo

  "${RUNNER[@]}" "$summary" \
      --original "$source" \
      --lang "$lang" \
      --mock \
      --out "$out" \
      | sed "s/^/    /"

  echo
  printf "${BOLD}${headline_color}== headline ==${RESET}\n"
  grep -E "^- (Claims analyzed|Divergence score):" "$out" | sed "s/^/    /"
  echo
  printf "${BOLD}${headline_color}== label distribution ==${RESET}\n"
  awk '/^## Label distribution/{flag=1; next} flag && /^## /{flag=0} flag' "$out" | sed "s/^/    /"
}

# ---------- run --------------------------------------------------------------
clear
printf "${BOLD}summary-doctor${RESET} ${DIM}· three-demo walk-through (mock mode)${RESET}\n"
say "out dir : $OUT_DIR  ${DIM}(auto-cleaned on exit)${RESET}"
echo

say "Demo 1: detecting reversal..."
run_demo 1 "reversal (EN)"   en demos/01-reversal-en   "$RED"
sleep 1

say "Demo 2: detecting softening..."
run_demo 2 "softening (ZH)"  zh demos/02-softening-zh  "$YELLOW"
sleep 1

say "Demo 3: positive control (faithful summary should be 0%)..."
run_demo 3 "faithful (EN)"   en demos/03-faithful-en   "$GREEN"

# ---------- summary ----------------------------------------------------------
hr
score () { awk -F'[*%]' '/Divergence score/ {gsub(/[^0-9]/,"",$3); print $3}' "$1"; }
revs  () { awk -F'|' '/^\| `reversed`/ {gsub(/[^0-9]/,"",$3); print $3}' "$1"; }

D1_REV=$(revs  "$OUT_DIR/demo-1.md")
D1_DIV=$(score "$OUT_DIR/demo-1.md")
D2_DIV=$(score "$OUT_DIR/demo-2.md")
D3_DIV=$(score "$OUT_DIR/demo-3.md")

printf "${BOLD}summary:${RESET}\n"
printf "  demo 1 (reversal)   caught ${RED}${BOLD}%s${RESET} reversed claim(s) · divergence ${RED}${BOLD}%s%%${RESET}\n" "${D1_REV:-?}" "${D1_DIV:-?}"
printf "  demo 2 (softening)  divergence ${YELLOW}${BOLD}%s%%${RESET}\n" "${D2_DIV:-?}"
printf "  demo 3 (positive)   divergence ${GREEN}${BOLD}%s%%${RESET}  ${DIM}(expected 0%%)${RESET}\n" "${D3_DIV:-?}"
echo
say "done. reports were written under: $OUT_DIR"
say "tip: rerun with real LLM by dropping --mock and exporting ANTHROPIC_API_KEY."
hr
