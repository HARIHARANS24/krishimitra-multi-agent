"""
pages/1_Advisory_Assistant.py
================================
Chat interface where a farmer can ask free-form questions like
"What should I grow this season?" or "Will rain affect my crop?".
Backed by the CoordinatorAgent, which routes to the right specialist
agent(s) and returns an explainable, multi-section answer.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from agents.coordinator_agent import CoordinatorAgent
from database.db_manager import DatabaseManager
from frontend.components.ui_helpers import (
    init_page,
    language_selector,
    render_disclaimer,
    render_header,
    render_offline_notice,
)
from security.input_validation import ValidationError
from security.rate_limiter import RateLimitExceeded
from tools.translation_tool import translate_dynamic_text

strings = init_page("Advisory Assistant")

with st.sidebar:
    render_header(strings)
    language_selector(strings, key="lang_select_advisory")

render_header(strings, subtitle=strings["nav_advisory"])
render_offline_notice(strings)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "coordinator" not in st.session_state:
    st.session_state.coordinator = CoordinatorAgent(db=DatabaseManager())

for role, content in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(content)

example_questions = [
    "What should I grow this season?",
    "How much fertilizer should I use?",
    "Will rain affect my crop?",
]
st.caption("Try: " + " · ".join(f"_{q}_" for q in example_questions))

user_input = st.chat_input(strings["ask_placeholder"])

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            result = st.session_state.coordinator.handle_query(
                raw_query=user_input,
                farm_context=st.session_state.farm_context,
                user_identity=st.session_state.session_id,
            )
            answer = result.final_recommendation
            lang = st.session_state.language
            if lang != "en":
                answer = translate_dynamic_text(answer, lang)

            st.markdown(answer)

            if result.reflection_notes:
                with st.expander("🔎 Reflection notes"):
                    for note in result.reflection_notes:
                        st.markdown(f"- {note}")

            st.caption(f"Routed to: {', '.join(result.routed_agents) or 'none'} | "
                       f"Overall confidence: {result.confidence_score:.0f}%")

            st.session_state.chat_history.append(("assistant", answer))

        except ValidationError as exc:
            st.warning(f"Please rephrase your question: {exc}")
        except RateLimitExceeded:
            st.warning(strings["rate_limit_warning"])

render_disclaimer(strings)
