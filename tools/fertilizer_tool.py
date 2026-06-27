"""
tools/fertilizer_tool.py
==========================
Fertilizer & nutrient (N-P-K) recommendation used by the Fertilizer
Agent. Values are simplified per-acre guidelines adapted from common
Indian state agriculture department package-of-practice tables, split
across growth stages.
"""

from __future__ import annotations

from dataclasses import dataclass

# crop -> total NPK requirement in kg/acre, and stage split ratios.
FERTILIZER_KNOWLEDGE_BASE: dict[str, dict] = {
    "Groundnut": {"n": 8, "p": 16, "k": 16, "stage_split": {"basal": 1.0, "flowering": 0.0, "pod_filling": 0.0}},
    "Cotton": {"n": 40, "p": 20, "k": 20, "stage_split": {"basal": 0.4, "flowering": 0.3, "pod_filling": 0.3}},
    "Paddy": {"n": 48, "p": 24, "k": 24, "stage_split": {"basal": 0.5, "flowering": 0.25, "pod_filling": 0.25}},
    "Millet": {"n": 16, "p": 8, "k": 0, "stage_split": {"basal": 0.6, "flowering": 0.4, "pod_filling": 0.0}},
    "Sugarcane": {"n": 100, "p": 40, "k": 40, "stage_split": {"basal": 0.3, "flowering": 0.4, "pod_filling": 0.3}},
    "Banana": {"n": 80, "p": 32, "k": 120, "stage_split": {"basal": 0.25, "flowering": 0.35, "pod_filling": 0.40}},
    "Pulses (Black Gram)": {"n": 6, "p": 16, "k": 8, "stage_split": {"basal": 1.0, "flowering": 0.0, "pod_filling": 0.0}},
    "Maize": {"n": 48, "p": 24, "k": 16, "stage_split": {"basal": 0.5, "flowering": 0.3, "pod_filling": 0.2}},
    "Chilli": {"n": 40, "p": 20, "k": 20, "stage_split": {"basal": 0.3, "flowering": 0.4, "pod_filling": 0.3}},
    "Turmeric": {"n": 30, "p": 20, "k": 40, "stage_split": {"basal": 0.4, "flowering": 0.3, "pod_filling": 0.3}},
}

# Soil-type nutrient adjustment factors (heuristic): sandy soils leach
# nutrients faster (need slightly more), clay/black soils retain more.
SOIL_ADJUSTMENT = {
    "sandy": 1.15,
    "red": 1.05,
    "laterite": 1.10,
    "alluvial": 1.0,
    "loamy": 0.95,
    "black": 0.90,
    "clay": 0.90,
    "saline": 1.10,
}

GROWTH_STAGES = ["basal", "flowering", "pod_filling"]


@dataclass
class FertilizerPlan:
    crop_name: str
    soil_type: str
    total_n_kg: float
    total_p_kg: float
    total_k_kg: float
    stage_breakdown: list[dict]
    explanation: list[str]


def recommend_fertilizer(crop_name: str, soil_type: str, growth_stage: str | None = None) -> FertilizerPlan:
    base = FERTILIZER_KNOWLEDGE_BASE.get(crop_name)
    if base is None:
        base = {"n": 30, "p": 20, "k": 20, "stage_split": {"basal": 0.5, "flowering": 0.3, "pod_filling": 0.2}}
        note_unknown = True
    else:
        note_unknown = False

    adj = SOIL_ADJUSTMENT.get(soil_type.lower(), 1.0)
    total_n = round(base["n"] * adj, 1)
    total_p = round(base["p"] * adj, 1)
    total_k = round(base["k"] * adj, 1)

    stage_breakdown = []
    for stage in GROWTH_STAGES:
        frac = base["stage_split"].get(stage, 0.0)
        if frac == 0:
            continue
        stage_breakdown.append(
            {
                "stage": stage,
                "n_kg_per_acre": round(total_n * frac, 1),
                "p_kg_per_acre": round(total_p * frac, 1),
                "k_kg_per_acre": round(total_k * frac, 1),
            }
        )

    explanation = [
        f"Base NPK requirement for {crop_name}: N={base['n']}, P={base['p']}, K={base['k']} kg/acre.",
        f"Adjusted by soil factor x{adj} for '{soil_type}' soil (sandy/laterite soils need more due to "
        f"nutrient leaching; clay/black soils retain nutrients better and need less).",
    ]
    if note_unknown:
        explanation.append(
            f"'{crop_name}' was not found in the curated knowledge base; generic balanced NPK values were used. "
            "Consult a local agronomist or Soil Health Card for a precise recommendation."
        )
    if growth_stage and growth_stage not in GROWTH_STAGES:
        explanation.append(f"Growth stage '{growth_stage}' not recognized; showing the full-cycle plan.")
    elif growth_stage:
        explanation.append(f"Highlighting the dose specifically needed for the '{growth_stage}' stage.")

    return FertilizerPlan(
        crop_name=crop_name,
        soil_type=soil_type,
        total_n_kg=total_n,
        total_p_kg=total_p,
        total_k_kg=total_k,
        stage_breakdown=stage_breakdown,
        explanation=explanation,
    )
