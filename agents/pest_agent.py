"""
agents/pest_agent.py
=======================
Pest and Disease Agent: detects likely pest/disease risks for a crop
given recent weather, and recommends safe prevention/treatment.
"""

from __future__ import annotations

from agents.base_agent import AgentResponse, BaseAgent
from tools.pest_tool import assess_pest_risk
from tools.weather_tool import get_weather


class PestDiseaseAgent(BaseAgent):
    name = "pest_disease_agent"
    description = (
        "Assesses pest and disease risk for a given crop based on recent weather "
        "conditions, explaining symptoms, risk level, prevention, and safe treatment options."
    )
    tools = ["knowledge_base.get_pest_disease_risk", "weather.get_current_weather"]

    def run(self, crop_name: str, region: str, **_) -> AgentResponse:
        reading = get_weather(region)
        avg_temp = reading.current_temp_c
        risks = assess_pest_risk(crop_name, reading.humidity_pct, reading.rainfall_last_7d_mm, avg_temp)

        if not risks:
            return AgentResponse(
                agent_name=self.name,
                recommendation=f"No specific pest/disease risks identified for {crop_name} right now.",
                confidence_score=55.0,
                factors_considered=["No matching entries in the pest knowledge base for this crop."],
                alternatives=[],
            )

        top_risk = risks[0]
        factors = [
            f"Current conditions in {region}: humidity {reading.humidity_pct}%, "
            f"7-day rainfall {reading.rainfall_last_7d_mm} mm, temperature {avg_temp}°C.",
            f"'{top_risk.name}' ({top_risk.pest_type}) risk level assessed as {top_risk.risk_level} "
            "based on how favorable current conditions are for this pest/disease.",
            f"Symptoms to watch for: {top_risk.symptoms}",
        ]

        recommendation = (
            f"Highest current risk for {crop_name}: {top_risk.name} ({top_risk.risk_level} risk). "
            f"Prevention: {top_risk.prevention} If symptoms appear: {top_risk.treatment}"
        )

        alternatives = [f"{r.name} ({r.risk_level} risk)" for r in risks[1:]]

        return AgentResponse(
            agent_name=self.name,
            recommendation=recommendation,
            confidence_score={"High": 82.0, "Moderate": 68.0, "Low": 50.0}.get(top_risk.risk_level, 55.0),
            factors_considered=factors,
            alternatives=alternatives,
            raw_data={"risks": [r.__dict__ for r in risks]},
        )
