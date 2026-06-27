"""
pages/2_Crop_Planner.py
==========================
Generates weekly/monthly farming calendars via the PlanningAgent,
plus a fertilizer breakdown, for the farmer's chosen (or recommended)
crop.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from agents.crop_agent import CropRecommendationAgent
from agents.planning_agent import PlanningAgent
from frontend.components.ui_helpers import (
    init_page,
    language_selector,
    render_agent_response,
    render_disclaimer,
    render_header,
    render_offline_notice,
)

strings = init_page("Crop Planner")

with st.sidebar:
    render_header(strings)
    language_selector(strings, key="lang_select_planner")

render_header(strings, subtitle=strings["nav_planner"])
render_offline_notice(strings)

fc = st.session_state.farm_context

st.subheader("Step 1 — Pick a crop")
col1, col2 = st.columns([1, 2])
with col1:
    use_recommended = st.checkbox("Use top recommended crop", value=True)

if use_recommended:
    crop_resp = CropRecommendationAgent().run(
        soil_type=fc["soil_type"], season=fc["season"], rainfall_mm=fc["rainfall_mm"], region=fc["region"]
    )
    render_agent_response(crop_resp, strings)
    chosen_crop = crop_resp.recommendation.split(" (")[0]
else:
    chosen_crop = st.text_input(strings["crop_label"], value=fc.get("crop_name", "Groundnut"))

st.divider()
st.subheader("Step 2 — Generate calendar")
sowing_date = st.date_input("Sowing date")

if st.button(strings["generate_plan_button"], type="primary"):
    plan_resp = PlanningAgent().run(
        crop_name=chosen_crop, soil_type=fc["soil_type"], sowing_date=sowing_date.isoformat()
    )
    render_agent_response(plan_resp, strings)

    st.subheader(f"📅 {strings['weekly_plan_header']}")
    weekly_df = pd.DataFrame(plan_resp.raw_data["weekly_plan"])
    weekly_df["activities"] = weekly_df["activities"].apply(lambda a: "; ".join(a))
    st.dataframe(weekly_df, use_container_width=True, hide_index=True)

    st.subheader(f"🗓️ {strings['monthly_plan_header']}")
    monthly_df = pd.DataFrame(plan_resp.raw_data["monthly_plan"])
    monthly_df["activities"] = monthly_df["activities"].apply(lambda a: "; ".join(a))
    st.dataframe(monthly_df, use_container_width=True, hide_index=True)

    st.subheader("📍 Key milestones")
    milestones_df = pd.DataFrame(plan_resp.raw_data["milestones"])
    st.dataframe(milestones_df, use_container_width=True, hide_index=True)

render_disclaimer(strings)
