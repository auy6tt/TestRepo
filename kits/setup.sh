#!/usr/bin/env bash
# Set up the starter kits in a new Claude Code cloud session, or on any Ubuntu or Debian machine.
#
#   bash kits/setup.sh                       system tools, then every kit's Python environment
#   bash kits/setup.sh board-minutes ...     system tools, then only the kits you name
#   bash kits/setup.sh --system              system tools only
#   bash kits/setup.sh --list                the kits, and where each kit's Python goes
#
# Cloud sessions start from a clean machine, so run this at the start of each session.
# kits/README.md shows how to put the system tools in your environment's setup script,
# so they are already there when a session starts.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KITS="$ROOT/kits"
LOGS="${TMPDIR:-/tmp}/kit-setup-logs"

# System packages the kits use (LibreOffice parts, OCR, PDF tools and fonts).
SYSTEM_PACKAGES="libreoffice-writer libreoffice-calc libreoffice-draw libreoffice-impress
  libmspub-tools poppler-utils tesseract-ocr ghostscript fonts-crosextra-carlito
  fonts-crosextra-caladea fonts-liberation fonts-dejavu-core python3-venv"

ALL_KITS="board-minutes cra-readiness doc-accessibility model-retirement pdf-binder
  publisher-rescue redcap-xlsform replication-package security-questionnaire weekly-digest"

# Where each kit's Python ends up: the same place as in the kit's own README.
python_for() {
  case "$1" in
    board-minutes)          echo "$HOME/.venvs/board-minutes/bin/python" ;;
    cra-readiness)          echo "$HOME/.cache/cra-readiness/venv/bin/python" ;;
    doc-accessibility)      echo "$HOME/.venvs/doc-accessibility/bin/python" ;;
    model-retirement)       echo "/tmp/mr-venv/bin/python" ;;
    pdf-binder)             echo "$KITS/pdf-binder/.venv/bin/python" ;;
    publisher-rescue)       echo "$HOME/.venvs/publisher-rescue/bin/python" ;;
    redcap-xlsform)         echo "/tmp/redcap-venv/bin/python" ;;
    replication-package)    echo "$ROOT/.venv/bin/python" ;;
    security-questionnaire) echo "$HOME/.venvs/security-questionnaire/bin/python" ;;
    weekly-digest)          echo "$KITS/weekly-digest/.venv/bin/python" ;;
    *) return 1 ;;
  esac
}

make_venv() {  # <folder> <requirements file>
  python3 -m venv "$1" &&
    "$1/bin/pip" install -q --upgrade pip &&
    "$1/bin/pip" install -q -r "$2"
}

setup_kit() {
  local kit="$1" py
  py="$(python_for "$kit")"
  case "$kit" in
    # These kits have their own setup script; use it so the result matches their README.
    board-minutes)     bash "$KITS/board-minutes/scripts/setup.sh" ;;
    cra-readiness)     bash "$KITS/cra-readiness/scripts/setup.sh" ;;
    doc-accessibility) bash "$KITS/doc-accessibility/scripts/setup.sh" --no-apt --verapdf ;;
    # The rest only need a virtual environment with the kit's requirements.
    *)                 make_venv "${py%/bin/python}" "$KITS/$kit/requirements.txt" ;;
  esac
}

install_system() {
  if ! command -v apt-get >/dev/null 2>&1; then
    echo "No apt-get on this machine: install LibreOffice, Tesseract, Ghostscript and Poppler yourself."
    echo "(Mac: brew install --cask libreoffice && brew install tesseract ghostscript poppler)"
    return 0
  fi
  # shellcheck disable=SC2086
  if dpkg -s $SYSTEM_PACKAGES >/dev/null 2>&1; then
    echo "System tools already installed."
    return 0
  fi
  local sudo=""
  if [ "$(id -u)" -ne 0 ]; then sudo="sudo"; fi
  echo "Installing system tools (about 2 minutes the first time)..."
  export DEBIAN_FRONTEND=noninteractive
  $sudo apt-get update -qq || echo "apt-get update failed; trying the install anyway."
  # shellcheck disable=SC2086
  if ! $sudo apt-get install -y -qq --no-install-recommends $SYSTEM_PACKAGES >/dev/null; then
    echo "Some system tools did not install. PDF conversion, OCR or .pub files may not work."
  fi
}

list_kits() {
  printf "%-24s %s\n" "Kit" "Python to run its scripts with"
  for kit in $ALL_KITS; do printf "%-24s %s\n" "$kit" "$(python_for "$kit")"; done
}

WANT_SYSTEM=1
WANT_KITS=""
for arg in "$@"; do
  case "$arg" in
    --system) WANT_KITS="none" ;;
    --list) list_kits; exit 0 ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    -*) echo "Unknown option: $arg"; exit 1 ;;
    *)
      if ! python_for "$arg" >/dev/null; then
        echo "Unknown kit: $arg. Run 'bash kits/setup.sh --list' to see the kits."; exit 1
      fi
      WANT_KITS="$WANT_KITS $arg" ;;
  esac
done
[ -z "$WANT_KITS" ] && WANT_KITS="$ALL_KITS"

[ "$WANT_SYSTEM" = 1 ] && install_system
[ "$WANT_KITS" = "none" ] && { echo "System tools done."; exit 0; }

# Set up the kits side by side; each one's output goes to its own log file.
mkdir -p "$LOGS"
echo "Setting up Python environments for: $(echo $WANT_KITS)"
echo "(logs in $LOGS)"
declare -A PIDS
for kit in $WANT_KITS; do
  setup_kit "$kit" >"$LOGS/$kit.log" 2>&1 &
  PIDS[$kit]=$!
done

FAILED=0
echo
printf "%-24s %-7s %s\n" "Kit" "Result" "Python to run its scripts with"
for kit in $WANT_KITS; do
  if wait "${PIDS[$kit]}" && [ -x "$(python_for "$kit")" ]; then
    printf "%-24s %-7s %s\n" "$kit" "ready" "$(python_for "$kit")"
  else
    printf "%-24s %-7s %s\n" "$kit" "FAILED" "see $LOGS/$kit.log"
    FAILED=1
  fi
done

echo
echo "In Claude Code, type /<kit name> (for example /board-minutes) to use a kit's skill."
exit $FAILED
