"""Clean the tutoring pilot data.

Reads:  data/raw/tutoring_pilot.csv
Writes: data/derived/analysis_sample.csv
Based on the authors' code/clean_data.py (J. Doe, March 2023). Only the file paths changed.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]  # the package's top folder

raw = pd.read_csv(ROOT / "data" / "raw" / "tutoring_pilot.csv")

# keep students who took the endline test
df = raw[raw["endline_math"].notna()].copy()

# standardise scores with the control group mean and sd
for v in ["baseline_math", "endline_math"]:
    mu = df.loc[df["tutoring"] == 0, v].mean()
    sd = df.loc[df["tutoring"] == 0, v].std()
    df[v.replace("_math", "_z")] = (df[v] - mu) / sd

df["gain"] = df["endline_math"] - df["baseline_math"]

keep = ["student_id", "school_id", "grade", "female", "low_income", "tutoring",
        "baseline_math", "endline_math", "baseline_z", "endline_z", "gain"]
df[keep].to_csv(ROOT / "data" / "derived" / "analysis_sample.csv", index=False)
print("Saved", len(df), "students")
