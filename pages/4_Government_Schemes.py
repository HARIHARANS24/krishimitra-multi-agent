"""
pages/4_Government_Schemes.py
================================
Search and browse government agricultural schemes via the
GovernmentSchemeAgent, with a plain-language eligibility explanation
based on the farmer's profile.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from agents.scheme_agent import GovernmentSchemeAgent
from frontend.components.ui_helpers import (
    init_page,
    language_selector,
    render_disclaimer,
    render_header,
    render_offline_notice,
)

strings = init_page("Government Schemes")

with st.sidebar:
    render_header(strings)
    language_selector(strings, key="lang_select_schemes")

render_header(strings, subtitle=strings["nav_schemes"])
render_offline_notice(strings)

fc = st.session_state.farm_context

col1, col2 = st.columns(2)
with col1:
    keyword = st.text_input(strings["search_schemes_placeholder"])
with col2:
    state = st.text_input(strings["state_label"], value=fc.get("state", "Tamil Nadu"))

if st.button("Search schemes", type="primary") or not keyword:
    resp = GovernmentSchemeAgent().run(keyword=keyword or None, state=state or None, farmer_profile=fc)
    matches = resp.raw_data.get("matches", [])

    if not matches:
        st.info(strings["no_data"])
    else:
        for m in matches:
            with st.container(border=True):
                st.markdown(f"### {m['scheme_name']}")
                st.write(m["description"])
                st.markdown(f"**Eligibility:** {m['eligibility']}")
                st.markdown(f"**Benefits:** {m['benefits']}")
                st.caption(m["relevance_note"])
                if m.get("official_link"):
                    st.markdown(f"[Official portal]({m['official_link']})")

render_disclaimer(strings)
