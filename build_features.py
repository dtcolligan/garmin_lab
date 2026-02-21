import os
import pandas as pd
import numpy as np

DATA_DIR = "data"
CLEAN_PATH = os.path.join(DATA_DIR, "clean", "daily_hybrid.csv")
OUT_DIR = os.path.join(DATA_DIR, "model")
os.makedirs(OUT_DIR, exist_ok=True)

def rolling_slope(y: pd.Series) -> float:
    """
    Slope of a linear fit over the window index [0..n-1].
    Returns NaN if not enough points.
    """
    y = pd.to_numeric(y, errors="coerce").dropna()
    n = len(y)
    if n < 4:
        return np.nan
    x = np.arange(n)
    # slope = cov(x,y)/var(x)
    return float(np.cov(x, y, bias=True)[0,1] / np.var(x))

def main():
    df = pd.read_csv(CLEAN_PATH)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)

    # Keep only dates where you actually have meaningful physiology
    key = ["sleep_total_hours", "resting_hr", "avg_overnight_hrv", "sleep_score"]
    df["has_core_data"] = df[key].notna().any(axis=1)

    first_valid = df.loc[df["has_core_data"], "date"].min()
    if pd.notna(first_valid):
        df = df[df["date"] >= first_valid].copy()

    feats = pd.DataFrame()
    feats["date"] = df["date"]
    feats["dow"] = df["date"].dt.dayofweek  # 0=Mon
    feats["week"] = df["date"].dt.isocalendar().week.astype(int)
    feats["month"] = df["date"].dt.month
    feats["days_since_start"] = (df["date"] - df["date"].min()).dt.days

    # Core signals
    for c in [
        "sleep_total_hours",
        "sleep_deep_hours",
        "sleep_rem_hours",
        "sleep_light_hours",
        "sleep_awake_hours",
        "sleep_score",
        "resting_hr",
        "avg_overnight_hrv",
        "avg_sleep_stress",
        "stress_avg",
        "body_battery_change",
    ]:
        if c in df.columns:
            feats[c] = pd.to_numeric(df[c], errors="coerce")

    # Rolling stats (7d) — only uses past days
    roll_cols = ["sleep_total_hours", "sleep_score", "resting_hr", "avg_overnight_hrv", "stress_avg"]
    for c in roll_cols:
        if c in feats.columns:
            feats[f"{c}_7d_mean"] = feats[c].rolling(7, min_periods=4).mean()
            feats[f"{c}_7d_std"] = feats[c].rolling(7, min_periods=4).std()
            feats[f"{c}_7d_slope"] = feats[c].rolling(7, min_periods=4).apply(rolling_slope, raw=False)

    # Targets (tomorrow)
    if "readiness_flag" in df.columns:
        feats["target_readiness_flag_tomorrow"] = df["readiness_flag"].shift(-1)

    feats["target_sleep_total_hours_tomorrow"] = feats["sleep_total_hours"].shift(-1) if "sleep_total_hours" in feats.columns else np.nan
    feats["target_resting_hr_tomorrow"] = feats["resting_hr"].shift(-1) if "resting_hr" in feats.columns else np.nan

    out_path = os.path.join(OUT_DIR, "daily_features.csv")
    feats.to_csv(out_path, index=False)
    print(f"Wrote {len(feats)} rows -> {out_path}")
    print("Columns:", len(feats.columns))

if __name__ == "__main__":
    main()

