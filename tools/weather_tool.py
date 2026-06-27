"""
tools/weather_tool.py
=======================
Weather data access + analysis used by the Weather Agent.

Two modes:
  * LIVE mode: calls Open-Meteo (no key required) when network access
    is available. Open-Meteo is used because it has a generous free
    tier suitable for a capstone demo.
  * SIMULATED mode: deterministic, seasonally-aware synthetic weather
    generator used when network/API access is unavailable -- this
    keeps the whole platform demoable offline (important for a Kaggle
    capstone where graders may run it without configuring API keys).

Both modes return the same `WeatherReading` / `ForecastDay` shape so
the agent layer above never needs to know which mode is active.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import date, timedelta

import httpx

from config.settings import settings

# Approximate lat/lon for a handful of Tamil Nadu / common Indian regions,
# used for live lookups and as a stable seed source for simulation.
REGION_COORDINATES = {
    "tirunelveli": (8.7139, 77.7567),
    "madurai": (9.9252, 78.1198),
    "chennai": (13.0827, 80.2707),
    "coimbatore": (11.0168, 76.9558),
    "thanjavur": (10.7870, 79.1378),
    "erode": (11.3410, 77.7172),
    "trichy": (10.7905, 78.7047),
    "salem": (11.6643, 78.1460),
}


@dataclass
class ForecastDay:
    day_offset: int
    date_str: str
    temp_max_c: float
    temp_min_c: float
    rainfall_mm: float
    humidity_pct: float
    condition: str


@dataclass
class WeatherReading:
    region: str
    source: str  # "live" or "simulated"
    current_temp_c: float
    humidity_pct: float
    rainfall_last_7d_mm: float
    forecast: list[ForecastDay] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _seeded_rng(region: str) -> random.Random:
    """Deterministic per-region RNG so repeated demo runs are stable."""
    seed = int(hashlib.sha256(region.lower().encode()).hexdigest(), 16) % (10**8)
    # Mix in the day-of-year so values still vary day to day.
    seed += date.today().timetuple().tm_yday
    return random.Random(seed)


def _simulate_weather(region: str) -> WeatherReading:
    rng = _seeded_rng(region)
    month = date.today().month
    # Rough seasonal baseline for South India: more rain Jun-Sep (SW monsoon)
    # and Oct-Dec (NE monsoon).
    if month in (6, 7, 8, 9):
        base_rain, rain_var, temp_base = 8.0, 12.0, 30.0
    elif month in (10, 11, 12):
        base_rain, rain_var, temp_base = 6.0, 15.0, 28.0
    else:
        base_rain, rain_var, temp_base = 0.5, 2.0, 33.0

    current_temp = round(temp_base + rng.uniform(-2.5, 2.5), 1)
    humidity = round(55 + rng.uniform(0, 30), 1)
    rainfall_7d = round(max(0.0, sum(rng.uniform(0, rain_var) + base_rain * rng.random() for _ in range(7))), 1)

    forecast = []
    conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Heavy Rain", "Thunderstorms"]
    for i in range(7):
        day_rain = max(0.0, rng.gauss(base_rain, rain_var / 2))
        if day_rain < 1:
            condition = "Sunny" if rng.random() > 0.3 else "Partly Cloudy"
        elif day_rain < 10:
            condition = "Light Rain"
        elif day_rain < 30:
            condition = "Heavy Rain"
        else:
            condition = "Thunderstorms"
        forecast.append(
            ForecastDay(
                day_offset=i,
                date_str=(date.today() + timedelta(days=i)).isoformat(),
                temp_max_c=round(temp_base + rng.uniform(-1, 4), 1),
                temp_min_c=round(temp_base - rng.uniform(4, 8), 1),
                rainfall_mm=round(day_rain, 1),
                humidity_pct=round(50 + rng.uniform(0, 35), 1),
                condition=condition,
            )
        )

    warnings = []
    heavy_rain_days = [f for f in forecast if f.rainfall_mm > 30]
    if heavy_rain_days:
        warnings.append(
            f"Heavy rainfall expected on {', '.join(d.date_str for d in heavy_rain_days)}. "
            "Consider delaying irrigation and protect harvested produce from waterlogging."
        )
    dry_streak = sum(1 for f in forecast if f.rainfall_mm < 1)
    if dry_streak >= 5:
        warnings.append(
            f"Dry spell expected ({dry_streak} of next 7 days with negligible rain). "
            "Plan supplementary irrigation."
        )

    return WeatherReading(
        region=region,
        source="simulated",
        current_temp_c=current_temp,
        humidity_pct=humidity,
        rainfall_last_7d_mm=rainfall_7d,
        forecast=forecast,
        warnings=warnings,
    )


def _fetch_live_weather(region: str) -> WeatherReading | None:
    coords = REGION_COORDINATES.get(region.lower())
    if not coords:
        return None
    lat, lon = coords
    try:
        resp = httpx.get(
            f"{settings.weather_api_base_url}/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean",
                "timezone": "Asia/Kolkata",
                "forecast_days": 7,
            },
            timeout=6.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    try:
        daily = data["daily"]
        forecast = []
        for i, d in enumerate(daily["time"]):
            forecast.append(
                ForecastDay(
                    day_offset=i,
                    date_str=d,
                    temp_max_c=daily["temperature_2m_max"][i],
                    temp_min_c=daily["temperature_2m_min"][i],
                    rainfall_mm=daily["precipitation_sum"][i],
                    humidity_pct=daily.get("relative_humidity_2m_mean", [60] * len(daily["time"]))[i],
                    condition="Rain" if daily["precipitation_sum"][i] > 1 else "Clear",
                )
            )
        rainfall_7d = round(sum(f.rainfall_mm for f in forecast), 1)
        current = data.get("current", {})

        warnings = []
        heavy_rain_days = [f for f in forecast if f.rainfall_mm > 30]
        if heavy_rain_days:
            warnings.append(
                f"Heavy rainfall expected on {', '.join(d.date_str for d in heavy_rain_days)}."
            )

        return WeatherReading(
            region=region,
            source="live",
            current_temp_c=current.get("temperature_2m", forecast[0].temp_max_c if forecast else 30.0),
            humidity_pct=current.get("relative_humidity_2m", 60.0),
            rainfall_last_7d_mm=rainfall_7d,
            forecast=forecast,
            warnings=warnings,
        )
    except (KeyError, IndexError):
        return None


def get_weather(region: str, prefer_live: bool = True) -> WeatherReading:
    """Public entry point used by the Weather Agent / MCP weather server."""
    if prefer_live:
        live = _fetch_live_weather(region)
        if live is not None:
            return live
    return _simulate_weather(region)


def estimate_irrigation_need(reading: WeatherReading, crop_water_need_mm_per_week: float = 35.0) -> dict:
    """Very simple irrigation-need heuristic: compare forecast rainfall
    against a crop's typical weekly water requirement.
    """
    forecast_rain = sum(f.rainfall_mm for f in reading.forecast)
    deficit = max(0.0, crop_water_need_mm_per_week - forecast_rain)
    return {
        "forecast_rainfall_mm": round(forecast_rain, 1),
        "crop_water_need_mm": crop_water_need_mm_per_week,
        "irrigation_deficit_mm": round(deficit, 1),
        "irrigation_recommended": deficit > 5,
    }
