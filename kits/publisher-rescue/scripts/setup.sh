#!/usr/bin/env bash
# One-time setup for a fresh Ubuntu or Debian machine or cloud sandbox.
#
#   bash kits/publisher-rescue/scripts/setup.sh
#
# Installs:
#   - LibreOffice Draw (holds the Microsoft Publisher import filter, libmspub),
#     Writer and Impress (for Word and PowerPoint files)
#   - libmspub-tools (pub2raw, for checking .pub files that will not open)
#   - Poppler tools (pdftoppm, pdfinfo) and fonts with the same letter widths
#     as Calibri and Cambria (Carlito, Caladea), so layouts match Office
#   - a Python virtual environment with the packages in requirements.txt
#
# Set VENV to choose where the virtual environment goes
# (default: ~/.venvs/publisher-rescue).
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${VENV:-$HOME/.venvs/publisher-rescue}"
SUDO=""
if [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi

echo "== Installing LibreOffice modules, tools and fonts"
export DEBIAN_FRONTEND=noninteractive
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq --no-install-recommends \
  libreoffice-draw libreoffice-writer libreoffice-impress libmspub-tools \
  poppler-utils fonts-crosextra-carlito fonts-crosextra-caladea \
  fonts-liberation fonts-dejavu-core python3-venv >/dev/null

echo "== Creating the Python environment in $VENV"
PYTHON="$(command -v python3.11 || command -v python3)"
"$PYTHON" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$KIT_DIR/requirements.txt"

echo "== Checking"
soffice --version | head -1
if [ -f /usr/lib/libreoffice/program/libwpftdrawlo.so ]; then
  echo "LibreOffice Draw with the Publisher filter: installed"
else
  echo "WARNING: LibreOffice Draw's import filters were not found; .pub files will not open."
fi
"$VENV/bin/python" -c "import docx, pptx, openpyxl, pymupdf, PIL; print('Python packages: OK')"

echo
echo "Done. Before running the scripts, start the environment with:"
echo "  source $VENV/bin/activate"
