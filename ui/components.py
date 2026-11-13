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


def safe_openings_list(openings: list[dict]) -> None:
    """Each opening as a bold heading line with its notes as sub-bullets."""
    for entry in openings:
        label, _, detail = entry["opening"].partition(":")
        lines = [f"- **{label.strip()}:** {detail.strip()}" if detail else f"- **{label.strip()}**"]
        lines += [f"    - {note}" for note in entry.get("notes") or []]
        st.markdown("\n".join(lines))


def confidence_slider(suspect: Suspect, verdict: str, current: int) -> int:
    """0-100% confidence in the chosen verdict; disabled while undecided."""
    undecided = verdict == "undecided"
    value = st.slider(
        "How confident are you in this choice?",
        min_value=0,
        max_value=100,
        value=current,
        step=5,
        format="%d%%",
        key=f"confidence_{suspect.data['id']}",
        disabled=undecided,
    )
    if undecided:
        st.caption("Choose guilty or innocent to set your confidence.")
    return value


def verdict_options() -> list[str]:
    return ["undecided", "innocent", "guilty"]
