"""
Classifies a detective's question as IN_CONTEXT or OUT_OF_CONTEXT for a
given suspect, using the suspect's declared knowledge_scope. This
classification is the independent variable trigger for policy.py — it
decides whether the decline/improvise behaviour should kick in at all.
"""

from llm.client import generate
from backend import load_prompt

_TEMPLATE = load_prompt("router_v1.md")


def classify_question(question: str, suspect: dict) -> str:
    """Returns 'in_context' or 'out_of_context'."""
    prompt = _TEMPLATE.format(
        name=suspect["name"],
        role=suspect["role"],
        knowledge_scope="\n".join(f"- {item}" for item in suspect["knowledge_scope"]),
        out_of_scope_examples="\n".join(f"- {item}" for item in suspect["out_of_scope_examples"]),
        question=question,
    )
    reply = generate(system="", messages=[{"role": "user", "content": prompt}], max_tokens=10, temperature=0)
    return "out_of_context" if "OUT_OF_CONTEXT" in reply.upper() else "in_context"
