#!/usr/bin/env bash
# Rebuild the blank templates and the portfolio sample (fictional Mossbyte Labs, Sprout S1).
# Also a quick end-to-end test of every script.
#
#   CRA_PY=<venv>/bin/python CRA_NPM_TOOLS=<npm folder> bash scripts/build_sample.sh
#
# Set CRA_TODAY=YYYY-MM-DD to pin the dates printed in the documents.
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${CRA_PY:-python3}"
S="$KIT/samples/mossbyte-sprout-s1"
OUT="$S/deliverables"
export CRA_TODAY="${CRA_TODAY:-$(date +%F)}"

echo "== Blank templates"
"$PY" "$KIT/scripts/fill_templates.py" --blank --out "$KIT/templates"
"$PY" "$KIT/scripts/make_gap_checklist.py" --out "$KIT/templates/cra-gap-checklist.xlsx"

echo "== Sample: SBOM"
rm -rf "$OUT"
mkdir -p "$OUT"
"$PY" "$KIT/scripts/make_sbom.py" "$S/source/sprout-cloud" "$S/source/sprout-companion" \
  --extra-components "$S/source/firmware-components.csv" \
  --client "$S/client.json" --product-type device --out "$OUT/sbom"
SBOM="$(ls "$OUT"/sbom/*.cdx.json | head -1)"

echo "== Sample: vulnerability report"
"$PY" "$KIT/scripts/vuln_report.py" "$SBOM" --node-project "$S/source/sprout-companion" \
  --client "$S/client.json" --out "$OUT"

echo "== Sample: documents"
"$PY" "$KIT/scripts/fill_templates.py" --client "$S/client.json" --out "$OUT" --only policy,runbook,support,handover

echo "== Sample: security.txt"
"$PY" "$KIT/scripts/make_security_txt.py" --client "$S/client.json" --out "$OUT/security.txt" > /dev/null
"$PY" "$KIT/scripts/make_security_txt.py" --check "$OUT/security.txt"

echo "== Sample: gap checklist"
"$PY" "$KIT/scripts/make_gap_checklist.py" --client "$S/client.json" --status "$S/gap-status.csv" \
  --out "$OUT/cra-gap-checklist.xlsx"

echo
echo "Done. Sample deliverables are in $OUT"
