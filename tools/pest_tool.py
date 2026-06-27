"""
tools/pest_tool.py
====================
Pest & disease risk lookup used by the Pest and Disease Agent.

Knowledge is keyed by crop and indexed by current weather conditions
(humidity / rainfall raise risk for fungal disease; dry heat raises
risk for certain insect pests), reflecting common agronomic patterns.
"""

from __future__ import annotations

from dataclasses import dataclass

PEST_KNOWLEDGE_BASE: dict[str, list[dict]] = {
    "Groundnut": [
        {
            "name": "Leaf Spot (Cercospora)",
            "type": "fungal disease",
            "symptoms": "Small brown/black circular spots on leaves, yellowing margins, premature defoliation.",
            "favorable_conditions": "high_humidity",
            "prevention": "Use disease-free seed, crop rotation, avoid waterlogging, maintain spacing for airflow.",
            "treatment": "Spray a recommended fungicide (e.g. chlorothalonil-based) at first symptom; consult local Krishi Vigyan Kendra for dosage.",
        },
        {
            "name": "Aphids",
            "type": "insect pest",
            "symptoms": "Clusters of small insects on undersides of leaves; curling and yellowing of foliage.",
            "favorable_conditions": "dry_heat",
            "prevention": "Encourage natural predators (ladybirds), avoid excess nitrogen fertilizer.",
            "treatment": "Neem oil spray for mild infestation; recommended insecticide for severe outbreaks.",
        },
    ],
    "Cotton": [
        {
            "name": "Pink Bollworm",
            "type": "insect pest",
            "symptoms": "Rosette flowers, damaged bolls with pink larvae inside, reduced lint quality.",
            "favorable_conditions": "warm_humid",
            "prevention": "Use pheromone traps, destroy crop residue after harvest, timely sowing.",
            "treatment": "Targeted insecticide application based on trap catch thresholds; consult extension officer.",
        },
        {
            "name": "Whitefly",
            "type": "insect pest",
            "symptoms": "Yellowing leaves, sticky honeydew residue, sooty mould growth.",
            "favorable_conditions": "dry_heat",
            "prevention": "Yellow sticky traps, avoid water stress, intercropping with non-host crops.",
            "treatment": "Neem-based biopesticide first; systemic insecticide only if infestation is severe.",
        },
    ],
    "Paddy": [
        {
            "name": "Blast (Magnaporthe oryzae)",
            "type": "fungal disease",
            "symptoms": "Spindle-shaped lesions on leaves with grey centers, neck rot at panicle stage.",
            "favorable_conditions": "high_humidity",
            "prevention": "Balanced nitrogen use, resistant varieties, proper water management.",
            "treatment": "Fungicide spray (e.g. tricyclazole) at early symptom stage per label dosage.",
        },
        {
            "name": "Brown Plant Hopper",
            "type": "insect pest",
            "symptoms": "Yellowing and drying of plants in patches ('hopper burn'), stunted growth.",
            "favorable_conditions": "warm_humid",
            "prevention": "Avoid excess nitrogen, maintain proper spacing, use resistant varieties.",
            "treatment": "Recommended insecticide if hopper count exceeds economic threshold (consult local advisory).",
        },
    ],
    "Millet": [
        {
            "name": "Downy Mildew",
            "type": "fungal disease",
            "symptoms": "Pale green to yellow streaks on leaves, downy white growth on undersides.",
            "favorable_conditions": "high_humidity",
            "prevention": "Use treated/resistant seed, avoid dense sowing, remove infected plants early.",
            "treatment": "Seed treatment with metalaxyl-based fungicide before sowing; remove infected plants.",
        },
    ],
    "Sugarcane": [
        {
            "name": "Red Rot",
            "type": "fungal disease",
            "symptoms": "Reddish discoloration inside stalk, foul smell, drying of leaves.",
            "favorable_conditions": "warm_humid",
            "prevention": "Use disease-free setts, resistant varieties, field sanitation.",
            "treatment": "No cure once infected -- remove and destroy affected clumps; treat seed setts before planting.",
        },
    ],
    "Banana": [
        {
            "name": "Panama Wilt (Fusarium)",
            "type": "fungal disease",
            "symptoms": "Yellowing of older leaves progressing upward, splitting of pseudostem base.",
            "favorable_conditions": "waterlogged_soil",
            "prevention": "Use disease-free tissue-culture plants, avoid waterlogging, soil solarization.",
            "treatment": "No chemical cure -- remove and destroy infected plants, avoid replanting bananas in same soil for 2+ years.",
        },
    ],
}

DEFAULT_RISKS = [
    {
        "name": "General Fungal Risk",
        "type": "fungal disease",
        "symptoms": "Leaf spots, wilting, discoloration -- monitor closely during humid weather.",
        "favorable_conditions": "high_humidity",
        "prevention": "Ensure good drainage and airflow, avoid overhead irrigation in evenings.",
        "treatment": "Consult local agricultural extension officer for crop-specific fungicide guidance.",
    }
]


@dataclass
class PestRisk:
    name: str
    pest_type: str
    risk_level: str  # Low / Moderate / High
    symptoms: str
    prevention: str
    treatment: str


def _condition_tag(humidity_pct: float, rainfall_7d_mm: float, temp_c: float) -> str:
    if humidity_pct > 75 and rainfall_7d_mm > 20:
        return "high_humidity"
    if temp_c > 32 and rainfall_7d_mm < 5:
        return "dry_heat"
    if humidity_pct > 65 and temp_c > 26:
        return "warm_humid"
    if rainfall_7d_mm > 60:
        return "waterlogged_soil"
    return "normal"


def assess_pest_risk(crop_name: str, humidity_pct: float, rainfall_7d_mm: float, temp_c: float) -> list[PestRisk]:
    entries = PEST_KNOWLEDGE_BASE.get(crop_name, DEFAULT_RISKS)
    current_condition = _condition_tag(humidity_pct, rainfall_7d_mm, temp_c)

    risks = []
    for entry in entries:
        if entry["favorable_conditions"] == current_condition:
            risk_level = "High"
        elif entry["favorable_conditions"] == "normal":
            risk_level = "Low"
        else:
            risk_level = "Moderate"
        risks.append(
            PestRisk(
                name=entry["name"],
                pest_type=entry["type"],
                risk_level=risk_level,
                symptoms=entry["symptoms"],
                prevention=entry["prevention"],
                treatment=entry["treatment"],
            )
        )

    # Sort: High risk first, for clearer farmer-facing prioritization.
    order = {"High": 0, "Moderate": 1, "Low": 2}
    risks.sort(key=lambda r: order.get(r.risk_level, 3))
    return risks
