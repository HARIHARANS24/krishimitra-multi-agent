"""
tests/test_mcp.py
====================
Integration tests that prove KrishiMitra's MCP servers work end to
end over the real MCP protocol (stdio transport): a server is spawned
as a subprocess, a client session connects, tool discovery is
performed, and tools are actually called.

These tests require the `mcp` package (see requirements.txt). If it
is not installed in a given environment, they are skipped rather than
failing the whole suite.
"""

from __future__ import annotations

import json

import pytest

mcp_module = pytest.importorskip("mcp", reason="mcp package not installed")

from mcp_servers.mcp_client import call_tool_json, list_tools_for_server  # noqa: E402


@pytest.mark.asyncio
class TestWeatherMCPServer:
    async def test_lists_expected_tools(self):
        tools = await list_tools_for_server("weather")
        assert "get_current_weather" in tools
        assert "get_irrigation_recommendation" in tools

    async def test_get_current_weather_returns_valid_payload(self):
        result = await call_tool_json("weather", "get_current_weather", {"region": "Tirunelveli"})
        assert result["region"] == "Tirunelveli"
        assert "forecast" in result
        assert len(result["forecast"]) == 7


@pytest.mark.asyncio
class TestCropDbMCPServer:
    async def test_lists_expected_tools(self):
        tools = await list_tools_for_server("crop_db")
        assert "recommend_crops" in tools
        assert "list_known_crops" in tools

    async def test_recommend_crops_returns_ranked_list(self):
        result = await call_tool_json(
            "crop_db", "recommend_crops", {"soil_type": "red", "season": "kharif", "rainfall_mm": 850, "top_n": 3}
        )
        assert isinstance(result, list)
        assert len(result) <= 3
        assert result[0]["suitability_score"] >= result[-1]["suitability_score"]


@pytest.mark.asyncio
class TestKnowledgeBaseMCPServer:
    async def test_lists_expected_tools(self):
        tools = await list_tools_for_server("knowledge_base")
        assert "get_pest_disease_risk" in tools
        assert "get_fertilizer_plan" in tools
        assert "search_government_schemes" in tools

    async def test_get_fertilizer_plan_returns_npk(self):
        result = await call_tool_json(
            "knowledge_base", "get_fertilizer_plan", {"crop_name": "Groundnut", "soil_type": "red"}
        )
        assert "total_n_kg_per_acre" in result
        assert "total_p_kg_per_acre" in result
        assert "total_k_kg_per_acre" in result


@pytest.mark.asyncio
class TestMarketPriceMCPServer:
    async def test_lists_expected_tools(self):
        tools = await list_tools_for_server("market_price")
        assert "get_market_price" in tools
        assert "record_market_price" in tools

    async def test_record_then_get_market_price(self):
        record_result = await call_tool_json(
            "market_price",
            "record_market_price",
            {
                "crop_name": "TestCropMCP",
                "market_name": "Test Mandi",
                "region": "TestRegion",
                "price_per_quintal": 5000,
                "trend": "rising",
            },
        )
        assert record_result["status"] == "recorded"

        get_result = await call_tool_json(
            "market_price", "get_market_price", {"crop_name": "TestCropMCP", "region": "TestRegion"}
        )
        assert get_result["latest_price_per_quintal"] == 5000
