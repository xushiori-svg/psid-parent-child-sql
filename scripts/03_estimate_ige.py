# Estimate the intergenerational elasticity (IGE) and the rank-rank slope.
# Run from the project folder: python scripts/03_estimate_ige.py

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

matched = pd.read_csv("data/clean/matched_sample.csv")
child_years = pd.read_csv("data/clean/child_income_years.csv")


def ols(y, x):
    # simple regression y = a + b*x, returns slope, robust standard error, n
    X = np.column_stack([np.ones(len(x)), x])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ beta
    n = len(y)
    bread = np.linalg.inv(X.T @ X)
    meat = X.T @ (X * (resid ** 2)[:, None])
    vcov = bread @ meat @ bread * n / (n - 2)
    return beta[1], np.sqrt(vcov[1, 1]), n


def log_ige(df, child_col, parent_col):
    # log(child income) = a + b * log(parent income)
    return ols(np.log(df[child_col].values), np.log(df[parent_col].values))


def rank_slope(df, child_col, parent_col):
    # child percentile rank = a + b * parent percentile rank
    # ranks go from 0 to 100 and are computed inside the sample used
    child_rank = df[child_col].rank(pct=True).values * 100
    parent_rank = df[parent_col].rank(pct=True).values * 100
    return ols(child_rank, parent_rank)


def income_at_age(age):
    # child income observed at this age (or one year later, since the PSID
    # is every two years after 1997); keep the first one for each child
    d = child_years[(child_years["age"] >= age) & (child_years["age"] <= age + 1)]
    d = d.sort_values(["child_id", "age", "year"]).drop_duplicates("child_id")
    return d[["child_id", "rel_income"]].rename(columns={"rel_income": f"c_inc_age{age}"})


# parents: need income in 1968 and at least 3 of the 5 years 1968-1972
parents_ok = matched[(matched["p_years"] >= 3) & matched["p_inc_1968"].notna()]

# 1. life-cycle pattern: child income measured at one age, from 25 to 45
rows = []
for age in range(25, 46):
    d = parents_ok.merge(income_at_age(age), on="child_id")
    col = f"c_inc_age{age}"
    b, se, n = log_ige(d, col, "p_inc_avg")
    r, rse, _ = rank_slope(d, col, "p_inc_avg")
    rows.append({"child_age": age, "log_ige": b, "log_ige_se": se,
                 "rank_slope": r, "rank_slope_se": rse, "n": n})
lifecycle = pd.DataFrame(rows)
lifecycle.to_csv(RESULTS_DIR / "lifecycle_estimates.csv", index=False)
print(lifecycle.round(3))

# 2. main table on one common sample
# children with income at age 27-28, at age 40-41, and at least 3 years at 35-44
common = (
    parents_ok[parents_ok["c_years"] >= 3]
    .merge(income_at_age(27), on="child_id")
    .merge(income_at_age(40), on="child_id")
)

specs = [
    ("Parent 1968 only", "Child at age 27", "p_inc_1968", "c_inc_age27"),
    ("Parent 1968 only", "Child at age 40", "p_inc_1968", "c_inc_age40"),
    ("Parent 1968-1972 average", "Child at age 27", "p_inc_avg", "c_inc_age27"),
    ("Parent 1968-1972 average", "Child at age 40", "p_inc_avg", "c_inc_age40"),
    ("Parent 1968 only", "Child age 35-44 average", "p_inc_1968", "c_inc_avg"),
    ("Parent 1968-1972 average", "Child age 35-44 average", "p_inc_avg", "c_inc_avg"),
]
table = []
for p_label, c_label, p_col, c_col in specs:
    b, se, n = log_ige(common, c_col, p_col)
    r, rse, _ = rank_slope(common, c_col, p_col)
    table.append({"parent_income": p_label, "child_income": c_label,
                  "log_ige": round(b, 3), "log_ige_se": round(se, 3),
                  "rank_slope": round(r, 3), "rank_slope_se": round(rse, 3),
                  "n": n})
table = pd.DataFrame(table)
table.to_csv(RESULTS_DIR / "ige_table.csv", index=False)
print(table)

# sample description
desc = pd.DataFrame({
    "item": ["Children matched to a parent (SQL)",
             "Parents with 1968 income and 3+ years in 1968-1972",
             "Common sample used in the main table",
             "Child birth years in common sample",
             "Mean parent age in 1968 (common sample)",
             "Mean years of child income at 35-44 (common sample)"],
    "value": [len(matched), len(parents_ok), len(common),
              f"{common['child_birth_year'].min():.0f}-{common['child_birth_year'].max():.0f}",
              round(common["parent_age_1968"].mean(), 1),
              round(common["c_years"].mean(), 1)],
})
desc.to_csv(RESULTS_DIR / "sample_description.csv", index=False)
print(desc)

# figure 1: estimates by the age when child income is measured
long_run_log = table.iloc[5]["log_ige"]
long_run_rank = table.iloc[5]["rank_slope"]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, col, ref, title in [
    (axes[0], "log_ige", long_run_log, "Log-log IGE"),
    (axes[1], "rank_slope", long_run_rank, "Rank-rank slope"),
]:
    lo = lifecycle[col] - 1.96 * lifecycle[col + "_se"]
    hi = lifecycle[col] + 1.96 * lifecycle[col + "_se"]
    ax.fill_between(lifecycle["child_age"], lo, hi, color="#2a6f97", alpha=0.15)
    ax.plot(lifecycle["child_age"], lifecycle[col], color="#2a6f97", marker="o",
            markersize=4, label="Child income from one year at this age")
    ax.axhline(ref, color="#c44536", linestyle="--",
               label="Child income averaged over ages 35-44")
    ax.set_title(title)
    ax.set_xlabel("Child age when income is measured")
    ax.set_ylim(0, 0.8)
    ax.set_xticks(range(25, 46, 5))
    ax.grid(alpha=0.3)
axes[0].set_ylabel("Estimated slope")
axes[0].legend(loc="lower right", fontsize=8.5, frameon=False)
fig.text(0.5, -0.02, "Parent income is the 1968-1972 average. Shaded band is the 95% confidence interval.",
         ha="center", fontsize=9, color="gray")
fig.tight_layout()
fig.savefig(RESULTS_DIR / "fig1_lifecycle.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# figure 2: binned scatter of child rank on parent rank (long-run measures)
d = common.copy()
d["parent_rank"] = d["p_inc_avg"].rank(pct=True) * 100
d["child_rank"] = d["c_inc_avg"].rank(pct=True) * 100
d["bin"] = pd.qcut(d["parent_rank"], 20, labels=False)
bins = d.groupby("bin")[["parent_rank", "child_rank"]].mean()
slope, _, _ = ols(d["child_rank"].values, d["parent_rank"].values)
intercept = d["child_rank"].mean() - slope * d["parent_rank"].mean()

fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(bins["parent_rank"], bins["child_rank"], color="#2a6f97", s=30)
xs = np.array([0, 100])
ax.plot(xs, intercept + slope * xs, color="#c44536",
        label=f"Slope = {slope:.2f}")
ax.plot(xs, xs, color="gray", linestyle=":", label="No mobility (slope = 1)")
ax.axhline(50, color="lightgray", linewidth=0.8)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_xlabel("Parent income rank (1968-1972 average)")
ax.set_ylabel("Child income rank (ages 35-44 average)")
ax.set_title("Child income rank by parent income rank")
ax.legend(frameon=False, loc="upper left")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(RESULTS_DIR / "fig2_rank_rank.png", dpi=200)
plt.close(fig)

print("Saved results to", RESULTS_DIR)
