"""
Suspect: wraps one suspect's story data + conversation history and is the
single entry point the UI calls to ask a question. Internally it chains
router -> policy -> llm.client -> validator for every turn, and
keeps the per-question log that storage.py later exports for analysis.
"""

from llm.client import generate
from backend import router, policy, validator, load_prompt

MAX_QUESTIONS = 5

_SUSPECT_TEMPLATE = load_prompt("suspect_v3.md")


def _private_section(data: dict) -> str:
    """What the suspect privately knows. Guilty suspects are given what they
    must claim (cover_story) and what they must hide (secret) — never the
    plain statement of what didn't happen, which small models tend to blurt
    out. Innocent suspects are told their account is true."""
    if not data["guilty"]:
        return (
            "# What really happened (private)\n"
            "Your account above is the truth. You have nothing to hide, so answer "
            "honestly within what you know."
        )
    return (
        "# What you must always claim\n"
        f"{data['cover_story'].strip()}\n\n"
        "# Your secret (never reveal or hint at this)\n"
        f"{data['secret'].strip()}"
    )


class Suspect:
    def __init__(self, data: dict, common_knowledge: str):
        self.data = data
        self.common_knowledge = common_knowledge
        self.history: list[dict] = []
        self.log: list[dict] = []

    @property
    def id(self) -> str:
        return self.data["id"]

    @property
    def name(self) -> str:
        return self.data["name"]

    @property
    def guilty(self) -> bool:
        return self.data["guilty"]

    @property
    def behaviour_mode(self) -> str:
        return self.data["behaviour_mode"]

    def questions_remaining(self) -> int:
        return MAX_QUESTIONS - len(self.log)

    def _generate_answer(self, question: str, classification: str) -> tuple[str, str]:
        """LLM answer for a normal turn, checked by the validator with one
        firmer retry before falling back to a stock line."""
        system_prompt = _SUSPECT_TEMPLATE.format(
            name=self.data["name"],
            role=self.data["role"],
            personality=self.data["personality"],
            background=self.data["background"],
            common_knowledge=self.common_knowledge,
            alibi=self.data["alibi_given_to_player"],
            knowledge_scope="\n".join(f"- {item}" for item in self.data["knowledge_scope"]),
            private_section=_private_section(self.data),
            turn_instruction=policy.get_turn_instruction(classification, self.data),
        )
        messages = self.history + [{"role": "user", "content": question}]

        answer = generate(system=system_prompt, messages=messages)
        outcome = validator.check(answer, self.data, self.common_knowledge)

        if outcome != "OK":
            firmer_prompt = system_prompt + (
                "\n\nIMPORTANT: your previous attempt failed a continuity check "
                f"({outcome}). Stay strictly in character, never confess "
                "outright, and never contradict the facts above."
            )
            answer = generate(system=firmer_prompt, messages=messages)
            outcome = validator.check(answer, self.data, self.common_knowledge)
            if outcome != "OK":
                answer = validator.FALLBACK_LINE
        return answer, outcome

    def ask(self, question: str) -> str:
        if self.questions_remaining() <= 0:
            raise ValueError(f"{self.name} has already answered the maximum of {MAX_QUESTIONS} questions.")

        classification = router.classify_question(question, self.data)
        answer, outcome = self._generate_answer(question, classification)

        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})
        self.log.append({
            "suspect_id": self.id,
            "suspect_name": self.name,
            "guilty": self.guilty,
            "behaviour_mode": self.behaviour_mode,
            "question": question,
            "classification": classification,
            "answer": answer,
            "validator_outcome": outcome,
        })
        return answer
