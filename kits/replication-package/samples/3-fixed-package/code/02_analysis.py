"""Table 1 (baseline characteristics) and Table 2 (effect of the tutoring offer).

Reads:  data/derived/analysis_sample.csv
Writes: output/table1_summary_stats.csv, output/table2_main_results.csv
Based on the authors' code/analysis.py (J. Roe, May 2023). Only the file paths changed.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]  # the package's top folder
df = pd.read_csv(ROOT / "data" / "derived" / "analysis_sample.csv")

# ---------------------------------------------------------------
# Table 1: baseline characteristics by group
# ---------------------------------------------------------------
labels = {
    "baseline_math": "Baseline math score",
    "female": "Female",
    "low_income": "Low income",
    "grade": "Grade",
}
control = df[df["tutoring"] == 0]
treated = df[df["tutoring"] == 1]
rows = []
for var, label in labels.items():
    t = stats.ttest_ind(treated[var], control[var], equal_var=False)
    rows.append({
        "Variable": label,
        "Control mean": round(control[var].mean(), 3),
        "Control SD": round(control[var].std(), 3),
        "Tutoring mean": round(treated[var].mean(), 3),
        "Tutoring SD": round(treated[var].std(), 3),
        "Difference": round(treated[var].mean() - control[var].mean(), 3),
        "p-value": round(t.pvalue, 3),
    })
rows.append({"Variable": "Students", "Control mean": len(control), "Tutoring mean": len(treated)})
table1 = pd.DataFrame(rows)
table1.to_csv(ROOT / "output" / "table1_summary_stats.csv", index=False)


# ---------------------------------------------------------------
# Table 2: effect of the tutoring offer on endline math (SD units)
# ---------------------------------------------------------------
def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


specs = [
    "endline_z ~ tutoring",
    "endline_z ~ tutoring + baseline_z + female + low_income + C(grade)",
    "endline_z ~ tutoring + baseline_z + female + low_income + C(grade) + C(school_id)",
]
models = [smf.ols(f, data=df).fit(cov_type="cluster", cov_kwds={"groups": df["school_id"]})
          for f in specs]

names = {"tutoring": "Tutoring offer", "baseline_z": "Baseline score (z)",
         "female": "Female", "low_income": "Low income"}
table2 = []
for var, label in names.items():
    coef_row, se_row = [label], [""]
    for m in models:
        if var in m.params:
            coef_row.append(f"{m.params[var]:.3f}{stars(m.pvalues[var])}")
            se_row.append(f"({m.bse[var]:.3f})")
        else:
            coef_row += [""]
            se_row += [""]
    table2 += [coef_row, se_row]
table2.append(["Grade fixed effects", "No", "Yes", "Yes"])
table2.append(["School fixed effects", "No", "No", "Yes"])
table2.append(["Observations"] + [str(int(m.nobs)) for m in models])
table2.append(["R-squared"] + [f"{m.rsquared:.3f}" for m in models])
table2 = pd.DataFrame(table2, columns=["", "(1)", "(2)", "(3)"])
table2.to_csv(ROOT / "output" / "table2_main_results.csv", index=False)

print(table1)
print(table2)
print("mean gain:", np.round(df["gain"].mean(), 3))
