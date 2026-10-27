"""
Post-hoc safety/consistency check on a suspect's drafted answer. Catches the
model breaking character, confessing outright, or contradicting established
case facts. On failure, suspect.py asks for one regeneration with a firmer
instruction; if that also fails, a safe fallback line is used instead.
"""

from llm.client import generate
from backend import load_prompt

_TEMPLATE = load_prompt("validator_v1.md")

FALLBACK_LINE = "I'd rather not get into that."


def check(draft_answer: str, suspect: dict, common_knowledge: str) -> str:
    """Returns 'OK', 'BREAKS_CHARACTER', 'CONFESSES', or 'CONTRADICTS_FACTS'."""
    prompt = _TEMPLATE.format(
        name=suspect["name"],
        role=suspect["role"],
        common_knowledge=common_knowledge,
        draft_answer=draft_answer,
    )
    reply = generate(system="", messages=[{"role": "user", "content": prompt}], max_tokens=10, temperature=0)
    reply = reply.upper()
    for label in ("BREAKS_CHARACTER", "CONFESSES", "CONTRADICTS_FACTS"):
        if label in reply:
            return label
    return "OK"
