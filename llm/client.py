"""
The only module in this project allowed to import the Anthropic SDK or know
about API keys. Everything else (router, policy, suspect, validator) calls
`generate()` and gets back plain text.
"""

import streamlit as st
import anthropic


@st.cache_resource
def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=st.secrets["llm"]["api_key"])


def generate(system: str, messages: list[dict], max_tokens: int = 300, temperature: float = 0.8) -> str:
    """messages: [{"role": "user" | "assistant", "content": str}, ...]"""
    model = st.secrets["llm"].get("model", "claude-sonnet-5")
    response = _client().messages.create(
        model=model,
        system=system,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.content[0].text.strip()
