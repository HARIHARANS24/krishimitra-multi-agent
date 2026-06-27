"""
pages/5_Settings.py
=======================
Language selection and farm profile editing. Farm context is stored
in `st.session_state.farm_context` and used by every other page/agent
as the shared source of truth for the current session.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from frontend.components.ui_helpers import (
    init_page,
    language_selector,
    render_disclaimer,
    render_header,
)
from security.input_validation import (
    VALID_SEASONS,
    VALID_SOIL_TYPES,
    ValidationError,
    validate_land_area_acres,
    validate_rainfall_mm,
    validate_region_name,
)

strings = init_page("Settings")

with st.sidebar:
    render_header(strings)

render_header(strings, subtitle=strings["nav_settings"])

st.subheader(strings["language_label"])
language_selector(strings, key="lang_select_settings")

st.divider()
st.subheader(strings["farm_profile_header"])

fc = st.session_state.farm_context

with st.form("farm_profile_form"):
    region = st.text_input(strings["region_label"], value=fc["region"])
    soil_type = st.selectbox(
        strings["soil_type_label"], sorted(VALID_SOIL_TYPES), index=sorted(VALID_SOIL_TYPES).index(fc["soil_type"])
    )
    season = st.selectbox(
        strings["season_label"], sorted(VALID_SEASONS), index=sorted(VALID_SEASONS).index(fc["season"])
    )
    rainfall_mm = st.number_input(strings["rainfall_label"], min_value=0.0, max_value=5000.0, value=float(fc["rainfall_mm"]))
    land_area_acres = st.number_input(
        strings["land_area_label"], min_value=0.1, max_value=10000.0, value=float(fc["land_area_acres"])
    )
    crop_name = st.text_input(strings["crop_label"], value=fc["crop_name"])
    state = st.text_input(strings["state_label"], value=fc.get("state", ""))

    submitted = st.form_submit_button(strings["save_button"], type="primary")

if submitted:
    try:
        validated_region = validate_region_name(region)
        validated_rainfall = validate_rainfall_mm(rainfall_mm)
        validated_area = validate_land_area_acres(land_area_acres)

        st.session_state.farm_context = {
            "region": validated_region,
            "soil_type": soil_type,
            "season": season,
            "rainfall_mm": validated_rainfall,
            "land_area_acres": validated_area,
            "crop_name": crop_name.strip() or "Groundnut",
            "state": state.strip(),
        }
        st.success("Farm profile updated.")
    except ValidationError as exc:
        st.error(str(exc))

render_disclaimer(strings)
