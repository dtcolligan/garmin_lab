from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "clean"))

from health_model.daily_snapshot import DEFAULT_DB_PATH, generate_snapshot


class DailySnapshotNutritionScopingTest(unittest.TestCase):
    def test_generate_snapshot_scopes_nutrition_rows_to_requested_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export_dir = root / "export"
            export_dir.mkdir()

            (export_dir / "daily_summary_export.csv").write_text(
                "date,sleep_deep_sec,sleep_light_sec,sleep_rem_sec,sleep_awake_sec,sleep_score_overall,avg_sleep_respiration,awake_count,training_readiness_level,training_recovery_time_hours,training_readiness_sleep_pct,training_readiness_hrv_pct,training_readiness_stress_pct,training_readiness_load_pct,resting_hr,health_hrv_status,body_battery\n"
                "2026-04-08,3600,14400,5400,1200,82,14.2,2,HIGH,12,80,75,65,70,48,balanced,78\n"
            )
            (export_dir / "activities_export.csv").write_text("activity_id,start_time_local\n")

            db_path = root / "health_log.db"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE daily_summary (
                    user_id INTEGER NOT NULL,
                    date_for TEXT NOT NULL,
                    total_calories REAL,
                    total_protein_g REAL,
                    total_carbs_g REAL,
                    total_fat_g REAL,
                    total_fiber_g REAL,
                    meal_count INTEGER
                );

                CREATE TABLE meal_items (
                    user_id INTEGER NOT NULL,
                    date_for TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    calories REAL,
                    protein_g REAL,
                    carbs_g REAL,
                    fat_g REAL,
                    fiber_g REAL
                );
                """
            )
            conn.executemany(
                "INSERT INTO daily_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (1, "2026-04-08", 1800, 140, 170, 60, 28, 3),
                    (2, "2026-04-08", 2900, 210, 260, 110, 35, 4),
                ],
            )
            conn.executemany(
                "INSERT INTO meal_items VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (1, "2026-04-08", "Oats", 500, 20, 80, 10, 8),
                    (1, "2026-04-08", "Chicken Bowl", 700, 55, 60, 20, 6),
                    (1, "2026-04-08", "Yogurt", 300, 25, 20, 5, 0),
                    (2, "2026-04-08", "Burger", 1200, 40, 90, 70, 3),
                    (2, "2026-04-08", "Milkshake", 900, 15, 110, 35, 0)
                ],
            )
            conn.commit()
            conn.close()

            snapshot = generate_snapshot(
                export_dir=export_dir,
                gym_log_path=root / "missing_gym.json",
                db_path=db_path,
                target_date="2026-04-08",
                user_id=1,
            )

            self.assertEqual(snapshot.calories_kcal, 1800.0)
            self.assertEqual(snapshot.protein_g, 140.0)
            self.assertEqual(snapshot.carbs_g, 170.0)
            self.assertEqual(snapshot.fat_g, 60.0)
            self.assertTrue(snapshot.food_logged_bool)
            self.assertEqual(snapshot.nutrition_daily["source_name"], "health_log_sqlite_daily_summary")
            self.assertEqual(snapshot.nutrition_daily["source_record_id"], "nutrition:health_log_sqlite_daily_summary:day:2026-04-08")
            self.assertTrue(snapshot.nutrition_daily["provenance_record_id"].startswith("provenance_nutrition_daily_"))
            self.assertTrue(snapshot.nutrition_daily["nutrition_daily_id"].startswith("nutrition_daily_"))
            self.assertEqual(
                snapshot.nutrition_daily["top_meals_summary"],
                "Chicken Bowl (700 kcal), Oats (500 kcal), Yogurt (300 kcal)",
            )
            self.assertNotIn("Burger", snapshot.nutrition_daily["top_meals_summary"])
            self.assertNotIn("Milkshake", snapshot.nutrition_daily["top_meals_summary"])

    def test_default_db_path_points_to_live_pull_database(self) -> None:
        self.assertEqual(DEFAULT_DB_PATH.as_posix().rsplit("/", 3)[-3:], ["pull", "data", "health_log.db"])


if __name__ == "__main__":
    unittest.main()
