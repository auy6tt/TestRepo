"""Figure 1: endline math score by baseline quintile, tutoring offer vs control.

Reads:  data/derived/analysis_sample.csv
Writes: output/figure1_scores_by_baseline.png
Based on the authors' code/figure1.py. Only the file paths changed.
"""
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]  # the package's top folder
df = pd.read_csv(ROOT / "data" / "derived" / "analysis_sample.csv")
df["baseline_quintile"] = pd.qcut(df["baseline_math"], 5, labels=[1, 2, 3, 4, 5])
means = (df.groupby(["baseline_quintile", "tutoring"], observed=True)["endline_math"]
           .mean().unstack())

INK, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#e1e0d9", "#c3c2b7"
series = [(1, "Tutoring offer", "#2a78d6"), (0, "Control", "#eb6834")]

fig, ax = plt.subplots(figsize=(6.5, 4))
x = means.index.astype(int)
for group, label, color in series:
    y = means[group]
    ax.plot(x, y, color=color, linewidth=1.8, marker="o", markersize=7,
            markeredgecolor="white", markeredgewidth=1.5, label=label, zorder=3)
    ax.annotate(f"{label}: {y.iloc[-1]:.1f}", xy=(x[-1], y.iloc[-1]),
                xytext=(10, 0), textcoords="offset points", va="center",
                fontsize=9, color=INK)

ax.set_title("Endline math score by baseline score quintile", loc="left",
             fontsize=11, color=INK)
ax.set_xlabel("Baseline math score quintile (1 = lowest)", color=MUTED)
ax.set_ylabel("Mean endline math score (0-100)", color=MUTED)
ax.set_xticks(list(x))
ax.set_xlim(0.7, 6.2)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
for side in ["left", "bottom"]:
    ax.spines[side].set_color(AXIS)
ax.spines["bottom"].set_bounds(1, 5)
ax.tick_params(colors=MUTED, labelsize=9)
ax.legend(frameon=False, loc="upper left", fontsize=9)
fig.tight_layout()
fig.savefig(ROOT / "output" / "figure1_scores_by_baseline.png", dpi=200)
