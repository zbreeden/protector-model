# -----------------------------------------
# 1) Imports & Environment Info
# -----------------------------------------

import sys 
import os 
from pathlib import Path 
import pandas as pd # for data handling
import numpy as np # for numerical operations
import matplotlib.pyplot as plt # for plotting

# Make pandas prints friendlier.
pd.set_option("display.max.columns", 100) # show up to 100 columns when printing dataframes
pd.set_option("display.width", 160) # set display width to 160 characters

# Print environment info for reproducibility.
print({
	"python": sys.version,
	"numpy": np.__version__,
	"pandas": pd.__version__,
})

# -----------------------------------------
# 2) Paths & Dataset Config
# -----------------------------------------

CSV_PATH = Path("../FourTwentyAnalytics/protector-model/data/external/creditcard.csv")
print("CSV_PATH ->", CSV_PATH.resolve()) # print resolved path

expected_cols = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
assert CSV_PATH.exists(), f"CSV not found at {CSV_PATH.resolve()} — fix CSV_PATH above." # fail early

# -----------------------------------------
# 3) Load CSV (memory-friendly) with basic dtype (data type) hints
# -----------------------------------------

df = pd.read_csv(CSV_PATH, low_memory=False) #, delimiter=",", encoding="utf-8")

print("Initial dataframe shape:", df.shape) # print shape of dataframe - document shape
print("Dataframe columns:", df.columns.tolist()) # print list of columns - document columns
print("Dataframe dtypes:\n", df.dtypes) # print data types of each column - document dtypes (data types)
print("First 3 rows of the dataframe:\n", df.head(3)) # show first 3 rows of the dataframe

# -----------------------------------------
# 4) Sanity Checks (nulls, duplicates, target distribution)
# -----------------------------------------

# 4.1) Missing values
null_counts = df.isna().sum().sort_values(ascending=False)
print("Missing values (top 10):")
print(null_counts.head(10)) # expected to be zero for all columns in this dataset

# 4.2a) Duplicates (row-level exact dupes)
dup_count = df.duplicated().sum()
print(f"Exact duplicate rows: {dup_count}")

# 4.2b) Remove duplicates (if any)
if dup_count > 0:
	df = df.drop_duplicates().reset_index(drop=True)
	print("Dataframe shape after removing duplicates:", df.shape) # print new shape after deduplication - document new shape

# 4.3) Target distribution — a classic dataset is VERY imbalanced.
if "Class" in df.columns:
    target_counts = df["Class"].value_counts(dropna=False).sort_index()
    target_ratio = target_counts / len(df)
    print("Target counts:\n", target_counts.to_string())
    print("Target ratios:\n", (target_ratio*100).round(4).astype(str) + "%")
else:
    print("Column 'Class' not found — confirm your dataset's target column name.")

# -----------------------------------------
# 5) Basic Descriptives
# -----------------------------------------

desc = df.describe(include="all", percentiles=[0.01, 0.25, 0.5, 0.75, 0.99]).T
print("Descriptive statistics:\n", desc) # print descriptive statistics - document descriptives

export_path = CSV_PATH.parent / "creditcard_descriptives.csv" # define export path for descriptives
desc.to_csv(export_path, index=True) # export descriptives to CSV
print(f"Descriptive statistics exported to {export_path.resolve()}") # confirm export path

# -----------------------------------------
# 6) Basic Univariate Plots (UI-friendly exports)
# -----------------------------------------
from pathlib import Path
import matplotlib.pyplot as plt

# Where to save images (keep consistent with your UI paths)
PLOT_DIR = CSV_PATH.parent  # e.g., .../protector-model/data/external
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# Helper to export crisp PNGs (no transparency; high DPI)
def save_figure(fig, name: str):
    out = PLOT_DIR / f"{name}.png"  # use .png for web
    fig.savefig(
        out,
        dpi=300,               # crisp text in UI
        bbox_inches="tight",   # trims extra margins
        facecolor="white",     # solid background (no alpha)
        edgecolor="none"
    )
    plt.close(fig)             # free memory / avoid overlaps
    print(f"Saved plot -> {out.resolve()}")

# Sample for plotting if very large
sample = df.sample(n=min(100_000, len(df)), random_state=42) if len(df) > 100_000 else df

# 6.1) Amount distribution
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(sample["Amount"], bins=50, alpha=0.9)
ax.set_title("Transaction Amount — Distribution")
ax.set_xlabel("Amount")
ax.set_ylabel("Frequency")
ax.grid(True, alpha=0.25)
save_figure(fig, "amount_distribution")  # writes .../amount_distribution.png

# 6.2) Time distribution (if present)
if "Time" in sample.columns:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(sample["Time"], bins=50, alpha=0.9)
    ax.set_title("Transaction Time — Distribution")
    ax.set_xlabel("Time (seconds since first tx)")
    ax.set_ylabel("Frequency")
    ax.grid(True, alpha=0.25)
    save_figure(fig, "time_distribution")

# 6.3) Class distribution
if "Class" in df.columns:
    counts = sample["Class"].value_counts().sort_index()
    # materialize counts as a concrete NumPy int array to avoid ExtensionArray typing issues
    heights = counts.to_numpy().astype(int)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(counts.index.astype(str), heights, alpha=0.9)
    ax.set_title("Transaction Class — Distribution")
    ax.set_xlabel("Class")
    ax.set_ylabel("Count")
    for i, v in enumerate(heights):
        ax.text(i, int(v), f"{int(v):,}", ha="center", va="bottom", fontsize=9)
    ax.grid(True, axis="y", alpha=0.25)
    save_figure(fig, "class_distribution")


# -----------------------------------------
# 7) Quick Correlation Peek (subset)
# -----------------------------------------

subset_cols = [c for c in df.columns if c.startswith("V")][:8] + ["Amount", "Class"]
subset_cols = [c for c in subset_cols if c in df.columns]
if len(subset_cols) >= 2:
    corr = df[subset_cols].corr(numeric_only=True)
    print("Correlation (subset):\n", corr.round(3))
    # Simple image-less view; for matrices, printing numeric is often more helpful than a heatmap wall.

    export_path = CSV_PATH.parent / "correlation_subset.csv" # define export path for correlation
    corr.to_csv(export_path, index=True) # export correlation to CSV
    print(f"Correlation subset exported to {export_path.resolve()}") # confirm export path
else:
    print("Not enough numeric columns found for correlation subset.")
    # No correlation file exported because not enough numeric columns were found.

# Save a compact cleaned artifact next to the raw file.

clean = df.copy()
# Drop any columns that are completely null to keep the artifact small and reset the index.
clean = clean.dropna(axis=1, how="all").reset_index(drop=True)

out_path = CSV_PATH.with_name(CSV_PATH.stem + "_clean.parquet")
try:
    clean.to_parquet(out_path, index=False)
    print("Wrote cleaned dataset ->", out_path.resolve())
except (ImportError, ValueError, OSError) as err:
    # pandas.to_parquet raises ValueError when no engine is available
    # catching ImportError/OSError covers installation/system errors too
    print(f"Parquet write failed (maybe pyarrow/fastparquet not installed). Falling back to CSV. Error: {err}")
    out_path = CSV_PATH.with_name(CSV_PATH.stem + "_clean.csv")
    clean.to_csv(out_path, index=False)
    print("Wrote cleaned dataset ->", out_path.resolve())

print(clean.head(3))


# -----------------------------------------
# 10) Baseline Model Hook — Logistic Regression (clean version)
# -----------------------------------------
# Purpose:
# - Quick "does this pipeline have signal?" check
# - Keep it simple, fast, and explainable
# - Save a portable model artifact for the interview

# ---- Imports (grouped up front) ----
from pathlib import Path
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# ---- Config (edit paths if needed) ----
ARTIFACT_DIR = Path("../FourTwentyAnalytics/protector-model/data/external")  # <- adjust if you want
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)  # make sure path exists
MODEL_PATH = ARTIFACT_DIR / "baseline_fraud_model.joblib"
SCORED_PATH = ARTIFACT_DIR / "transactions_with_scores.parquet"  # optional: for PBI

# ---- Sanity guard: do we have the target? ----
if "Class" not in df.columns:
    raise ValueError("Target column 'Class' not found — confirm your label field name.")

# ---- Split features/target ----
# We drop only the target; leave all other columns in for a quick baseline.
X = df.drop(columns=["Class"], errors="ignore")
y = df["Class"]

# Stratify to preserve the extreme class imbalance in both train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42
)

# ---- Model (simple, robust defaults) ----
# Notes:
# - class_weight='balanced' handles the 0.17% prevalence without resampling
# - max_iter bumped to avoid "reached limit" warnings
# - solver='lbfgs' is fine here; 'saga' also works if you run into convergence issues
model = LogisticRegression(
    max_iter=5000,
    class_weight="balanced",
    solver="lbfgs",
    n_jobs=-1  # harmless if ignored; speeds up some solvers
)

# ---- Fit ----
model.fit(X_train, y_train)

# ---- Evaluate at default 0.50 threshold (quick read) ----
preds = model.predict(X_test)
print("Baseline Logistic Regression Report (threshold=0.50):")
print(classification_report(y_test, preds, digits=4))

# ---- Save model artifact (kept close to training to avoid scope issues) ----
joblib.dump(model, MODEL_PATH)
print(f"Saved baseline model -> {MODEL_PATH.resolve()}")

# ---- Optional: export probabilities for Power BI threshold demo ----
from pathlib import Path

try:
    proba = model.predict_proba(X_test)[:, 1]
    scored = X_test.copy()
    scored["Class"] = y_test.values
    scored["proba"] = proba

    # Define output paths
    SCORED_PATH = Path(CSV_PATH.parent / "transactions_with_scores.parquet")
    CSV_EXPORT_PATH = SCORED_PATH.with_suffix(".csv")

    # Try Parquet first (compact, faster)
    try:
        scored.to_parquet(SCORED_PATH, index=False)
        print(f"Saved scored transactions -> {SCORED_PATH.resolve()}")
    except Exception as e:
        print(f"Parquet export failed ({e}). Skipping to CSV fallback.")

    # Always export CSV for Power BI
    scored.to_csv(CSV_EXPORT_PATH, index=False)
    print(f"Saved scored transactions CSV -> {CSV_EXPORT_PATH.resolve()}")

except Exception as e:
    print("Skipped probability export (predict_proba unavailable).", e)


# -----------------------------------------
# Export simple KPI metrics
# -----------------------------------------
import json
from sklearn.metrics import precision_score, recall_score, f1_score

# Evaluate at default 0.5 threshold
proba = model.predict_proba(X_test)[:, 1]
preds = (proba >= 0.5).astype(int)

metrics = {
    "precision": float(precision_score(y_test, preds)),
    "recall": float(recall_score(y_test, preds)),
    "f1": float(f1_score(y_test, preds)),
    "threshold": 0.5,
    "n_samples": len(y_test),
    "timestamp": pd.Timestamp.now().isoformat()
}

SIGNAL_DIR = Path("../FourTwentyAnalytics/protector-model/signals/")

metrics_path = SIGNAL_DIR / "baseline_metrics.json"
with open(metrics_path, "w") as f:
    json.dump(metrics, f, indent=2)

print(f"Saved baseline metrics -> {metrics_path.resolve()}")


# -----------------------------------------
# End of Script
# -----------------------------------------