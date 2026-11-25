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

## Project Structure

```
iis_interrogation_game/
├── app.py                      ← Streamlit entry point
├── requirements.txt
├── README.md
├── .gitignore                  ← excludes secrets.toml and data_exports/
│
├── .streamlit/
│   ├── config.toml             ← app theme (colours, font) + server/browser settings
│   ├── secrets.toml            ← model settings + Google Sheets credentials
│   │                              (gitignored; copy from secrets_example.toml)
│   └── secrets_example.toml    ← secrets.toml layout with placeholder values
│
├── backend/                    ← game logic
│   ├── __init__.py             ← load_prompt(): reads a prompt template and
│   │                              strips its <!-- --> developer notes
│   ├── session.py              ← owns st.session_state: loads the story, builds
│   │                              Suspect objects, generates the anonymous
│   │                              participant_id, tracks the current stage,
│   │                              selected suspect, verdicts and confidence
│   ├── router.py               ← classifies a question as IN_CONTEXT /
│   │                              OUT_OF_CONTEXT for a given suspect (one LLM call)
│   ├── policy.py               ← turns that classification + the suspect's
│   │                              assigned behaviour_mode into the decline/
│   │                              improvise instruction — this is where the
│   │                              study's independent variable is implemented
│   ├── suspect.py              ← Suspect class: the per-question pipeline
│   │                              (router -> policy -> llm -> validator),
│   │                              conversation history, the analysis log,
│   │                              `_private_section()` (what each suspect must
│   │                              claim / hide)
│   ├── validator.py            ← post-hoc check on a drafted answer (catches
│   │                              broken character, outright confessions,
│   │                              contradicted facts); triggers one retry,
│   │                              then a stock fallback line
│   └── storage.py              ← writes the completed session's conversation
│                                  log and verdicts to data_exports/*.csv;
│                                  can also mirror them to Google Sheets
│                                  (disabled in ui/screens.py)
│
├── llm/                        ← the only place that talks to the model
│   ├── __init__.py
│   └── client.py               ← Ollama wrapper: generate(system, messages)
│
├── ui/                         ← everything the player sees
│   ├── __init__.py
│   ├── screens.py              ← one function per screen: welcome, case
│   │                              (tabbed: evidence / interrogation /
│   │                              verdict), summary
│   ├── components.py           ← reusable render helpers (chat history,
│   │                              question counter, evidence and safe-opening
│   │                              lists, confidence slider, verdict options)
│   └── style.css               ← noir-detective styling layered on the theme
│
├── story/
│   └── story_a.yaml            ← the case file: case briefing, evidence sheet,
│                                  shared facts, solution, and all four
│                                  suspects' backgrounds, alibis, knowledge
│                                  scope and, for the guilty two, their cover
│                                  story, secret and planted plot hole
│
├── prompts/                    ← prompt templates, filled via str.format()
│   ├── suspect.md              ← builds each suspect's system prompt
│   ├── router.md               ← the in/out-of-context classifier prompt
│   └── validator.md            ← the post-hoc answer-check prompt
│
├── tests/
│   ├── cases.yaml              ← hand-written question -> expected
│   │                              classification cases (Canalside suspects)
│   └── run_eval.py             ← runs cases.yaml through the real router
│                                  and the real story data, reports accuracy
│
├── docs/
│   ├── prompt_log.md           ← changelog of prompt versions and why
│   │                              each change was made (A2 requirement)
│   ├── System_Diagram.pdf      ← architecture diagram of the module flow
│   ├── AI_Behaviour_Flowchart.pdf ← how a suspect's reply is produced
│   └── storyboards/            ← UI storyboards / mockups go here
│
└── data_exports/               ← CSVs of conversations and verdicts written
                                   by storage.py (gitignored — participant
                                   data, not source code)
```

## How a question is answered

1. The player asks a suspect a question in the Interrogation Room tab of the
   case screen (`_interrogation_tab()` in `ui/screens.py`).
2. `Suspect.ask()` (`backend/suspect.py`) sends the question to
   `router.classify_question()`, which labels it IN_CONTEXT or
   OUT_OF_CONTEXT using that suspect's `knowledge_scope` and
   `out_of_scope_examples` from `story_a.yaml`.
3. `policy.get_turn_instruction()` turns that label, plus the suspect's fixed
   `behaviour_mode` (decline/improvise), into an instruction for this turn.
4. The suspect's system prompt (`prompts/suspect.md`) is filled in with
   their name, role, personality, background, the shared case facts, their
   alibi, their knowledge scope, their private section (see below) and that
   instruction, and sent to the local Ollama model via `llm/client.py`.
5. `validator.check()` screens the drafted answer for broken character,
   outright confessions, or contradicted facts. If it fails, the answer is
   regenerated once with a firmer instruction; if that also fails, the
   suspect gives the stock line "I'd rather not get into that."
6. The question, classification (`in_context` or `out_of_context`), answer
   and validator outcome are appended to that suspect's log, along with the
   suspect's ID, name, `guilty` and `behaviour_mode`. `backend/storage.py`
   writes the log out when the player submits their verdicts.

## What each suspect knows

Every suspect's prompt has a private section, built by `_private_section()`
in `backend/suspect.py`:

- **Innocent suspects** are told their account is the truth and they have
  nothing to hide.
- **Guilty suspects** get two fields from `story_a.yaml`: `cover_story`
  (what they must always claim, e.g. "you radioed maintenance") and
  `secret` (what they did and must never reveal). They are deliberately
  *not* shown `ground_truth` or `plot_hole`. Those fields are for the
  researcher only and are not read by any code; the Case Closed screen shows
  the story's `solution` field instead. Small models given the plain truth
  ("he never called maintenance") tend to repeat it.

**The plot hole.** No suspect is told what the maintenance call log
contains, so a question confronting Sarah or Danny with it (no call during
the 01:10 drop) is classified OUT_OF_CONTEXT and handled by their normal
decline/improvise instruction. There are no scripted replies; the guilty
suspects respond to the plot hole the same way as to any other
out-of-knowledge question. `tests/cases.yaml` covers this.

The validator's CONFESSES check backs up the rule against confessing, with
one retry. The validator never sees the secret, so it only catches an
outright admission of guilt, not a hint or partial leak.

## Data collected

With the player's explicit consent (a checkbox on the welcome screen that
must be ticked before the case starts), each session is tagged only with a
randomly generated, anonymous `participant_id` (a UUID). No names or
identifying information are collected. See `backend/storage.py`.

- **Conversations** (one row per question): turn number, suspect ID and
  name, `guilty`, `behaviour_mode`, the question, the router's
  classification, the suspect's answer and the validator outcome.
- **Verdicts** (one row per suspect): UTC timestamp, suspect ID and name,
  `guilty`, `behaviour_mode`, the player's verdict (guilty / innocent /
  undecided), their 0–100 confidence (blank if undecided), whether the
  verdict was correct, and how many questions they asked that suspect.
