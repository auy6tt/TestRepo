#!/usr/bin/env bash
# One-time setup for the document accessibility kit (Linux, including Claude Code cloud sessions).
#
#   bash kits/doc-accessibility/scripts/setup.sh             Python packages and system tools
#   bash kits/doc-accessibility/scripts/setup.sh --verapdf   also download veraPDF (needs Java and Maven)
#   bash kits/doc-accessibility/scripts/setup.sh --no-apt    skip system packages (if you have no sudo)
#
# Settings (environment variables):
#   DOC_A11Y_VENV  where to make the Python virtual environment (default: ~/.venvs/doc-accessibility)
#   VERAPDF_DIR    where to put veraPDF (default: ~/.cache/doc-accessibility/verapdf)
#
# Cloud sessions start from a clean machine, so run this at the start of each
# session, or put it in your environment's setup script.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${DOC_A11Y_VENV:-$HOME/.venvs/doc-accessibility}"
VERAPDF_DIR="${VERAPDF_DIR:-$HOME/.cache/doc-accessibility/verapdf}"
VERAPDF_VERSION="${VERAPDF_VERSION:-1.28.2}"
WANT_APT=1
WANT_VERAPDF=0
for arg in "$@"; do
  case "$arg" in
    --no-apt) WANT_APT=0 ;;
    --verapdf) WANT_VERAPDF=1 ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

# 1. System tools: LibreOffice Writer (Word to tagged PDF), Tesseract and Ghostscript (OCR).
#    Some machines have LibreOffice without its Writer part; conversions then fail
#    with "source file could not be loaded".
if [ "$WANT_APT" = 1 ] && command -v apt-get >/dev/null 2>&1; then
  SUDO=""
  if [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi
  echo "Installing system tools (libreoffice-writer, tesseract-ocr, ghostscript)..."
  $SUDO apt-get update -qq || echo "apt-get update failed; trying the install anyway."
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq --no-install-recommends \
      libreoffice-writer tesseract-ocr ghostscript \
    || echo "Could not install some system tools. OCR or Word-to-PDF conversion may not work."
elif [ "$WANT_APT" = 1 ]; then
  echo "No apt-get on this machine. Install LibreOffice and Tesseract yourself"
  echo "(Mac: brew install --cask libreoffice && brew install tesseract ghostscript)."
fi

# 2. Python packages, in their own virtual environment.
echo "Setting up Python packages in $VENV ..."
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$KIT_DIR/requirements.txt"

# 3. veraPDF (optional): the free PDF/UA validator, fetched from Maven Central.
if [ "$WANT_VERAPDF" = 1 ]; then
  MVN="$(command -v mvn || true)"
  if [ -z "$MVN" ] && [ -x /opt/maven/bin/mvn ]; then MVN=/opt/maven/bin/mvn; fi
  if [ -n "$MVN" ] && command -v java >/dev/null 2>&1; then
    echo "Downloading veraPDF $VERAPDF_VERSION into $VERAPDF_DIR ..."
    POM_DIR="$(mktemp -d)"
    cat > "$POM_DIR/pom.xml" <<EOF
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>local</groupId>
  <artifactId>verapdf-download</artifactId>
  <version>1</version>
  <packaging>pom</packaging>
  <dependencies>
    <dependency>
      <groupId>org.verapdf.apps</groupId>
      <artifactId>greenfield-apps</artifactId>
      <version>$VERAPDF_VERSION</version>
    </dependency>
  </dependencies>
</project>
EOF
    mkdir -p "$VERAPDF_DIR/lib"
    "$MVN" -q -B -f "$POM_DIR/pom.xml" dependency:copy-dependencies -DoutputDirectory="$VERAPDF_DIR/lib"
    rm -rf "$POM_DIR"
  else
    echo "veraPDF needs Java and Maven, and one of them is missing."
    echo "On your own computer, install veraPDF from https://verapdf.org/ and set VERAPDF_DIR to its folder."
  fi
fi

# 4. What is ready?
echo
echo "Python for the scripts: $VENV/bin/python"
for tool in soffice tesseract gs java; do
  if command -v "$tool" >/dev/null 2>&1; then echo "  found $tool"; else echo "  missing $tool"; fi
done
if [ -d "$VERAPDF_DIR/lib" ] && ls "$VERAPDF_DIR/lib"/*.jar >/dev/null 2>&1; then
  echo "  found veraPDF in $VERAPDF_DIR"
else
  echo "  veraPDF not installed (optional: run this script with --verapdf)"
fi
