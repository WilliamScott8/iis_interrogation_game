"""
Thin wrapper around st.session_state: owns the one-time setup of a
playthrough (loading the story, building Suspect objects, generating an
anonymous participant id) and the small bits of game state the UI screens
read and write (current stage, selected suspect, verdicts).
"""

import uuid
from pathlib import Path

import streamlit as st
import yaml

from backend.suspect import Suspect

STORY_PATH = Path(__file__).resolve().parent.parent / "story" / "story_a.yaml"

STAGES = ("welcome", "evidence", "interrogation", "verdict", "summary")


def _load_story() -> dict:
    with open(STORY_PATH) as f:
        return yaml.safe_load(f)


def init_session() -> None:
    if "initialized" in st.session_state:
        return
    story = _load_story()
    st.session_state.initialized = True
    st.session_state.participant_id = str(uuid.uuid4())
    st.session_state.consent_given = False
    st.session_state.stage = "welcome"
    st.session_state.story = story
    st.session_state.suspects = {
        s["id"]: Suspect(s, story["common_knowledge"]) for s in story["suspects"]
    }
    st.session_state.current_suspect_id = story["suspects"][0]["id"]
    st.session_state.verdicts = {s["id"]: "undecided" for s in story["suspects"]}


def get_story() -> dict:
    return st.session_state.story


def get_suspects() -> dict[str, Suspect]:
    return st.session_state.suspects


def get_current_suspect() -> Suspect:
    return st.session_state.suspects[st.session_state.current_suspect_id]


def set_current_suspect(suspect_id: str) -> None:
    st.session_state.current_suspect_id = suspect_id


def get_verdicts() -> dict[str, str]:
    return st.session_state.verdicts


def set_verdict(suspect_id: str, verdict: str) -> None:
    st.session_state.verdicts[suspect_id] = verdict


def get_stage() -> str:
    return st.session_state.stage


def set_stage(stage: str) -> None:
    assert stage in STAGES, f"unknown stage: {stage}"
    st.session_state.stage = stage
