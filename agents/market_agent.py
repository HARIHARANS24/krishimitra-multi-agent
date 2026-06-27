"""
agents/market_agent.py
=========================
Market Intelligence Agent: analyzes crop prices, identifies
profitable crops, and provides market trend insights.
"""

from __future__ import annotations

from agents.base_agent import AgentResponse, BaseAgent
from tools.market_tool import analyze_market, compare_crops_by_opportunity


class MarketIntelligenceAgent(BaseAgent):
    name = "market_intelligence_agent"
    description = (
        "Analyzes current and historical crop market prices, computes a profit opportunity "
        "score, and compares multiple crops to help farmers decide what to sell or grow next."
    )
    tools = ["market_price.get_market_price", "market_price.compare_crop_profitability"]

    def run(self, crop_name: str, region: str | None = None, compare_with: list[str] | None = None, **_) -> AgentResponse:
        insight = analyze_market(crop_name, region)

        factors = list(insight.notes)
        if insight.latest_price_per_quintal is not None:
            factors.insert(
                0,
                f"Latest price for {crop_name} in {insight.region}: "
                f"Rs. {insight.latest_price_per_quintal}/quintal "
                f"({'+' if (insight.price_change_pct or 0) >= 0 else ''}{insight.price_change_pct or 0}% vs previous reading).",
            )

        recommendation = (
            f"{crop_name}: {insight.trend} trend, profit opportunity score {insight.profit_opportunity_score}/100."
        )

        alternatives = []
        if compare_with:
            comparison = compare_crops_by_opportunity([crop_name] + compare_with, region)
            alternatives = [
                f"{c.crop_name} (score {c.profit_opportunity_score})" for c in comparison if c.crop_name != crop_name
            ]

        return AgentResponse(
            agent_name=self.name,
            recommendation=recommendation,
            confidence_score=min(90.0, max(40.0, insight.profit_opportunity_score)),
            factors_considered=factors,
            alternatives=alternatives,
            raw_data={"insight": insight.__dict__},
        )
