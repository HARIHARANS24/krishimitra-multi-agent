"""
mcp_servers/weather_server.py
================================
MCP server exposing weather data as standardized MCP tools, so any
MCP-compatible agent/client (Google ADK agents, Claude, or other
hosts) can call it -- not just KrishiMitra's own Weather Agent.

Run standalone for testing:
    python -m mcp_servers.weather_server

This uses the official `mcp` Python SDK's FastMCP server, communicating
over stdio (the standard transport for locally-spawned MCP servers).
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from tools.weather_tool import estimate_irrigation_need, get_weather

mcp = FastMCP("krishimitra-weather")


@mcp.tool()
def get_current_weather(region: str) -> str:
    """Get current weather conditions and a 7-day forecast for an
    agricultural region.

    Args:
        region: Region/district name, e.g. "Tirunelveli".
    """
    reading = get_weather(region)
    payload = {
        "region": reading.region,
        "source": reading.source,
        "current_temp_c": reading.current_temp_c,
        "humidity_pct": reading.humidity_pct,
        "rainfall_last_7d_mm": reading.rainfall_last_7d_mm,
        "forecast": [
            {
                "date": f.date_str,
                "temp_max_c": f.temp_max_c,
                "temp_min_c": f.temp_min_c,
                "rainfall_mm": f.rainfall_mm,
                "humidity_pct": f.humidity_pct,
                "condition": f.condition,
            }
            for f in reading.forecast
        ],
        "warnings": reading.warnings,
    }
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
def get_irrigation_recommendation(region: str, crop_water_need_mm_per_week: float = 35.0) -> str:
    """Estimate whether supplementary irrigation is needed this week
    for a given region and crop water requirement.

    Args:
        region: Region/district name.
        crop_water_need_mm_per_week: Typical weekly water requirement of the crop in mm.
    """
    reading = get_weather(region)
    result = estimate_irrigation_need(reading, crop_water_need_mm_per_week)
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
