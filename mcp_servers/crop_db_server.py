"""
mcp_servers/crop_db_server.py
================================
MCP server exposing the crop knowledge base / suitability scoring
engine as MCP tools.

Run standalone for testing:
    python -m mcp_servers.crop_db_server
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from tools.crop_tool import CROP_KNOWLEDGE_BASE, score_crops

mcp = FastMCP("krishimitra-crop-db")


@mcp.tool()
def recommend_crops(soil_type: str, season: str, rainfall_mm: float, top_n: int = 3) -> str:
    """Recommend the top N most suitable crops for given farm conditions.

    Args:
        soil_type: One of alluvial, black, red, laterite, sandy, clay, loamy, saline.
        season: One of kharif, rabi, zaid, summer.
        rainfall_mm: Expected/typical seasonal rainfall in millimeters.
        top_n: Number of top crop recommendations to return.
    """
    scores = score_crops(soil_type, season, rainfall_mm, top_n)
    payload = [
        {
            "crop_name": s.crop_name,
            "suitability_score": s.suitability_score,
            "factors": s.factors,
            "water_need_mm_per_week": s.water_need_mm_per_week,
            "duration_days": s.duration_days,
        }
        for s in scores
    ]
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
def list_known_crops() -> str:
    """List all crops currently in the knowledge base, with their
    suitable soils and seasons."""
    payload = {
        crop: {"soils": sorted(info["soils"]), "seasons": sorted(info["seasons"])}
        for crop, info in CROP_KNOWLEDGE_BASE.items()
    }
    return json.dumps(payload, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
