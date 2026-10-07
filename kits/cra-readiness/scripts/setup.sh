#!/usr/bin/env bash
# Install the tools the CRA readiness kit needs, without touching the system.
#
#   bash scripts/setup.sh                 # installs into ~/.cache/cra-readiness
#   bash scripts/setup.sh /some/folder    # installs into /some/folder
#
# Creates <folder>/venv (Python: cyclonedx-py, pip-audit, ...) and
# <folder>/npm (Node: cyclonedx-npm, cdxgen). Nothing is installed globally.
# You can also set CRA_VENV and CRA_NPM_TOOLS to choose each folder yourself.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="${1:-${CRA_TOOLS_DIR:-$HOME/.cache/cra-readiness}}"
VENV="${CRA_VENV:-$TOOLS_DIR/venv}"
NPM_DIR="${CRA_NPM_TOOLS:-$TOOLS_DIR/npm}"

command -v python3 >/dev/null || { echo "python3 is missing"; exit 1; }
command -v npm >/dev/null || { echo "npm is missing (install Node.js 20 or newer)"; exit 1; }

echo "Python tools -> $VENV"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/python" -m pip install --quiet -r "$KIT_DIR/requirements.txt"

echo "Node tools   -> $NPM_DIR"
mkdir -p "$NPM_DIR"
cp "$KIT_DIR/package.json" "$NPM_DIR/package.json"
(cd "$NPM_DIR" && npm install --no-audit --no-fund --omit=optional --loglevel=error)

echo
echo "Installed:"
echo "  cyclonedx-py  $("$VENV/bin/cyclonedx-py" --version)"
echo "  pip-audit     $("$VENV/bin/pip-audit" --version | awk '{print $2}')"
echo "  cyclonedx-npm $("$NPM_DIR/node_modules/.bin/cyclonedx-npm" --version)"
echo "  cdxgen        $("$NPM_DIR/node_modules/.bin/cdxgen" --version 2>/dev/null | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
echo
echo "Run the kit's scripts with this Python, for example:"
echo "  export CRA_PY=\"$VENV/bin/python\" CRA_NPM_TOOLS=\"$NPM_DIR\""
echo "  \"\$CRA_PY\" $KIT_DIR/scripts/make_sbom.py --help"
