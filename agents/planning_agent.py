"""
agents/planning_agent.py
===========================
Planning Agent: generates weekly, monthly, and seasonal farming
calendars by combining outputs from the Crop, Weather, and Fertilizer
agents -- demonstrating multi-step planning and agent collaboration
within a single agent's reasoning, in addition to the Coordinator's
top-level orchestration.
"""

from __future__ import annotations

from datetime import date, timedelta

from agents.base_agent import AgentResponse, BaseAgent
from tools.crop_tool import CROP_KNOWLEDGE_BASE
from tools.fertilizer_tool import recommend_fertilizer


class PlanningAgent(BaseAgent):
    name = "planning_agent"
    description = (
        "Generates weekly, monthly, and seasonal farming calendars for a chosen crop, "
        "sequencing sowing, fertilizer application, irrigation checkpoints, and harvest."
    )
    tools = ["crop_db.list_known_crops", "knowledge_base.get_fertilizer_plan"]

    def run(self, crop_name: str, soil_type: str, sowing_date: str | None = None, **_) -> AgentResponse:
        info = CROP_KNOWLEDGE_BASE.get(crop_name)
        duration = info["duration_days"] if info else 110
        start = date.fromisoformat(sowing_date) if sowing_date else date.today()

        fert_plan = recommend_fertilizer(crop_name, soil_type)

        milestones = [
            {"week": 0, "date": start.isoformat(), "activity": f"Sow {crop_name} / apply basal fertilizer dose."},
        ]
        # Mid-cycle flowering checkpoint (~40% of duration).
        flowering_offset = int(duration * 0.4)
        milestones.append(
            {
                "week": flowering_offset // 7,
                "date": (start + timedelta(days=flowering_offset)).isoformat(),
                "activity": "Flowering stage -- apply top-dressing fertilizer dose, monitor for pests.",
            }
        )
        # Pod-filling / grain-filling checkpoint (~70% of duration).
        podfill_offset = int(duration * 0.7)
        milestones.append(
            {
                "week": podfill_offset // 7,
                "date": (start + timedelta(days=podfill_offset)).isoformat(),
                "activity": "Pod/grain-filling stage -- ensure adequate irrigation, final nutrient top-up if applicable.",
            }
        )
        harvest_date = start + timedelta(days=duration)
        milestones.append(
            {
                "week": duration // 7,
                "date": harvest_date.isoformat(),
                "activity": f"Expected harvest window for {crop_name}.",
            }
        )

        weekly_plan = self._build_weekly_plan(start, milestones)
        monthly_plan = self._build_monthly_plan(start, harvest_date, milestones)

        recommendation = (
            f"{crop_name} farming calendar: sow on {start.isoformat()}, expect harvest around "
            f"{harvest_date.isoformat()} (~{duration} day cycle)."
        )

        factors = [
            f"Crop cycle duration for {crop_name}: ~{duration} days.",
            "Fertilizer milestones aligned to basal / flowering / pod-filling growth stages.",
            f"Fertilizer totals: N={fert_plan.total_n_kg} kg, P={fert_plan.total_p_kg} kg, "
            f"K={fert_plan.total_k_kg} kg per acre.",
        ]

        return AgentResponse(
            agent_name=self.name,
            recommendation=recommendation,
            confidence_score=68.0,
            factors_considered=factors,
            alternatives=["Adjust the calendar by 1-2 weeks based on local extension officer guidance."],
            raw_data={
                "milestones": milestones,
                "weekly_plan": weekly_plan,
                "monthly_plan": monthly_plan,
            },
        )

    @staticmethod
    def _build_weekly_plan(start: date, milestones: list[dict]) -> list[dict]:
        plan = []
        for i in range(4):  # first 4 weeks, detailed
            week_start = start + timedelta(weeks=i)
            activities = [m["activity"] for m in milestones if m["week"] == i]
            plan.append(
                {
                    "week_number": i + 1,
                    "starting": week_start.isoformat(),
                    "activities": activities or ["Routine monitoring: weeds, soil moisture, pest scouting."],
                }
            )
        return plan

    @staticmethod
    def _build_monthly_plan(start: date, harvest: date, milestones: list[dict]) -> list[dict]:
        plan = []
        cur = start
        month_num = 1
        while cur < harvest:
            month_end = min(cur + timedelta(days=30), harvest)
            activities = [m["activity"] for m in milestones if cur <= date.fromisoformat(m["date"]) < month_end]
            plan.append(
                {
                    "month_number": month_num,
                    "period": f"{cur.isoformat()} to {month_end.isoformat()}",
                    "activities": activities or ["Routine crop care and monitoring."],
                }
            )
            cur = month_end
            month_num += 1
        return plan
