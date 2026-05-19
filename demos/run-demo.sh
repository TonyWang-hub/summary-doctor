#!/usr/bin/env bash
# summary-doctor · scripted walk-through of every bundled demo.
# All runs use --mock, so no API key is required. Re-run as often as you like.
#
# This script auto-discovers any directory under demos/ that contains both a
# summary.txt and a source.txt — drop a new demo in and it shows up next run.

set -u

# ---------- styling ----------------------------------------------------------
if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
  BOLD=$(tput bold); DIM=$(tput dim); RESET=$(tput sgr0)
  CYAN=$(tput setaf 6); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); MAGENTA=$(tput setaf 5)
else
  BOLD=""; DIM=""; RESET=""; CYAN=""; GREEN=""; YELLOW=""; RED=""; MAGENTA=""
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

# ---------- per-demo configuration -------------------------------------------
# Lookup helpers: derive lang + headline colour + descriptive tag from the dir
# name. Anything we don't recognise gets sensible defaults.
demo_lang () {
  case "$1" in
    *-zh) echo zh ;;
    *-en) echo en ;;
    *)    echo auto ;;
  esac
}

# tag: short human-readable name; mostly inferred from the dir slug
demo_tag () {
  local d="$1"
  # strip leading "NN-" prefix
  local stem="${d#[0-9][0-9]-}"
  # lang suffix → uppercase
  case "$stem" in
    *-zh) echo "${stem%-zh}" "(ZH)" ;;
    *-en) echo "${stem%-en}" "(EN)" ;;
    *)    echo "$stem" ;;
  esac
}

# headline colour: positive controls go green, everything else gets a
# warning palette
demo_colour () {
  case "$1" in
    *faithful*)         echo "$GREEN" ;;
    *softening*)        echo "$YELLOW" ;;
    *scope-creep*)      echo "$YELLOW" ;;
    *cherry-picking*)   echo "$MAGENTA" ;;
    *temporal*)         echo "$MAGENTA" ;;
    *fabricated*)       echo "$RED" ;;
    *reversal*|*inversion*) echo "$RED" ;;
    *)                  echo "$CYAN" ;;
  esac
}

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

# ---------- discover ---------------------------------------------------------
# every immediate subdir of demos/ that has both summary.txt and source.txt.
# bash 3.2 (macOS default) has no mapfile, so we collect via a for-loop.
DEMOS=()
while IFS= read -r line; do
  DEMOS+=("$line")
done < <(
  for d in demos/*/; do
    d="${d%/}"
    [[ -f "$d/summary.txt" && -f "$d/source.txt" ]] || continue
    echo "$d"
  done | sort
)

if [[ ${#DEMOS[@]} -eq 0 ]]; then
  printf "${RED}no demos found under demos/${RESET}\n" >&2
  exit 1
fi

# ---------- run --------------------------------------------------------------
clear
printf "${BOLD}summary-doctor${RESET} ${DIM}· walk-through of %d demo(s) (mock mode)${RESET}\n" "${#DEMOS[@]}"
say "out dir : $OUT_DIR  ${DIM}(auto-cleaned on exit)${RESET}"
echo

declare -a DEMO_NAMES DEMO_DIVS DEMO_REVS DEMO_FABS
n=0
for dir in "${DEMOS[@]}"; do
  n=$((n + 1))
  name="$(basename "$dir")"
  lang="$(demo_lang "$name")"
  tag="$(demo_tag "$name")"
  colour="$(demo_colour "$name")"

  say "Demo $n: $tag ..."
  run_demo "$n" "$tag" "$lang" "$dir" "$colour"

  out="$OUT_DIR/demo-${n}.md"
  div=$(awk -F'[*%]' '/Divergence score/ {gsub(/[^0-9]/,"",$3); print $3}' "$out")
  rev=$(awk -F'|' '/^\| `reversed`/ {gsub(/[^0-9]/,"",$3); print $3}' "$out")
  fab=$(awk -F'|' '/^\| `fabricated`/ {gsub(/[^0-9]/,"",$3); print $3}' "$out")
  DEMO_NAMES+=("$name")
  DEMO_DIVS+=("${div:-?}")
  DEMO_REVS+=("${rev:-0}")
  DEMO_FABS+=("${fab:-0}")
  sleep 0.3
done

# ---------- summary ----------------------------------------------------------
hr
printf "${BOLD}summary:${RESET}\n"
printf "  %-32s %8s %10s %12s\n" "demo" "div%" "reversed" "fabricated"
printf "  %-32s %8s %10s %12s\n" "----" "----" "--------" "----------"
for i in "${!DEMO_NAMES[@]}"; do
  name="${DEMO_NAMES[$i]}"
  div="${DEMO_DIVS[$i]}"
  rev="${DEMO_REVS[$i]}"
  fab="${DEMO_FABS[$i]}"
  case "$name" in
    *faithful*) colour="$GREEN" ;;
    *) colour="$RED" ;;
  esac
  printf "  ${colour}%-32s %8s %10s %12s${RESET}\n" "$name" "${div}%" "$rev" "$fab"
done
echo
say "done. reports were written under: $OUT_DIR"
say "tip: rerun with real LLM by dropping --mock and exporting ANTHROPIC_API_KEY."
hr
