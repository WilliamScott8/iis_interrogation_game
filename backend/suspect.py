"""
Suspect: wraps one suspect's story data + conversation history and is the
single entry point the UI calls to ask a question. Internally it chains
router -> policy -> llm.client -> validator for every turn, and keeps the
per-question log that storage.py later exports for analysis.
"""

from llm.client import generate
from backend import router, policy, validator, load_prompt

MAX_QUESTIONS = 8

_SUSPECT_TEMPLATE = load_prompt("suspect_v1.md")


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

    def ask(self, question: str) -> str:
        if self.questions_remaining() <= 0:
            raise ValueError(f"{self.name} has already answered the maximum of {MAX_QUESTIONS} questions.")

        classification = router.classify_question(question, self.data)
        turn_instruction = policy.get_turn_instruction(classification, self.data)
        system_prompt = _SUSPECT_TEMPLATE.format(
            name=self.data["name"],
            role=self.data["role"],
            personality=self.data["personality"],
            background=self.data["background"],
            common_knowledge=self.common_knowledge,
            alibi=self.data["alibi_given_to_player"],
            turn_instruction=turn_instruction,
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
