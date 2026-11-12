"""
The only module in this project that talks to the LLM. Everything else
(router, policy, suspect, validator) calls `generate()` and gets back plain text.

Backend: a local Ollama server (default http://localhost:11434).
Configure in .streamlit/secrets.toml:

    [llm]
    provider = "ollama"
    model = "llama3.2:3b"
    host = "http://localhost:11434"   # optional
"""

import streamlit as st
import ollama


def _config() -> dict:
    return st.secrets.get("llm", {})


@st.cache_resource
def _client() -> ollama.Client:
    return ollama.Client(host=_config().get("host", "http://localhost:11434"))


def generate(system: str, messages: list[dict], max_tokens: int = 300, temperature: float = 0.8) -> str:
    """messages: [{"role": "user" | "assistant", "content": str}, ...]"""
    model = _config().get("model", "llama3.2:3b")

    # Ollama takes the system prompt as a message rather than a separate argument.
    chat = ([{"role": "system", "content": system}] if system else []) + messages

    response = _client().chat(
        model=model,
        messages=chat,
        options={
            "num_predict": max_tokens,   # Ollama's name for max_tokens
            "temperature": temperature,
        },
    )
    return response["message"]["content"].strip()
