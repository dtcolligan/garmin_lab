"""Persona spec dataclass + synthetic-evidence helpers.

A ``PersonaSpec`` is the declarative shape of a synthetic user. The
runner reads it, materialises a state DB + evidence stream, and drives
the `hai` pipeline against it.

This module is pure data + helpers — it does not touch the filesystem
or invoke subprocesses. The runner does that.
"""

from __future__ import annotations

import csv
import io
import math
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Literal, Optional


SexAtBirth = Literal["male", "female"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
GoalDirection = Literal[
    "maintenance", "fat_loss", "muscle_gain", "performance", "recomp"
]
DataSource = Literal["intervals_icu", "garmin", "manual_only", "mixed"]


@dataclass(frozen=True)
class StrengthSession:
    """A single recorded strength session for the persona's history."""

    date_offset_days: int
    """Days before as_of_date when the session happened (positive = past)."""
    session_type: str
    """e.g. 'strength_upper', 'strength_lower', 'strength_sbd'."""
    total_volume_kg: float
    """Sum of weight × reps across all sets, in kg."""
    rpe_avg: float = 7.5


@dataclass(frozen=True)
class RunSession:
    """A single recorded run session."""

    date_offset_days: int
    distance_m: float
    duration_s: int
    avg_hr: int
    feel: int = 3
    """Garmin-style 1–5 feel rating (3 = neutral)."""


@dataclass(frozen=True)
class CrossSession:
    """A non-impact cardio session (cycling, swim, row, etc.)."""

    date_offset_days: int
    kind: str
    """e.g. 'cycling', 'swimming', 'rowing'."""
    duration_s: int
    avg_hr: int


@dataclass(frozen=True)
class NutritionDay:
    """A single day's nutrition intake."""

    date_offset_days: int
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


@dataclass(frozen=True)
class WearableDay:
    """One day of synthetic wearable evidence (matches Garmin CSV schema subset)."""

    date_offset_days: int
    hrv_ms: Optional[float]
    resting_hr: Optional[int]
    sleep_hours: Optional[float]
    sleep_score: Optional[int]
    steps: int = 8000
    moderate_intensity_min: int = 0
    vigorous_intensity_min: int = 0
    body_battery: Optional[int] = None
    all_day_stress: Optional[int] = None
    acute_load: Optional[float] = None
    chronic_load: Optional[float] = None


@dataclass(frozen=True)
class PersonaSpec:
    """Declarative shape of a synthetic user persona."""

    persona_id: str
    """e.g. 'p1_dom_baseline'. Used for DB filename + log labels."""
    label: str
    """Short human label, e.g. 'Dom-baseline', 'Female marathoner'."""
    description: str
    """One-paragraph description of what this persona stresses."""

    age: int
    sex_at_birth: SexAtBirth
    weight_kg: float
    height_cm: int
    activity_level: ActivityLevel

    primary_goal: GoalDirection
    goal_description: str

    data_source: DataSource

    history_days: int
    """How many days of history to materialise before as_of_date."""

    weekly_strength_count: int
    weekly_running_count: int
    typical_strength_split: list[str] = field(default_factory=list)
    """e.g. ['strength_upper', 'strength_lower'] alternating."""

    sleep_window_target: Optional[tuple[str, str]] = None
    """(bed_time, wake_time) HH:MM 24-hour."""

    daily_kcal_target: Optional[int] = None
    daily_protein_target_g: Optional[int] = None

    typical_strength_volume_kg: float = 5000.0
    typical_run_distance_m: float = 8000.0
    typical_run_duration_s: int = 3000
    typical_run_avg_hr: int = 150

    typical_hrv_ms: float = 60.0
    typical_resting_hr: int = 55
    typical_sleep_hours: float = 7.5
    typical_sleep_score: int = 80

    cross_sessions_per_week: int = 0
    cross_kind: str = "cycling"

    sporadic_logging: bool = False
    """If True, ~30% of days have nutrition / readiness gaps."""
    history_gap_days: tuple[int, ...] = ()
    """Specific past offsets where there is NO wearable data (illness/vacation)."""

    today_planned_session: str = "rest"
    """planned_session_type token for as_of date."""
    today_soreness: str = "low"
    today_energy: str = "moderate"
    today_stress_score: int = 3

    recorded_strength_history: list[StrengthSession] = field(default_factory=list)
    recorded_run_history: list[RunSession] = field(default_factory=list)
    recorded_cross_history: list[CrossSession] = field(default_factory=list)
    recorded_nutrition_history: list[NutritionDay] = field(default_factory=list)

    def expected_bmr_kcal(self) -> float:
        """Mifflin-St Jeor, regardless of sex constant."""
        const = 5 if self.sex_at_birth == "male" else -161
        return (
            10.0 * self.weight_kg
            + 6.25 * self.height_cm
            - 5.0 * self.age
            + const
        )

    def expected_tdee_kcal(self) -> float:
        multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9,
        }
        return self.expected_bmr_kcal() * multipliers[self.activity_level]


# ---------------------------------------------------------------------------
# Synthetic wearable history generator
# ---------------------------------------------------------------------------

def synthesise_wearable_history(
    spec: PersonaSpec,
    as_of: date,
    seed: Optional[int] = None,
) -> list[WearableDay]:
    """Generate ``spec.history_days + 1`` ``WearableDay`` rows ending on as_of.

    Values are sampled around the persona's typical centroid with small
    daily noise. Specific offsets named in ``spec.history_gap_days`` are
    omitted entirely (illness / vacation gaps).
    """

    rng = random.Random(seed if seed is not None else hash(spec.persona_id) & 0xFFFF)
    rows: list[WearableDay] = []
    for offset in range(spec.history_days, -1, -1):
        if offset in spec.history_gap_days:
            continue
        if spec.data_source == "manual_only" and offset != 0:
            # Manual-only personas don't have wearable history beyond
            # whatever they manually log. as_of can still be present
            # as a "today's manual readiness" row.
            continue

        # Sporadic logging: ~30% of days have no readiness submitted, but
        # the wearable continues recording. We model that on the readiness
        # side, not here.
        hrv = _jitter(rng, spec.typical_hrv_ms, 4.5)
        rhr = int(round(_jitter(rng, spec.typical_resting_hr, 2.0)))
        sleep_h = _jitter(rng, spec.typical_sleep_hours, 0.7)
        sleep_score = int(round(_jitter(rng, spec.typical_sleep_score, 6.0)))

        # Acute / chronic load track the persona's training pattern.
        # Higher weekly session count → higher load centroids.
        weekly_load = (
            spec.weekly_running_count * 30.0
            + spec.weekly_strength_count * 25.0
            + spec.cross_sessions_per_week * 20.0
        )
        acute = max(2.0, _jitter(rng, weekly_load / 7.0, weekly_load / 30.0))
        chronic = max(2.0, _jitter(rng, weekly_load / 7.0, weekly_load / 60.0))

        rows.append(
            WearableDay(
                date_offset_days=offset,
                hrv_ms=round(hrv, 1),
                resting_hr=rhr,
                sleep_hours=round(sleep_h, 2),
                sleep_score=max(0, min(100, sleep_score)),
                acute_load=round(acute, 2),
                chronic_load=round(chronic, 2),
                body_battery=(
                    None
                    if spec.data_source in {"intervals_icu", "manual_only"}
                    else int(round(_jitter(rng, 55.0, 8.0)))
                ),
                all_day_stress=(
                    None
                    if spec.data_source in {"intervals_icu", "manual_only"}
                    else int(round(_jitter(rng, 28.0, 8.0)))
                ),
            )
        )
    return rows


def _jitter(rng: random.Random, centre: float, half_width: float) -> float:
    return centre + rng.uniform(-half_width, half_width)


# ---------------------------------------------------------------------------
# Garmin CSV serialiser
# ---------------------------------------------------------------------------

GARMIN_CSV_HEADER = (
    "date,steps,distance_m,active_kcal,total_kcal,moderate_intensity_min,"
    "vigorous_intensity_min,resting_hr,min_hr_day,max_hr_day,floors_ascended_m,"
    "all_day_stress,body_battery,avg_environment_altitude_m,sleep_deep_sec,"
    "sleep_light_sec,sleep_rem_sec,sleep_awake_sec,avg_sleep_respiration,"
    "avg_sleep_stress,awake_count,sleep_score_overall,sleep_score_quality,"
    "sleep_score_duration,sleep_score_recovery,training_readiness_level,"
    "training_recovery_time_hours,training_readiness_sleep_pct,"
    "training_readiness_hrv_pct,training_readiness_stress_pct,"
    "training_readiness_sleep_history_pct,training_readiness_load_pct,"
    "training_readiness_hrv_weekly_avg,training_readiness_valid_sleep,"
    "acute_load,chronic_load,acwr_status,acwr_status_feedback,"
    "training_status,training_status_feedback,health_hrv_value,"
    "health_hrv_status,health_hrv_baseline_low,health_hrv_baseline_high,"
    "health_hr_value,health_hr_status,health_hr_baseline_low,"
    "health_hr_baseline_high,health_spo2_value,health_spo2_status,"
    "health_spo2_baseline_low,health_spo2_baseline_high,"
    "health_skin_temp_c_value,health_skin_temp_c_status,"
    "health_skin_temp_c_baseline_low,health_skin_temp_c_baseline_high,"
    "health_respiration_value,health_respiration_status,"
    "health_respiration_baseline_low,health_respiration_baseline_high"
)


def render_garmin_csv(
    rows: list[WearableDay],
    as_of: date,
) -> str:
    """Render synthetic wearable rows as a Garmin daily-summary CSV string.

    Only the columns the projection layer reads are populated meaningfully;
    others are emitted as empty so the schema matches without inventing
    health-graded vendor fields.
    """

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(GARMIN_CSV_HEADER.split(","))
    for row in sorted(rows, key=lambda r: -r.date_offset_days):
        d = as_of - timedelta(days=row.date_offset_days)
        sleep_total_sec = (
            int(row.sleep_hours * 3600.0) if row.sleep_hours is not None else None
        )
        # Sleep stage breakdown — rough split typical in Garmin data
        if sleep_total_sec:
            deep = int(sleep_total_sec * 0.18)
            rem = int(sleep_total_sec * 0.20)
            awake = int(sleep_total_sec * 0.04)
            light = sleep_total_sec - deep - rem - awake
        else:
            deep = rem = awake = light = ""
        writer.writerow(
            [
                d.isoformat(),
                row.steps,
                row.steps * 0.8,  # naive distance estimate
                row.steps * 0.04,  # naive active kcal estimate
                "",
                row.moderate_intensity_min,
                row.vigorous_intensity_min,
                row.resting_hr if row.resting_hr is not None else "",
                "",
                "",
                "",
                row.all_day_stress if row.all_day_stress is not None else "",
                row.body_battery if row.body_battery is not None else "",
                "",
                deep,
                light,
                rem,
                awake,
                "",
                "",
                "",
                row.sleep_score if row.sleep_score is not None else "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                row.acute_load if row.acute_load is not None else "",
                row.chronic_load if row.chronic_load is not None else "",
                "",
                "",
                "",
                "",
                row.hrv_ms if row.hrv_ms is not None else "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )
    return buf.getvalue()


__all__ = [
    "PersonaSpec",
    "StrengthSession",
    "RunSession",
    "CrossSession",
    "NutritionDay",
    "WearableDay",
    "synthesise_wearable_history",
    "render_garmin_csv",
    "GARMIN_CSV_HEADER",
]
