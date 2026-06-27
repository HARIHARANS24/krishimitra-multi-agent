"""
mcp_servers/market_price_server.py
=====================================
MCP server exposing crop market price data and trend analysis.

Run standalone for testing:
    python -m mcp_servers.market_price_server
"""

from __future__ import annotations

import json
from datetime import date

from mcp.server.fastmcp import FastMCP

from database.db_manager import DatabaseManager
from tools.market_tool import analyze_market, compare_crops_by_opportunity

mcp = FastMCP("krishimitra-market-price")
_db = DatabaseManager()


@mcp.tool()
def get_market_price(crop_name: str, region: str = "") -> str:
    """Get the latest market price, trend, and profit opportunity score
    for a crop, optionally scoped to a region.

    Args:
        crop_name: Name of the crop, e.g. "Groundnut".
        region: Optional region/market name to filter by.
    """
    insight = analyze_market(crop_name, region or None, db=_db)
    payload = {
        "crop_name": insight.crop_name,
        "region": insight.region,
        "latest_price_per_quintal": insight.latest_price_per_quintal,
        "price_change_pct": insight.price_change_pct,
        "trend": insight.trend,
        "profit_opportunity_score": insight.profit_opportunity_score,
        "notes": insight.notes,
    }
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
def compare_crop_profitability(crop_names: list[str], region: str = "") -> str:
    """Compare multiple crops by profit opportunity score, ranked best first.

    Args:
        crop_names: List of crop names to compare.
        region: Optional region/market name to filter by.
    """
    insights = compare_crops_by_opportunity(crop_names, region or None, db=_db)
    payload = [
        {
            "crop_name": i.crop_name,
            "profit_opportunity_score": i.profit_opportunity_score,
            "trend": i.trend,
            "latest_price_per_quintal": i.latest_price_per_quintal,
        }
        for i in insights
    ]
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
def record_market_price(
    crop_name: str, market_name: str, region: str, price_per_quintal: float, trend: str = "stable"
) -> str:
    """Record a new market price observation (e.g. from a field agent
    or manual entry).

    Args:
        crop_name: Name of the crop.
        market_name: Name of the mandi/market.
        region: Region the market is located in.
        price_per_quintal: Price in INR per quintal.
        trend: One of rising, falling, stable.
    """
    row_id = _db.upsert_market_price(
        crop_name, market_name, region, price_per_quintal, date.today().isoformat(), trend
    )
    return json.dumps({"status": "recorded", "market_id": row_id})


if __name__ == "__main__":
    mcp.run(transport="stdio")
