"""
app.py
========
KrishiMitra AI -- main Streamlit entry point / Dashboard page.

Run with:  streamlit run app.py

Streamlit auto-discovers additional pages in the sibling `pages/`
directory (Advisory Assistant, Crop Planner, Market Insights,
Government Schemes, Settings), giving the multi-page app described
in the project spec.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable when Streamlit runs this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from agents.crop_agent import CropRecommendationAgent
from agents.weather_agent import WeatherAgent
from config.settings import settings
from frontend.components.ui_helpers import (
    init_page,
    language_selector,
    render_disclaimer,
    render_header,
    render_offline_notice,
)
from security.rate_limiter import RateLimitExceeded, global_rate_limiter

strings = init_page("Dashboard")

with st.sidebar:
    render_header(strings)
    language_selector(strings)
    st.caption(f"Environment: {settings.app_env} | Gemini configured: {settings.has_gemini_key()}")
    for warning in settings.validate():
        st.warning(warning)

render_header(strings)
render_offline_notice(strings)

fc = st.session_state.farm_context
st.subheader(strings["farm_profile_header"])
cols = st.columns(5)
cols[0].metric(strings["region_label"], fc["region"])
cols[1].metric(strings["soil_type_label"], fc["soil_type"].title())
cols[2].metric(strings["season_label"], fc["season"].title())
cols[3].metric(strings["rainfall_label"], f"{fc['rainfall_mm']} mm")
cols[4].metric(strings["land_area_label"], f"{fc['land_area_acres']} ac")
st.caption("Edit your farm profile in Settings.")

st.divider()

col_weather, col_crop = st.columns(2)

with col_weather:
    st.subheader(f"🌦️ {strings['dashboard_weather_header']}")
    try:
        global_rate_limiter.enforce("dashboard_session")
        weather_resp = WeatherAgent().run(region=fc["region"])
        w = weather_resp.raw_data["weather"]
        st.metric("Current Temp", f"{w['current_temp_c']} °C")
        st.metric("Humidity", f"{w['humidity_pct']} %")
        st.metric("Rainfall (last 7d)", f"{w['rainfall_last_7d_mm']} mm")
        st.caption(f"Data source: {w['source']}")

        with st.expander("7-day forecast"):
            for day in w["forecast"]:
                st.write(f"**{day['date']}** — {day['condition']}, rain {day['rainfall_mm']}mm, "
                         f"{day['temp_min_c']}–{day['temp_max_c']}°C")

        if w["warnings"]:
            st.subheader(f"⚠️ {strings['dashboard_alerts_header']}")
            for warning in w["warnings"]:
                st.markdown(f"<div class='km-alert'>{warning}</div>", unsafe_allow_html=True)
    except RateLimitExceeded as exc:
        st.warning(strings["rate_limit_warning"])

with col_crop:
    st.subheader(f"🌱 {strings['dashboard_crop_header']}")
    try:
        crop_resp = CropRecommendationAgent().run(
            soil_type=fc["soil_type"], season=fc["season"], rainfall_mm=fc["rainfall_mm"], region=fc["region"]
        )
        st.markdown(
            f"<div class='km-card'><b>{crop_resp.recommendation}</b><br>"
            f"<span class='km-confidence-badge'>{strings['confidence_label']}: {crop_resp.confidence_score:.0f}%</span></div>",
            unsafe_allow_html=True,
        )
        with st.expander(strings["reason_label"]):
            for f in crop_resp.factors_considered:
                st.markdown(f"- {f}")
        if crop_resp.alternatives:
            st.caption(f"{strings['alternatives_label']}: " + ", ".join(crop_resp.alternatives))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not generate a crop recommendation right now: {exc}")

st.divider()
st.info("👉 Use **Advisory Assistant** in the sidebar to ask a free-form question, or explore "
        "**Crop Planner**, **Market Insights**, and **Government Schemes**.")

render_disclaimer(strings)
