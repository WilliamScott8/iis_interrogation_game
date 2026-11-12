"""
One function per screen in the player's journey:
welcome -> case -> summary

The "case" screen is a set of tabs (Evidence Sheet, Interrogation Room,
Verdict Form) the player can switch between freely until they submit.

Each screen function reads/writes state via backend.session and is called
once per rerun by app.py based on the current stage.
"""

import streamlit as st

from backend import session, storage
from backend.suspect import MAX_QUESTIONS
from ui.components import (
    chat_history,
    confidence_slider,
    evidence_list,
    question_counter,
    verdict_options,
)


def welcome_screen() -> None:
    story = session.get_story()
    st.title(story["title"])
    st.write(story["case_briefing"])

    st.subheader("Before you begin")
    st.write(
        "You will play as the detective and interview four suspects. Your "
        "answers stay anonymous. With your permission, we'd like to record "
        "the questions you ask, the suspects' responses, and your final "
        "verdicts for research into how people respond to AI characters "
        "during interrogation. No identifying information is collected."
    )
    consent = st.checkbox("I agree to let my anonymous session data be recorded for this research.")

    if st.button("Begin the case", disabled=not consent):
        st.session_state.consent_given = True
        session.set_stage("case")
        st.rerun()


def case_screen() -> None:
    """The main game screen: three tabs the player can switch between freely."""
    story = session.get_story()
    st.title(story["title"])

    evidence_tab, interrogation_tab, verdict_tab = st.tabs(
        ["Evidence Sheet", "Interrogation Room", "Verdict Form"],
        key="case_tabs",
    )
    with evidence_tab:
        _evidence_tab()
    with interrogation_tab:
        _interrogation_tab()
    with verdict_tab:
        _verdict_tab()


def _evidence_tab() -> None:
    sheet = session.get_story()["evidence_sheet"]

    st.header("Evidence Sheet")
    st.markdown(f"**Victim:** {sheet['victim']}")
    st.markdown(f"**Stolen item:** {sheet['stolen_item']}")
    st.markdown(f"**Location:** {sheet['location']}")
    st.markdown(f"**Theft window:** {sheet['theft_window']}")
    st.markdown("**Known facts:**")
    evidence_list(sheet["facts"])

    st.divider()
    st.info(
        f"You may ask each of the four suspects up to {MAX_QUESTIONS} questions, "
        "in any order. Use plain English, and ask whatever you'd ask a real suspect. "
        "Switch between the tabs above at any time, and submit from the Verdict Form "
        "when you're ready."
    )


def _interrogation_tab() -> None:
    st.header("Interrogation Room")
    suspects = session.get_suspects()

    tabs = st.tabs([suspects[sid].name for sid in suspects], key="suspect_tabs")

    for tab, suspect_id in zip(tabs, suspects):
        suspect = suspects[suspect_id]
        with tab:
            st.caption(suspect.data["role"])
            chat_history(suspect)
            question_counter(suspect)

            remaining = suspect.questions_remaining()
            question = st.chat_input(
                f"Ask {suspect.name} a question...",
                key=f"input_{suspect_id}",
                disabled=remaining <= 0,
            )
            if question:
                with st.spinner(f"{suspect.name} is thinking..."):
                    suspect.ask(question)
                st.rerun()


def _verdict_tab() -> None:
    st.header("Verdict Form")
    st.caption(
        "For each suspect, say whether you think they are guilty or innocent, "
        "then how confident you are in that choice."
    )
    suspects = session.get_suspects()
    verdicts = session.get_verdicts()
    confidences = session.get_confidences()

    for suspect_id, suspect in suspects.items():
        with st.container(border=True):
            st.subheader(suspect.name)
            choice = st.radio(
                f"I think {suspect.name} is...",
                options=verdict_options(),
                index=verdict_options().index(verdicts[suspect_id]),
                key=f"verdict_{suspect_id}",
                horizontal=True,
            )
            session.set_verdict(suspect_id, choice)

            confidence = confidence_slider(suspect, choice, confidences[suspect_id])
            session.set_confidence(suspect_id, confidence)

    st.divider()
    if st.button("Submit final verdicts", type="primary"):
        pid = st.session_state.participant_id
        args = (pid, suspects, session.get_verdicts(), session.get_confidences())
        # storage.save_local(*args)
        storage.export_to_sheets(*args)
        session.set_stage("summary")
        st.rerun()


def summary_screen() -> None:
    st.title("Case Closed")
    suspects = session.get_suspects()
    verdicts = session.get_verdicts()
    confidences = session.get_confidences()

    correct_count = 0
    for suspect_id, suspect in suspects.items():
        truth = "guilty" if suspect.guilty else "innocent"
        verdict = verdicts[suspect_id]
        is_correct = verdict == truth
        correct_count += is_correct
        icon = "✅" if is_correct else "❌"
        confidence = "" if verdict == "undecided" else f" ({confidences[suspect_id]}% confident)"
        st.write(f"{icon} **{suspect.name}** — you said *{verdict}*{confidence}, actually *{truth}*.")

    st.divider()
    st.write(f"You correctly identified **{correct_count} / {len(suspects)}** suspects.")
    st.write("Thank you for playing. Your anonymous responses have been recorded for the study.")
