# Clean the tutoring pilot data
# JD, March 2023. Raw file was first saved on D:\projects\tutoring\raw (old laptop)
import os
import pandas as pd

os.chdir("C:/Users/jdoe/Dropbox/tutoring-paper")

raw = pd.read_csv("C:/Users/jdoe/Dropbox/tutoring-paper/data/raw/tutoring_pilot.csv")

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
df[keep].to_csv("data/derived/analysis_sample.csv", index=False)
print("Saved", len(df), "students")
