"""Appendix Table A1: attrition (missing endline test) by group.

Reads:  data/raw/tutoring_pilot.csv
Writes: output/tableA1_attrition.csv
This program was missing from the package as first deposited. The authors supplied it
on request (J. Doe, June 2023). Only the file paths changed.
"""
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]  # the package's top folder
raw = pd.read_csv(ROOT / "data" / "raw" / "tutoring_pilot.csv")
raw["missing_endline"] = raw["endline_math"].isna().astype(int)

m = smf.ols("missing_endline ~ tutoring", data=raw).fit(
    cov_type="cluster", cov_kwds={"groups": raw["school_id"]})

rows = []
for g, label in [(0, "Control"), (1, "Tutoring offer")]:
    sub = raw[raw["tutoring"] == g]
    rows.append({
        "Group": label,
        "Students assigned": len(sub),
        "Took endline test": int((sub["missing_endline"] == 0).sum()),
        "Share missing": round(sub["missing_endline"].mean(), 3),
    })
rows.append({
    "Group": "Difference (tutoring - control)",
    "Share missing": round(m.params["tutoring"], 3),
})
rows.append({
    "Group": "p-value (clustered by school)",
    "Share missing": round(m.pvalues["tutoring"], 3),
})
pd.DataFrame(rows).to_csv(ROOT / "output" / "tableA1_attrition.csv", index=False)
