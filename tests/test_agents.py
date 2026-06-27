"""
tests/test_agents.py
=======================
Unit tests for each specialist agent's `run()` method, asserting the
explainability contract (recommendation, confidence_score,
factors_considered, alternatives) is always satisfied.
"""

from __future__ import annotations

from agents.base_agent import AgentResponse
from agents.crop_agent import CropRecommendationAgent
from agents.fertilizer_agent import FertilizerAgent
from agents.market_agent import MarketIntelligenceAgent
from agents.pest_agent import PestDiseaseAgent
from agents.planning_agent import PlanningAgent
from agents.scheme_agent import GovernmentSchemeAgent
from agents.weather_agent import WeatherAgent


def assert_valid_agent_response(response: AgentResponse):
    assert isinstance(response, AgentResponse)
    assert response.recommendation
    assert 0 <= response.confidence_score <= 100
    assert isinstance(response.factors_considered, list)
    assert len(response.factors_considered) > 0
    assert isinstance(response.alternatives, list)


class TestWeatherAgent:
    def test_run_returns_valid_response(self):
        agent = WeatherAgent()
        response = agent.run(region="Tirunelveli")
        assert_valid_agent_response(response)
        assert "weather" in response.raw_data

    def test_irrigation_field_present(self):
        agent = WeatherAgent()
        response = agent.run(region="Madurai", crop_water_need_mm_per_week=40)
        assert "irrigation" in response.raw_data
        assert "irrigation_recommended" in response.raw_data["irrigation"]


class TestCropRecommendationAgent:
    def test_run_returns_top_crop(self):
        agent = CropRecommendationAgent()
        response = agent.run(soil_type="red", season="kharif", rainfall_mm=850, region="Tirunelveli")
        assert_valid_agent_response(response)
        assert len(response.raw_data["top_crops"]) <= 3

    def test_alternatives_are_distinct_from_top(self):
        agent = CropRecommendationAgent()
        response = agent.run(soil_type="black", season="kharif", rainfall_mm=900)
        top_crop_name = response.raw_data["top_crops"][0]["crop_name"]
        assert top_crop_name not in response.alternatives


class TestPestDiseaseAgent:
    def test_run_returns_risk_assessment(self):
        agent = PestDiseaseAgent()
        response = agent.run(crop_name="Groundnut", region="Tirunelveli")
        assert_valid_agent_response(response)
        assert "risks" in response.raw_data

    def test_unknown_crop_falls_back_gracefully(self):
        agent = PestDiseaseAgent()
        response = agent.run(crop_name="Dragonfruit", region="Tirunelveli")
        assert_valid_agent_response(response)


class TestFertilizerAgent:
    def test_run_returns_npk_plan(self):
        agent = FertilizerAgent()
        response = agent.run(crop="Groundnut", soil_type="red")
        assert_valid_agent_response(response)
        assert response.raw_data["total_n_kg"] >= 0

    def test_soil_adjustment_changes_dosage(self):
        agent = FertilizerAgent()
        sandy = agent.run(crop="Cotton", soil_type="sandy")
        clay = agent.run(crop="Cotton", soil_type="clay")
        assert sandy.raw_data["total_n_kg"] != clay.raw_data["total_n_kg"]


class TestMarketIntelligenceAgent:
    def test_run_with_seeded_data(self, test_db, monkeypatch):
        import tools.market_tool as market_tool_module

        agent = MarketIntelligenceAgent()
        # Patch the DB used by the underlying tool to our isolated test_db.
        monkeypatch.setattr(market_tool_module, "DatabaseManager", lambda: test_db)
        response = agent.run(crop_name="Groundnut", region="Tirunelveli")
        assert_valid_agent_response(response)

    def test_run_with_no_data_returns_neutral_score(self):
        agent = MarketIntelligenceAgent()
        response = agent.run(crop_name="NonexistentCrop123")
        assert_valid_agent_response(response)
        assert response.raw_data["insight"]["trend"] == "unknown"


class TestGovernmentSchemeAgent:
    def test_run_finds_seeded_schemes(self, test_db, monkeypatch):
        import tools.scheme_tool as scheme_tool_module

        agent = GovernmentSchemeAgent()
        monkeypatch.setattr(scheme_tool_module, "DatabaseManager", lambda: test_db)
        response = agent.run(keyword="insurance")
        assert_valid_agent_response(response)
        assert len(response.raw_data["matches"]) > 0


class TestPlanningAgent:
    def test_run_returns_calendar(self):
        agent = PlanningAgent()
        response = agent.run(crop_name="Groundnut", soil_type="red", sowing_date="2026-06-01")
        assert_valid_agent_response(response)
        assert len(response.raw_data["milestones"]) >= 2
        assert len(response.raw_data["weekly_plan"]) == 4
        assert len(response.raw_data["monthly_plan"]) >= 1
