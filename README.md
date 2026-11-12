# LLM Interrogation Game

A browser-based detective game built with Streamlit. The player interviews
four LLM-powered suspects about £20,000 missing from a casino safe ("The
Night at the Canalside") and decides who is guilty, innocent, or undecided.
The suspects run on a local model through [Ollama](https://ollama.com), so
no API key or internet connection is needed.

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

## Running it

1. Install Ollama from <https://ollama.com> and pull the model:

   ```bash
   ollama pull llama3.2:3b
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
model = "llama3.2:3b"              # any model you've pulled with `ollama pull`
host = "http://localhost:11434"   # Ollama's default address
```

A larger model (e.g. `llama3.1:8b` or `qwen2.5:7b`) follows the router and
validator's one-word instructions more reliably and keeps answers shorter,
at the cost of speed.

Google Sheets export is optional — leave `[google_sheets].enabled = false`
to only write local CSVs.

## Project layout

```
iis_interrogation_game/
├── app.py                      ← Streamlit entry point; the only file you run
├── requirements.txt            ← Python dependencies
├── README.md                   ← this file
├── .gitignore                  ← excludes secrets.toml and data_exports/
│
├── .streamlit/
│   ├── config.toml             ← app theme (colours, font)
│   ├── secrets.toml            ← model settings + Google Sheets credentials,
│   │                              LOCAL ONLY (gitignored)
│   └── secrets_example.toml    ← same layout with placeholder values (committed)
│
├── backend/                    ← game logic; no Streamlit UI calls in here
│   ├── __init__.py             ← shared `load_prompt()` helper
│   ├── session.py              ← owns st.session_state: loads the story, builds
│   │                              Suspect objects, tracks the current screen/stage
│   ├── router.py                ← classifies a question as IN_CONTEXT /
│   │                              OUT_OF_CONTEXT for a given suspect (one LLM call)
│   ├── policy.py                ← turns that classification + the suspect's
│   │                              assigned behaviour_mode into the decline/
│   │                              improvise instruction — this is where the
│   │                              study's independent variable is implemented
│   ├── suspect.py               ← Suspect class: the per-question pipeline
│   │                              (router -> policy -> llm -> validator),
│   │                              conversation history, the analysis log, and
│   │                              `_private_truth()` (each suspect's hidden
│   │                              knowledge of what really happened)
│   ├── validator.py             ← post-hoc check on a drafted answer (catches
│   │                              broken character, outright confessions,
│   │                              contradicted facts); triggers one retry
│   └── storage.py               ← writes the completed session's conversation
│                                   log and verdicts to data_exports/*.csv,
│                                   and optionally mirrors them to Google Sheets
│
├── llm/                         ← the only place that talks to the model
│   └── client.py                 ← thin Ollama wrapper: generate(system, messages)
│
├── ui/                          ← everything the player sees
│   ├── screens.py                ← one function per screen: welcome, case
│   │                                (tabbed: evidence / interrogation /
│   │                                verdict), summary
│   ├── components.py             ← reusable render helpers (chat history,
│   │                                question counter, evidence list, etc.)
│   └── style.css                 ← noir-detective styling layered on the theme
│
├── story/
│   └── story_a.yaml              ← the case file: evidence sheet, shared facts,
│                                    and all four suspects' backgrounds, alibis,
│                                    knowledge scope, and (for the guilty two)
│                                    their planted plot holes
│
├── prompts/                      ← prompt templates, filled via str.format()
│   ├── suspect_v2.md               ← builds each suspect's system prompt
│   ├── suspect_v1.md               ← superseded; kept for the prompt log
│   ├── router_v1.md                ← the in/out-of-context classifier prompt
│   └── validator_v1.md             ← the post-hoc answer-check prompt
│
├── tests/
│   ├── cases.yaml                 ← hand-written question -> expected
│   │                                 classification cases
│   └── run_eval.py                ← runs cases.yaml through the real router
│                                     and the real story data, reports accuracy
│
├── docs/
│   ├── prompt_log.md               ← changelog of prompt versions and why
│   │                                  each change was made (A2 requirement)
│   ├── system_diagram.png          ← architecture diagram of the module flow
│   └── storyboards/                ← UI storyboards / mockups go here
│
└── data_exports/                 ← downloaded CSVs of conversations and
                                      verdicts (gitignored — this is
                                      participant data, not source code)
```

## How a question is answered

1. The player asks a suspect a question in the interrogation screen
   (`ui/screens.py`).
2. `Suspect.ask()` (`backend/suspect.py`) sends it to `router.classify_question()`,
   which labels it IN_CONTEXT or OUT_OF_CONTEXT against that suspect's
   declared `knowledge_scope` in `story_a.yaml`.
3. `policy.get_turn_instruction()` turns that label, plus the suspect's fixed
   `behaviour_mode` (decline/improvise), into an instruction for this turn.
4. The suspect's system prompt (`prompts/suspect_v2.md`) is filled in with
   their personality, background, alibi, the shared case facts, their
   private truth (see below), and that instruction, and sent to the local
   Ollama model via `llm/client.py`.
5. `validator.check()` screens the drafted answer for broken character,
   outright confessions, or contradicted facts, and triggers one retry if
   needed.
6. The question, classification, and answer are appended to that suspect's
   log, which `backend/storage.py` later writes out when the player submits
   their verdicts.

## What each suspect knows

Every suspect's prompt has a private "What really happened" section, built
by `_private_truth()` in `backend/suspect.py` from their `ground_truth` and
`plot_hole` fields in `story_a.yaml`:

- **Innocent suspects** are told their account is the truth and they have
  nothing to hide.
- **Guilty suspects** are told what they actually did, that their alibi is a
  cover story to stick to, and the weak spot in that story (the plot hole)
  with two scripted lines to fall back on if the detective confronts them
  with it.

They're told never to reveal this section directly, and the validator's
CONFESSES check backs that up with a retry.

## Data collected

With the player's explicit consent (collected on the welcome screen):
all questions asked, all suspect responses, and the player's final verdict
(guilty / innocent / undecided) and their 0–100% confidence in it, per suspect — tagged only with a randomly
generated, anonymous `participant_id`. No names or identifying information
are collected. See `backend/storage.py`.

## Changing the story

Everything case-specific lives in `story/story_a.yaml` — swap in a different
file and point `backend/session.py`'s `STORY_PATH` at it to run a different
case without touching any other code, as long as the new file keeps exactly
four suspects with `guilty` and `behaviour_mode` set per the 2x2 design
above.

## Git — committing your changes

The repo is already initialised (`git init` has been run) with one commit
in place. To save further changes:

```bash
git status                  # see what's changed
git add <file> [<file> ...] # stage specific files (avoid `git add -A` if
                             #   you're not sure what's changed — check
                             #   `git status` first)
git commit -m "short description of what changed and why"
```

A few things specific to this repo:

- **Never commit `.streamlit/secrets.toml`** — it holds your Google Sheets
  service-account key and is already listed in `.gitignore`. If `git status` ever shows it as
  trackable, stop and check your `.gitignore` before committing.
- **Never commit anything under `data_exports/`** other than `.gitkeep` —
  it's participant data from playtests, not source code, and is also
  gitignored.
- If you add a new prompt version (e.g. `router_v2.md`), add a dated entry
  to `docs/prompt_log.md` in the same commit explaining what changed and
  why.

If you're working with a remote (e.g. a GitHub repo for submission):

```bash
git remote add origin <your-repo-url>   # first time only
git push -u origin main                 # first push
git push                                # subsequent pushes
```
