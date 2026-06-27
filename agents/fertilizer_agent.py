"""
agents/fertilizer_agent.py
=============================
Fertilizer Agent: recommends fertilizer types/quantities and explains
dosage by crop growth stage.
"""

from __future__ import annotations

from agents.base_agent import AgentResponse, BaseAgent
from security.input_validation import validate_soil_type
from tools.fertilizer_tool import recommend_fertilizer


class FertilizerAgent(BaseAgent):
    name = "fertilizer_agent"
    description = (
        "Recommends fertilizer (N-P-K) quantities for a crop and soil type, broken down by "
        "growth stage, with the reasoning behind soil-based dosage adjustments."
    )
    tools = ["knowledge_base.get_fertilizer_plan"]

    def run(self, crop: str, soil_type: str, growth_stage: str | None = None, **_) -> AgentResponse:
        soil_type = validate_soil_type(soil_type)
        plan = recommend_fertilizer(crop, soil_type, growth_stage)

        recommendation = (
            f"For {crop} on {soil_type} soil: apply a total of {plan.total_n_kg} kg N, "
            f"{plan.total_p_kg} kg P, {plan.total_k_kg} kg K per acre across the crop cycle."
        )

        factors = list(plan.explanation)
        if plan.stage_breakdown:
            for stage in plan.stage_breakdown:
                factors.append(
                    f"At '{stage['stage']}' stage: N={stage['n_kg_per_acre']} kg, "
                    f"P={stage['p_kg_per_acre']} kg, K={stage['k_kg_per_acre']} kg per acre."
                )

        alternatives = [
            "Use organic alternatives (FYM, vermicompost) to partially substitute chemical fertilizer.",
            "Get a Soil Health Card test for a precise, field-specific recommendation.",
        ]

        return AgentResponse(
            agent_name=self.name,
            recommendation=recommendation,
            confidence_score=70.0,
            factors_considered=factors,
            alternatives=alternatives,
            raw_data={
                "total_n_kg": plan.total_n_kg,
                "total_p_kg": plan.total_p_kg,
                "total_k_kg": plan.total_k_kg,
                "stage_breakdown": plan.stage_breakdown,
            },
        )
