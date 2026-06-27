"""
agents/crop_agent.py
=======================
Crop Recommendation Agent: recommends crops based on soil, season,
and rainfall, producing the Top-3 + suitability scores required by
the project spec.
"""

from __future__ import annotations

from agents.base_agent import AgentResponse, BaseAgent
from security.input_validation import validate_season, validate_soil_type
from tools.crop_tool import score_crops


class CropRecommendationAgent(BaseAgent):
    name = "crop_recommendation_agent"
    description = (
        "Recommends the top crops for a farm based on soil type, season, and rainfall, "
        "returning a suitability score and a transparent breakdown of contributing factors."
    )
    tools = ["crop_db.recommend_crops", "crop_db.list_known_crops"]

    def run(self, soil_type: str, season: str, rainfall_mm: float, region: str | None = None, **_) -> AgentResponse:
        soil_type = validate_soil_type(soil_type)
        season = validate_season(season)

        scores = score_crops(soil_type, season, rainfall_mm, top_n=3)
        if not scores:
            return AgentResponse(
                agent_name=self.name,
                recommendation="No suitable crop could be determined for the given conditions.",
                confidence_score=0.0,
                factors_considered=["No crops in the knowledge base matched these conditions well."],
                alternatives=[],
            )

        top = scores[0]
        alternatives = [s.crop_name for s in scores[1:]]

        factors = [
            f"Soil compatibility for {top.crop_name} with '{soil_type}' soil: {top.factors['soil_compatibility']:.0f}%.",
            f"Season compatibility for '{season}' season: {top.factors['season_compatibility']:.0f}%.",
            f"Rainfall compatibility at {rainfall_mm} mm: {top.factors['rainfall_compatibility']:.0f}%.",
            f"Local market demand index: {top.factors['local_demand_index']:.0f}%.",
        ]
        if region:
            factors.insert(0, f"Conditions evaluated for region: {region}.")

        recommendation = (
            f"{top.crop_name} (suitability score {top.suitability_score}/100, "
            f"~{top.duration_days} day crop cycle, needs ~{top.water_need_mm_per_week} mm water/week)."
        )

        return AgentResponse(
            agent_name=self.name,
            recommendation=recommendation,
            confidence_score=min(95.0, top.suitability_score),
            factors_considered=factors,
            alternatives=alternatives,
            raw_data={"top_crops": [s.__dict__ for s in scores]},
        )
