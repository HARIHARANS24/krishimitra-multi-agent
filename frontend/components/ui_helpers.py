"""
frontend/components/ui_helpers.py
====================================
Shared Streamlit helpers used across every page: language loading,
farm-context session state, custom styling, and small render helpers
for AgentResponse / CoordinatorResult objects.
"""

from __future__ import annotations

import streamlit as st

from agents.base_agent import AgentResponse
from config.settings import SUPPORTED_LANGUAGES, settings
from tools.translation_tool import load_ui_strings

CUSTOM_CSS = """
<style>
:root {
    --km-green: #2E7D32;
    --km-light-green: #E8F5E9;
    --km-earth: #6D4C28;
    --km-amber: #F9A825;
}
.km-header {
    background: linear-gradient(135deg, var(--km-green), #43A047);
    padding: 1.2rem 1.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1rem;
}
.km-header h1 { margin: 0; font-size: 1.6rem; }
.km-header p { margin: 0.2rem 0 0 0; opacity: 0.9; font-size: 0.95rem; }
.km-card {
    background: var(--km-light-green);
    border-left: 4px solid var(--km-green);
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.7rem;
}
.km-alert {
    background: #FFF3E0;
    border-left: 4px solid var(--km-amber);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
}
.km-confidence-badge {
    display: inline-block;
    background: var(--km-green);
    color: white;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
}
.km-disclaimer {
    font-size: 0.78rem;
    color: #757575;
    margin-top: 1.5rem;
    border-top: 1px solid #e0e0e0;
    padding-top: 0.6rem;
}
</style>
"""


def init_page(page_title: str) -> dict:
    """Call at the top of every page: sets up CSS, language, and
    returns the loaded i18n string dict for convenience."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if "language" not in st.session_state:
        st.session_state.language = settings.default_language
    if "farm_context" not in st.session_state:
        st.session_state.farm_context = {
            "region": "Tirunelveli",
            "soil_type": "red",
            "season": "kharif",
            "rainfall_mm": 850,
            "crop_name": "Groundnut",
            "state": "Tamil Nadu",
            "land_area_acres": 3.5,
        }

    strings = load_ui_strings(st.session_state.language)
    st.set_page_config(page_title=f"{strings['app_title']} | {page_title}", page_icon="🌾", layout="wide")
    return strings


def render_header(strings: dict, subtitle: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="km-header">
            <h1>🌾 {strings['app_title']}</h1>
            <p>{subtitle or strings['app_tagline']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_offline_notice(strings: dict) -> None:
    if not settings.has_gemini_key():
        st.info(strings["offline_mode_notice"])


def render_disclaimer(strings: dict) -> None:
    st.markdown(f"<div class='km-disclaimer'>{strings['disclaimer']}</div>", unsafe_allow_html=True)


def language_selector(strings: dict, key: str = "lang_select") -> None:
    options = list(SUPPORTED_LANGUAGES.keys())
    labels = [SUPPORTED_LANGUAGES[k] for k in options]
    current_index = options.index(st.session_state.language) if st.session_state.language in options else 0
    chosen_label = st.selectbox(strings["language_label"], labels, index=current_index, key=key)
    chosen_code = options[labels.index(chosen_label)]
    if chosen_code != st.session_state.language:
        st.session_state.language = chosen_code
        st.rerun()


def render_agent_response(response: AgentResponse, strings: dict) -> None:
    st.markdown(f"#### {response.agent_name.replace('_', ' ').title()}")
    st.markdown(
        f"<div class='km-card'><b>{response.recommendation}</b><br>"
        f"<span class='km-confidence-badge'>{strings['confidence_label']}: {response.confidence_score:.0f}%</span></div>",
        unsafe_allow_html=True,
    )
    with st.expander(strings["reason_label"]):
        for factor in response.factors_considered:
            st.markdown(f"- {factor}")
    if response.alternatives:
        with st.expander(strings["alternatives_label"]):
            for alt in response.alternatives:
                st.markdown(f"- {alt}")
