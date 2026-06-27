"""
mcp_servers/knowledge_base_server.py
=======================================
MCP server exposing the broader agricultural knowledge base: pest &
disease guidance, fertilizer recommendations, and government scheme
lookups. Grouped into one server since they share the same
"agronomic reference knowledge" domain (as distinct from the live
weather and market price data servers).

Run standalone for testing:
    python -m mcp_servers.knowledge_base_server
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from tools.fertilizer_tool import recommend_fertilizer
from tools.pest_tool import assess_pest_risk
from tools.scheme_tool import search_schemes

mcp = FastMCP("krishimitra-knowledge-base")


@mcp.tool()
def get_pest_disease_risk(crop_name: str, humidity_pct: float, rainfall_7d_mm: float, temp_c: float) -> str:
    """Assess pest and disease risk for a crop given recent weather
    conditions, with prevention and treatment guidance.

    Args:
        crop_name: Name of the crop, e.g. "Groundnut".
        humidity_pct: Recent average humidity percentage.
        rainfall_7d_mm: Total rainfall over the last 7 days in mm.
        temp_c: Recent average temperature in Celsius.
    """
    risks = assess_pest_risk(crop_name, humidity_pct, rainfall_7d_mm, temp_c)
    payload = [
        {
            "name": r.name,
            "type": r.pest_type,
            "risk_level": r.risk_level,
            "symptoms": r.symptoms,
            "prevention": r.prevention,
            "treatment": r.treatment,
        }
        for r in risks
    ]
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
def get_fertilizer_plan(crop_name: str, soil_type: str, growth_stage: str = "") -> str:
    """Get an NPK fertilizer recommendation with stage-wise dosage
    breakdown for a crop and soil type.

    Args:
        crop_name: Name of the crop.
        soil_type: Soil type (alluvial, black, red, laterite, sandy, clay, loamy, saline).
        growth_stage: Optional specific stage to highlight (basal, flowering, pod_filling).
    """
    plan = recommend_fertilizer(crop_name, soil_type, growth_stage or None)
    payload = {
        "crop_name": plan.crop_name,
        "soil_type": plan.soil_type,
        "total_n_kg_per_acre": plan.total_n_kg,
        "total_p_kg_per_acre": plan.total_p_kg,
        "total_k_kg_per_acre": plan.total_k_kg,
        "stage_breakdown": plan.stage_breakdown,
        "explanation": plan.explanation,
    }
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
def search_government_schemes(keyword: str = "", state: str = "") -> str:
    """Search government agricultural schemes by keyword and/or state.

    Args:
        keyword: Search term (scheme name, benefit, eligibility text).
        state: Indian state name to filter by applicability.
    """
    matches = search_schemes(keyword=keyword or None, state=state or None)
    payload = [
        {
            "scheme_name": m.scheme_name,
            "description": m.description,
            "eligibility": m.eligibility,
            "benefits": m.benefits,
            "official_link": m.official_link,
            "relevance_note": m.relevance_note,
        }
        for m in matches
    ]
    return json.dumps(payload, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
