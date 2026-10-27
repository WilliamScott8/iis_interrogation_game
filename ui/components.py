"""Small, reusable Streamlit render functions shared across screens."""

import streamlit as st

from backend.suspect import MAX_QUESTIONS, Suspect


def chat_history(suspect: Suspect) -> None:
    for message in suspect.history:
        role = "user" if message["role"] == "user" else "assistant"
        avatar = "🕵️" if role == "user" else "🙂"
        with st.chat_message(role, avatar=avatar):
            st.write(message["content"])


def question_counter(suspect: Suspect) -> None:
    remaining = suspect.questions_remaining()
    st.caption(f"Questions remaining with {suspect.name}: {remaining} / {MAX_QUESTIONS}")
    st.progress(remaining / MAX_QUESTIONS)


def suspect_tabs(suspects: dict[str, Suspect]) -> list[str]:
    """Returns suspect ids in display order, for use with st.tabs labels."""
    return list(suspects.keys())


def evidence_list(facts: list[str]) -> None:
    for fact in facts:
        st.markdown(f"- {fact}")


def verdict_options() -> list[str]:
    return ["undecided", "innocent", "guilty"]
