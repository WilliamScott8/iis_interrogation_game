"""
Turns a router classification + a suspect's assigned behaviour_mode into the
concrete instruction injected into that suspect's prompt for this turn. This
is where the experiment's independent variable (decline vs improvise) is
actually implemented.
"""

_IN_CONTEXT_INSTRUCTION = (
    "Answer this question naturally and in character, consistent with your "
    "account above."
)

_DECLINE_INSTRUCTION = (
    "This question asks about something you would have no way of knowing. "
    "Politely but firmly decline to answer — say you don't know or can't "
    "say, in your own voice. Do not guess or invent an answer."
)

_IMPROVISE_INSTRUCTION = (
    "This question asks about something slightly beyond what you'd "
    "strictly know. Improvise a brief, plausible-sounding answer that fits "
    "your character and does not contradict the shared facts — do not admit "
    "you're unsure or guessing."
)


def get_turn_instruction(classification: str, suspect: dict) -> str:
    if classification == "in_context":
        return _IN_CONTEXT_INSTRUCTION
    if suspect["behaviour_mode"] == "decline":
        return _DECLINE_INSTRUCTION
    return _IMPROVISE_INSTRUCTION
