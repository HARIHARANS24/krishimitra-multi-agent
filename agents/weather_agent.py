"""
agents/weather_agent.py
=========================
Weather Agent: fetches weather, analyzes rainfall, predicts
irrigation needs, and raises warnings.
"""

from __future__ import annotations

from agents.base_agent import AgentResponse, BaseAgent
from tools.weather_tool import estimate_irrigation_need, get_weather


class WeatherAgent(BaseAgent):
    name = "weather_agent"
    description = (
        "Fetches current weather and 7-day forecasts for a farmer's region, analyzes "
        "rainfall patterns, predicts irrigation needs, and raises proactive warnings "
        "about extreme weather (heavy rain, dry spells)."
    )
    tools = ["weather.get_current_weather", "weather.get_irrigation_recommendation"]

    def run(self, region: str, crop_water_need_mm_per_week: float = 35.0, **_) -> AgentResponse:
        reading = get_weather(region)
        irrigation = estimate_irrigation_need(reading, crop_water_need_mm_per_week)

        factors = [
            f"Current temperature in {region}: {reading.current_temp_c}°C, humidity {reading.humidity_pct}%.",
            f"Rainfall over last 7 days: {reading.rainfall_last_7d_mm} mm.",
            f"Forecast rainfall over next 7 days: {irrigation['forecast_rainfall_mm']} mm "
            f"(crop needs ~{irrigation['crop_water_need_mm']} mm/week).",
        ]
        if reading.warnings:
            factors.extend(reading.warnings)

        if irrigation["irrigation_recommended"]:
            recommendation = (
                f"Irrigation is recommended this week. Expected rainfall deficit of "
                f"~{irrigation['irrigation_deficit_mm']} mm against your crop's needs."
            )
            confidence = 80.0 if reading.source == "live" else 65.0
        else:
            recommendation = (
                "No supplementary irrigation needed this week -- forecast rainfall should "
                "meet your crop's water requirement."
            )
            confidence = 78.0 if reading.source == "live" else 62.0

        alternatives = []
        if irrigation["irrigation_recommended"]:
            alternatives.append("Delay irrigation by 1-2 days and re-check forecast if rain looks likely.")
        else:
            alternatives.append("Light irrigation as a buffer if soil moisture appears low on inspection.")

        return AgentResponse(
            agent_name=self.name,
            recommendation=recommendation,
            confidence_score=confidence,
            factors_considered=factors,
            alternatives=alternatives,
            raw_data={
                "weather": {
                    "region": reading.region,
                    "source": reading.source,
                    "current_temp_c": reading.current_temp_c,
                    "humidity_pct": reading.humidity_pct,
                    "rainfall_last_7d_mm": reading.rainfall_last_7d_mm,
                    "forecast": [f.__dict__ for f in reading.forecast],
                    "warnings": reading.warnings,
                },
                "irrigation": irrigation,
            },
        )
