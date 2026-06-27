"""
pages/3_Market_Insights.py
==============================
Shows market prices, trends, and profit opportunity comparisons via
the MarketIntelligenceAgent.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from agents.market_agent import MarketIntelligenceAgent
from database.db_manager import DatabaseManager
from frontend.components.ui_helpers import (
    init_page,
    language_selector,
    render_agent_response,
    render_disclaimer,
    render_header,
    render_offline_notice,
)

strings = init_page("Market Insights")

with st.sidebar:
    render_header(strings)
    language_selector(strings, key="lang_select_market")

render_header(strings, subtitle=strings["nav_market"])
render_offline_notice(strings)

db = DatabaseManager()
fc = st.session_state.farm_context

col1, col2, col3 = st.columns(3)
with col1:
    crop_name = st.text_input(strings["crop_label"], value=fc.get("crop_name", "Groundnut"))
with col2:
    region = st.text_input(strings["region_label"], value=fc.get("region", "Tirunelveli"))
with col3:
    compare_raw = st.text_input(strings["market_compare_label"], value="Cotton, Millet")

compare_list = [c.strip() for c in compare_raw.split(",") if c.strip()]

if st.button("Analyze market", type="primary"):
    insight_resp = MarketIntelligenceAgent().run(crop_name=crop_name, region=region, compare_with=compare_list)
    render_agent_response(insight_resp, strings)

    all_rows = []
    for crop in [crop_name] + compare_list:
        rows = db.get_market_prices(crop)
        all_rows.extend(rows)

    if all_rows:
        df = pd.DataFrame(all_rows)
        df["price_date"] = pd.to_datetime(df["price_date"])
        df = df.sort_values("price_date")

        st.subheader("Price history")
        fig = px.line(
            df, x="price_date", y="price_per_quintal", color="crop_name", markers=True,
            labels={"price_date": "Date", "price_per_quintal": "Price (₹/quintal)", "crop_name": "Crop"},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Raw market data")
        st.dataframe(
            df[["crop_name", "market_name", "region", "price_per_quintal", "price_date", "trend"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info(strings["no_data"])

render_disclaimer(strings)
