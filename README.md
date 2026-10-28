# LLM Interrogation Game

A browser-based detective game built with Streamlit. The player interviews
four LLM-powered suspects about a robbery and decides who is guilty,
innocent, or undecided.

**Research question:** when an LLM-powered NPC is asked a question beyond
its given knowledge, does *declining* or *improvising* an answer affect the
player's confidence, trust, and verdict accuracy?

Each playthrough uses the same case (`story/story_a.yaml`) with four
suspects fixed to a 2x2 design — guilt × behaviour:

| Suspect           | Guilt     | When asked something outside their knowledge   |
|-------------------|-----------|------------------------------------------------|
| Suspect 1         | Innocent  | Declines ("I don't know / can't say")          |
| Suspect 2         | Innocent  | Improvises a plausible answer                  |
| Suspect 3         | Guilty    | Declines                                       |
| Suspect 4         | Guilty    | Improvises                                     |

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets_example.toml .streamlit/secrets.toml   # then edit it
streamlit run app.py
```

You need an Anthropic API key in `.streamlit/secrets.toml` (`[llm].api_key`).
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
│   ├── secrets.toml            ← real API keys, LOCAL ONLY (gitignored)
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
│   │                              conversation history, and the analysis log
│   ├── validator.py             ← post-hoc check on a drafted answer (catches
│   │                              broken character, outright confessions,
│   │                              contradicted facts); triggers one retry
│   └── storage.py               ← writes the completed session's conversation
│                                   log and verdicts to data_exports/*.csv,
│                                   and optionally mirrors them to Google Sheets
│
├── llm/                         ← the only place that talks to the model API
│   └── client.py                 ← thin Anthropic SDK wrapper: generate(system, messages)
│
├── ui/                          ← everything the player sees
│   ├── screens.py                ← one function per screen: welcome, evidence,
│   │                                interrogation, verdict, summary
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
│   ├── suspect_v1.md               ← builds each suspect's system prompt
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
4. The suspect's system prompt (`prompts/suspect_v1.md`) is filled in with
   their background, alibi, and that instruction, and sent to
   `llm/client.py`.
5. `validator.check()` screens the drafted answer for broken character,
   outright confessions, or contradicted facts, and triggers one retry if
   needed.
6. The question, classification, and answer are appended to that suspect's
   log, which `backend/storage.py` later writes out when the player submits
   their verdicts.

## Data collected

With the player's explicit consent (collected on the welcome screen):
all questions asked, all suspect responses, and the player's final verdict
(guilty / innocent / undecided) per suspect — tagged only with a randomly
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

- **Never commit `.streamlit/secrets.toml`** — it holds your real API key
  and is already listed in `.gitignore`. If `git status` ever shows it as
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
