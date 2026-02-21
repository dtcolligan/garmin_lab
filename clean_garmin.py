import os
import pandas as pd

DATA_DIR = "data"
OUT_DIR = os.path.join(DATA_DIR, "clean")
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    df = pd.read_csv(os.path.join(DATA_DIR, "daily_metrics_daily.csv"))

    clean = pd.DataFrame()
    clean["date"] = pd.to_datetime(df["date"], errors="coerce")

    # --- Sleep ---
    clean["sleep_total_hours"] = df["sleep.dailySleepDTO.sleepTimeSeconds"] / 3600
    clean["sleep_deep_hours"] = df["sleep.dailySleepDTO.deepSleepSeconds"] / 3600
    clean["sleep_rem_hours"] = df["sleep.dailySleepDTO.remSleepSeconds"] / 3600
    clean["sleep_light_hours"] = df["sleep.dailySleepDTO.lightSleepSeconds"] / 3600
    clean["sleep_awake_hours"] = df["sleep.dailySleepDTO.awakeSleepSeconds"] / 3600
    clean["sleep_score"] = df["sleep.dailySleepDTO.sleepScores.overall.value"]

    # --- Recovery ---
    clean["resting_hr"] = df["sleep.restingHeartRate"]
    clean["avg_sleep_stress"] = df["sleep.dailySleepDTO.avgSleepStress"]
    clean["avg_overnight_hrv"] = df["sleep.avgOvernightHrv"]
    clean["body_battery_change"] = df["sleep.bodyBatteryChange"]

    # --- Stress ---
    if "stress.avgStressLevel" in df.columns:
        clean["stress_avg"] = df["stress.avgStressLevel"]

    # --- RHR fallback ---
    if "rhr.restingHeartRate" in df.columns:
        clean["resting_hr"] = df["rhr.restingHeartRate"]

    # --- Performance ---
    if "max_metrics.vo2Max" in df.columns:
        clean["vo2max"] = df["max_metrics.vo2Max"]

    if "training_readiness.score" in df.columns:
        clean["training_readiness"] = df["training_readiness.score"]

    if "training_status.trainingStatus" in df.columns:
        clean["training_status"] = df["training_status.trainingStatus"]

    if "endurance_score.score" in df.columns:
        clean["endurance_score"] = df["endurance_score.score"]

    # --- Derived 7-day averages ---
    for col in [
        "sleep_total_hours",
        "resting_hr",
        "avg_overnight_hrv",
        "stress_avg",
        "training_readiness"
    ]:
        if col in clean.columns:
            clean[f"{col}_7d_avg"] = clean[col].rolling(7, min_periods=3).mean()

    # --- Readiness flag ---
    def flag(row):
        r = row.get("training_readiness")
        s = row.get("sleep_total_hours")
        h = row.get("resting_hr")

        if pd.notna(r) and r < 50:
            return "red"
        if pd.notna(s) and s < 6:
            return "red"
        if pd.notna(r) and r >= 75 and pd.notna(s) and s >= 7:
            return "green"
        return "amber"

    clean["readiness_flag"] = clean.apply(flag, axis=1)

    out_path = os.path.join(OUT_DIR, "daily_hybrid.csv")
    clean.to_csv(out_path, index=False)

    print(f"Wrote {len(clean)} rows -> {out_path}")
    print("\nNon-null counts:")
    print(clean.notna().sum().sort_values(ascending=False))

if __name__ == "__main__":
    main()
