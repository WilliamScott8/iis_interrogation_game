import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Matches <!-- ... --> developer notes in prompt templates (including multi-line).
_COMMENT = re.compile(r"<!--.*?-->\s*", re.DOTALL)


def load_prompt(filename: str) -> str:
    """Load a prompt template with its <!-- --> developer notes stripped, so
    they never reach the model (and placeholders inside them are not filled)."""
    text = (PROMPTS_DIR / filename).read_text()
    return _COMMENT.sub("", text).strip() + "\n"
