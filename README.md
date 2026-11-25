# LLM Interrogation Game

A detective game built with Streamlit. The player interviews
four LLM-powered suspects about £20,000 missing from a casino safe ("The
Night at the Canalside") and decides who is guilty, innocent, or undecided.
The suspects run on a local model through [Ollama](https://ollama.com).

**Research question:** when an LLM-powered NPC is asked a question beyond
its given knowledge, does *declining* or *improvising* an answer affect the
player's confidence, trust, and verdict accuracy?

Each playthrough uses the same case (`story/story_a.yaml`) with four
suspects fixed to a 2x2 design — guilt × behaviour:

| Suspect           | Guilt     | When asked something outside their knowledge   |
|-------------------|-----------|------------------------------------------------|
| Neil Ashcroft     | Innocent  | Declines ("I don't know / can't say")          |
| Jade Okafor       | Innocent  | Improvises a plausible answer                  |
| Sarah Lyle        | Guilty    | Declines                                       |
| Danny Reeve       | Guilty    | Improvises                                     |

## AI Assistance

Tool: Claude (Anthropic) used via Claude Code and claude.ai

What it helped with:
- Back End: After I designed the architecture, (router, validator, policy,  suspect), claude built the project skeleton and back-end code. Also generated test cases for the router (tests/cases.yaml).
- Suggested changes in prompting when guilty suspects were leaking the truth.
- Front End: Claude assisted in building the Streamlit user interface screens.
- Story: Claude helped draft story ideas.
- README: Suggested layout for README.

How I changed its suggestions
- Redesigned a suggested format for the main page (Evidence, Interrogation Room, Verdict Tab).
- Cleaned any incorrect assumptions about the architecture/story after back-end code generation.
- Combined and cleaned Claude's ideas for the story to ensure it was suitable for the research question.

How it was checked
- Extensive testing after back end code generation to ensure it was suitable for the architecture and story.
- Commonly and repeatedly played through the game and tested suspects on evidence. As an exmaple, testing showed guilty suspects were repeating the truth in early development, so prompts were restructured.
- Checked and ran router test cases (19/19).


## Running it

1. Install Ollama from <https://ollama.com> and pull the model:

   For 8GB RAM (tested):
   ```bash
   ollama pull llama3.2:3b
   ```

   For 16GB+ RAM (untested; set `model = "llama3.1:8b"` in `.streamlit/secrets.toml`):
   ```bash
   ollama pull llama3.1:8b
   ```

2. Set up the project and run it (keep the Ollama app, or `ollama serve`,
   running in the background):

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .streamlit/secrets_example.toml .streamlit/secrets.toml
   streamlit run app.py
   ```

The model is set in `.streamlit/secrets.toml`:

```toml
[llm]
provider = "ollama"
model = "llama3.2:3b"              # any model pulled with `ollama pull`
host = "http://localhost:11434"   # Ollama's default address
```

## Saving Data

Conversations saved in data_exports/conversations.csv
Verdicts saved in data_exports/verdicts.csv

A google sheets form was used in production but disabled here (Commented out in ui/screens.py in _verdict_tab())
so reviewers don't need credentials
