"""P8 — Day-1 fresh install, female lifter (23yo, muscle gain)."""

from __future__ import annotations

from .base import PersonaSpec


SPEC = PersonaSpec(
    persona_id="p8_day1_female_lifter",
    label="Day-1 female lifter",
    description=(
        "23-year-old female, 58kg / 165cm, moderate-to-active. New lifter "
        "(3× strength per week, no running). Muscle gain priority. "
        "JUST INSTALLED — zero history, zero wearable. Stresses: cold "
        "start path, female + muscle gain (less common goal direction "
        "in implicit assumptions), fresh state DB, day-1 UX. Highest "
        "expected new-bug yield in the matrix."
    ),
    age=23,
    sex_at_birth="female",
    weight_kg=58.0,
    height_cm=165,
    activity_level="moderate",
    primary_goal="muscle_gain",
    goal_description="Muscle gain — new lifter, building base strength",
    data_source="manual_only",
    history_days=0,  # day-1 fresh install
    weekly_strength_count=3,
    weekly_running_count=0,
    typical_strength_split=[
        "strength_lower",
        "strength_upper",
        "strength_sbd",
    ],
    sleep_window_target=("23:00", "07:00"),
    daily_kcal_target=2200,
    daily_protein_target_g=120,
    typical_strength_volume_kg=2200.0,
    typical_hrv_ms=55.0,
    typical_resting_hr=62,
    typical_sleep_hours=7.5,
    typical_sleep_score=80,
    today_planned_session="strength_lower",
    today_soreness="low",
    today_energy="high",
    today_stress_score=2,
    # No recorded history — this is day 1.
    recorded_strength_history=[],
    recorded_run_history=[],
    recorded_cross_history=[],
    recorded_nutrition_history=[],
)
