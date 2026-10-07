#!/usr/bin/env bash
# Set up the board minutes kit: create a Python virtual environment and install the packages.
#
# Usage:  bash kits/board-minutes/scripts/setup.sh
# The environment goes in ~/.venvs/board-minutes unless you set BOARD_MINUTES_VENV.
# Run it again in each new cloud session (the container is temporary).
set -euo pipefail

case "${1:-}" in
  -h|--help) sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
esac

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${BOARD_MINUTES_VENV:-$HOME/.venvs/board-minutes}"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Creating a virtual environment in $VENV"
  mkdir -p "$(dirname "$VENV")"
  python3 -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/python" -m pip install --quiet -r "$KIT_DIR/requirements.txt"

if ! command -v soffice >/dev/null 2>&1 && ! command -v libreoffice >/dev/null 2>&1; then
  pdf_note="LibreOffice not found: you'll get .docx and .xlsx but no PDF."
elif [ -d /usr/lib/libreoffice/program ] && [ ! -e /usr/lib/libreoffice/program/libswlo.so ]; then
  pdf_note="LibreOffice Writer is missing, so --pdf won't work. Install it with: sudo apt-get install -y --no-install-recommends libreoffice-writer"
else
  pdf_note="LibreOffice found: --pdf will work."
fi

echo "Ready. $pdf_note"
echo "Run the scripts with: $VENV/bin/python $KIT_DIR/scripts/<script>.py --help"
