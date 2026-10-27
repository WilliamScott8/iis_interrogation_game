"""
Entry point — the only file Streamlit runs directly (`streamlit run app.py`).
Owns nothing but wiring: load styling, make sure the session is initialised,
and dispatch to whichever screen matches the current stage.
"""

from pathlib import Path

import streamlit as st

from backend import session
from ui.screens import (
    evidence_screen,
    interrogation_screen,
    summary_screen,
    verdict_screen,
    welcome_screen,
)

st.set_page_config(page_title="The Ashworth Necklace", page_icon="🔍", layout="centered")

css_path = Path(__file__).resolve().parent / "ui" / "style.css"
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

session.init_session()

SCREENS = {
    "welcome": welcome_screen,
    "evidence": evidence_screen,
    "interrogation": interrogation_screen,
    "verdict": verdict_screen,
    "summary": summary_screen,
}

SCREENS[session.get_stage()]()
