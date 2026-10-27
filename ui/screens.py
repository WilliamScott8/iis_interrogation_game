"""
One function per screen in the player's journey:
welcome -> evidence -> interrogation -> verdict -> summary

Each function reads/writes state via backend.session and is called once per
rerun by app.py based on the current stage.
"""

import streamlit as st

from backend import session, storage
from ui.components import chat_history, evidence_list, question_counter, verdict_options


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
        session.set_stage("evidence")
        st.rerun()


def evidence_screen() -> None:
    story = session.get_story()
    sheet = story["evidence_sheet"]

    st.title("Evidence Sheet")
    st.markdown(f"**Victim:** {sheet['victim']}")
    st.markdown(f"**Stolen item:** {sheet['stolen_item']}")
    st.markdown(f"**Location:** {sheet['location']}")
    st.markdown(f"**Theft window:** {sheet['theft_window']}")
    st.markdown("**Known facts:**")
    evidence_list(sheet["facts"])

    st.divider()
    st.write(
        "You may ask each of the four suspects up to 8 questions, in any "
        "order. Use plain English — ask whatever you'd ask a real suspect."
    )
    if st.button("Begin interrogations"):
        session.set_stage("interrogation")
        st.rerun()


def interrogation_screen() -> None:
    st.title("Interrogation")
    suspects = session.get_suspects()

    tab_labels = [suspects[sid].name for sid in suspects]
    tabs = st.tabs(tab_labels)

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

    st.divider()
    if st.button("I'm ready to give my verdicts"):
        session.set_stage("verdict")
        st.rerun()


def verdict_screen() -> None:
    st.title("Your Verdicts")
    suspects = session.get_suspects()
    verdicts = session.get_verdicts()

    for suspect_id, suspect in suspects.items():
        st.subheader(suspect.name)
        choice = st.radio(
            f"Verdict for {suspect.name}",
            options=verdict_options(),
            index=verdict_options().index(verdicts[suspect_id]),
            key=f"verdict_{suspect_id}",
            horizontal=True,
        )
        session.set_verdict(suspect_id, choice)

    st.divider()
    if st.button("Submit final verdicts"):
        storage.save_local(st.session_state.participant_id, suspects, session.get_verdicts())
        storage.export_to_sheets(st.session_state.participant_id, suspects, session.get_verdicts())
        session.set_stage("summary")
        st.rerun()


def summary_screen() -> None:
    st.title("Case Closed")
    suspects = session.get_suspects()
    verdicts = session.get_verdicts()

    correct_count = 0
    for suspect_id, suspect in suspects.items():
        truth = "guilty" if suspect.guilty else "innocent"
        verdict = verdicts[suspect_id]
        is_correct = verdict == truth
        correct_count += is_correct
        icon = "✅" if is_correct else "❌"
        st.write(f"{icon} **{suspect.name}** — you said *{verdict}*, actually *{truth}*.")

    st.divider()
    st.write(f"You correctly identified **{correct_count} / {len(suspects)}** suspects.")
    st.write("Thank you for playing. Your anonymous responses have been recorded for the study.")
