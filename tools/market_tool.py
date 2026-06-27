"""
tools/market_tool.py
======================
Market price analysis used by the Market Intelligence Agent. Reads
from the local `market_data` table (seeded with demo data, refreshable
via the MCP market-price server) and computes trend + a simple
"profit opportunity score" used by both the Market Agent and the
Crop Recommendation Agent's explainability output.
"""

from __future__ import annotations

from dataclasses import dataclass

from database.db_manager import DatabaseManager


@dataclass
class MarketInsight:
    crop_name: str
    region: str
    latest_price_per_quintal: float | None
    price_change_pct: float | None
    trend: str
    profit_opportunity_score: float  # 0-100
    notes: list[str]


def analyze_market(crop_name: str, region: str | None = None, db: DatabaseManager | None = None) -> MarketInsight:
    db = db or DatabaseManager()
    rows = db.get_market_prices(crop_name, region)

    if not rows:
        return MarketInsight(
            crop_name=crop_name,
            region=region or "unknown",
            latest_price_per_quintal=None,
            price_change_pct=None,
            trend="unknown",
            profit_opportunity_score=50.0,
            notes=[f"No market data available yet for '{crop_name}' in this region. Showing a neutral score."],
        )

    rows_sorted = sorted(rows, key=lambda r: r["price_date"], reverse=True)
    latest = rows_sorted[0]
    notes = []

    price_change_pct = None
    if len(rows_sorted) > 1:
        previous = rows_sorted[1]
        if previous["price_per_quintal"]:
            price_change_pct = round(
                (latest["price_per_quintal"] - previous["price_per_quintal"]) / previous["price_per_quintal"] * 100,
                1,
            )

    trend = latest.get("trend") or "stable"

    # Profit opportunity score: blends trend direction, price momentum,
    # and absolute price level (normalized loosely against a reference
    # band) -- intentionally simple and explainable for a capstone demo.
    trend_component = {"rising": 70, "stable": 50, "falling": 30}.get(trend, 50)
    momentum_component = 50 + (price_change_pct or 0) * 2
    momentum_component = max(0, min(100, momentum_component))
    score = round(trend_component * 0.6 + momentum_component * 0.4, 1)

    if trend == "rising":
        notes.append(f"Prices for {crop_name} are trending upward in {latest['region']} -- a favorable window to sell.")
    elif trend == "falling":
        notes.append(f"Prices for {crop_name} are softening in {latest['region']} -- consider holding stock if storage allows.")
    else:
        notes.append(f"Prices for {crop_name} have been stable recently in {latest['region']}.")

    return MarketInsight(
        crop_name=crop_name,
        region=latest["region"],
        latest_price_per_quintal=latest["price_per_quintal"],
        price_change_pct=price_change_pct,
        trend=trend,
        profit_opportunity_score=score,
        notes=notes,
    )


def compare_crops_by_opportunity(crop_names: list[str], region: str | None = None, db: DatabaseManager | None = None) -> list[MarketInsight]:
    db = db or DatabaseManager()
    insights = [analyze_market(c, region, db) for c in crop_names]
    insights.sort(key=lambda i: i.profit_opportunity_score, reverse=True)
    return insights
