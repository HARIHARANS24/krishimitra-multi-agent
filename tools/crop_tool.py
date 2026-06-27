"""
tools/crop_tool.py
====================
Crop suitability scoring used by the Crop Recommendation Agent.

The knowledge base below is a simplified, curated agronomic lookup
(soil x season suitability + rainfall tolerance band per crop). In a
production system this table would be backed by ICAR/state
agriculture department datasets; here it is intentionally explicit
and inspectable so every score is explainable.
"""

from __future__ import annotations

from dataclasses import dataclass

# crop -> { suitable_soils, suitable_seasons, rainfall_min_mm, rainfall_max_mm,
#           water_need_mm_per_week, typical_duration_days }
CROP_KNOWLEDGE_BASE: dict[str, dict] = {
    "Groundnut": {
        "soils": {"red", "sandy", "loamy", "black"},
        "seasons": {"kharif", "rabi"},
        "rainfall_range": (500, 1250),
        "water_need_mm_per_week": 25,
        "duration_days": 110,
        "demand_index": 0.78,
    },
    "Cotton": {
        "soils": {"black", "alluvial", "loamy"},
        "seasons": {"kharif"},
        "rainfall_range": (600, 1200),
        "water_need_mm_per_week": 30,
        "duration_days": 160,
        "demand_index": 0.72,
    },
    "Paddy": {
        "soils": {"alluvial", "clay", "loamy"},
        "seasons": {"kharif", "rabi"},
        "rainfall_range": (1000, 2500),
        "water_need_mm_per_week": 50,
        "duration_days": 130,
        "demand_index": 0.65,
    },
    "Millet": {
        "soils": {"red", "sandy", "laterite", "black"},
        "seasons": {"kharif", "rabi", "zaid"},
        "rainfall_range": (300, 900),
        "water_need_mm_per_week": 15,
        "duration_days": 90,
        "demand_index": 0.80,
    },
    "Sugarcane": {
        "soils": {"alluvial", "black", "loamy"},
        "seasons": {"kharif", "zaid"},
        "rainfall_range": (1000, 1800),
        "water_need_mm_per_week": 45,
        "duration_days": 365,
        "demand_index": 0.70,
    },
    "Banana": {
        "soils": {"alluvial", "loamy", "red"},
        "seasons": {"kharif", "rabi", "zaid", "summer"},
        "rainfall_range": (1200, 2200),
        "water_need_mm_per_week": 40,
        "duration_days": 300,
        "demand_index": 0.75,
    },
    "Pulses (Black Gram)": {
        "soils": {"black", "red", "loamy", "alluvial"},
        "seasons": {"rabi", "zaid"},
        "rainfall_range": (350, 750),
        "water_need_mm_per_week": 18,
        "duration_days": 75,
        "demand_index": 0.68,
    },
    "Maize": {
        "soils": {"alluvial", "red", "loamy", "black"},
        "seasons": {"kharif", "rabi"},
        "rainfall_range": (500, 1000),
        "water_need_mm_per_week": 22,
        "duration_days": 100,
        "demand_index": 0.74,
    },
    "Chilli": {
        "soils": {"black", "red", "loamy", "alluvial"},
        "seasons": {"kharif", "rabi"},
        "rainfall_range": (600, 1200),
        "water_need_mm_per_week": 28,
        "duration_days": 150,
        "demand_index": 0.71,
    },
    "Turmeric": {
        "soils": {"red", "black", "loamy"},
        "seasons": {"kharif"},
        "rainfall_range": (1000, 1500),
        "water_need_mm_per_week": 32,
        "duration_days": 270,
        "demand_index": 0.69,
    },
}


@dataclass
class CropScore:
    crop_name: str
    suitability_score: float  # 0-100
    factors: dict
    water_need_mm_per_week: float
    duration_days: int


def _rainfall_fit(rainfall_mm: float, rng: tuple[float, float]) -> float:
    lo, hi = rng
    if lo <= rainfall_mm <= hi:
        return 1.0
    spread = hi - lo
    if rainfall_mm < lo:
        deficit = lo - rainfall_mm
    else:
        deficit = rainfall_mm - hi
    # Linear falloff: fully out of range by the time deficit == spread.
    return max(0.0, 1.0 - (deficit / max(spread, 1)))


def score_crops(
    soil_type: str,
    season: str,
    rainfall_mm: float,
    top_n: int = 3,
) -> list[CropScore]:
    """Score every crop in the knowledge base against the farm's
    conditions and return the top N, each with a transparent factor
    breakdown for the explainability layer.
    """
    soil_type = soil_type.lower()
    season = season.lower()
    results: list[CropScore] = []

    for crop, info in CROP_KNOWLEDGE_BASE.items():
        soil_match = 1.0 if soil_type in info["soils"] else 0.25
        season_match = 1.0 if season in info["seasons"] else 0.1
        rainfall_match = _rainfall_fit(rainfall_mm, info["rainfall_range"])
        demand = info["demand_index"]

        # Weighted blend: agronomic fit matters most, demand is a tiebreaker.
        score = (
            soil_match * 35
            + season_match * 30
            + rainfall_match * 25
            + demand * 10
        )
        results.append(
            CropScore(
                crop_name=crop,
                suitability_score=round(score, 1),
                factors={
                    "soil_compatibility": round(soil_match * 100, 0),
                    "season_compatibility": round(season_match * 100, 0),
                    "rainfall_compatibility": round(rainfall_match * 100, 0),
                    "local_demand_index": round(demand * 100, 0),
                },
                water_need_mm_per_week=info["water_need_mm_per_week"],
                duration_days=info["duration_days"],
            )
        )

    results.sort(key=lambda r: r.suitability_score, reverse=True)
    return results[:top_n]
