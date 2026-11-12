# Prompt Log

Record every meaningful change to a prompt in `prompts/`, in order, so the
reasoning behind the current version is traceable. Add a new entry — don't
edit old ones — each time a `_v2`, `_v3`, ... file is added or an existing
prompt is materially edited.

## suspect_v1.md
- **2026-10-27** — Initial version. Character system prompt built from
  story.yaml fields (background, personality, alibi) plus a per-turn
  instruction slotted in by `backend/policy.py`. Explicit rules added against
  breaking character or confessing outright, since early manual testing
  showed the model would occasionally say "as an AI..." when pushed on
  out-of-context questions.

## router_v1.md
- **2026-10-27** — Initial version. Single-word classification
  (IN_CONTEXT / OUT_OF_CONTEXT) run as a separate cheap call before the
  suspect answers, rather than asking the suspect model to self-judge —
  keeps the decline/improvise manipulation consistent and auditable
  independent of the suspect's own roleplay.

## validator_v1.md
- **2026-10-27** — Initial version. Three failure modes checked
  (BREAKS_CHARACTER, CONFESSES, CONTRADICTS_FACTS). Runs after every suspect
  answer; a failure triggers one regeneration attempt in
  `backend/suspect.py` before falling back to a safe stock line.

## suspect_v2.md
- **2026-11-12** — Replaced v1. Two problems fixed:
  1. v1 hard-coded a different case ("the Ashworth Diamond Necklace from the
     Blackwood Gallery") left over from an earlier story, which contradicted
     the Canalside casino facts in `common_knowledge`. The opening line is now
     story-agnostic and points at the shared facts instead.
  2. v1 never gave the model `ground_truth` or `plot_hole`, so guilty
     suspects did not know they were guilty and could not cover for anything.
     v2 adds a private `{private_truth}` section, built in
     `backend/suspect.py` (`_private_truth`): guilty suspects are told their
     alibi is a cover story, what really happened, and the scripted
     confrontation lines for their plot hole; innocent suspects are told
     their account is true. A rule was added against revealing this section
     directly; the validator's CONFESSES check still backs this up.

## suspect_v3.md
- **2026-11-12** — Replaced v2. Danny (and sometimes Sarah) denied radioing
  maintenance during the 01:10 table drop, contradicting their own alibi.
  Cause: v2 showed the model `ground_truth` ("he never called maintenance")
  and the `plot_hole` fallback lines up front, and `llama3.2:3b` repeated the
  truth or jumped straight to "maybe I sorted it myself" unprompted.
  Changes:
  - New story fields `cover_story` (what a guilty suspect must always claim)
    and `secret` (what they must hide) replace `ground_truth`/`plot_hole` in
    the prompt. Those two fields are now researcher-facing only.
  - New `confrontation` field (`triggers` + `lines`). When a question contains
    a trigger phrase (e.g. "maintenance log", "21:40"), `Suspect.ask()` skips
    the router and LLM and returns the scripted line verbatim: line 1 the
    first time, line 2 after. Logged as classification `confrontation`,
    validator outcome `SCRIPTED`. Asking the model to say the line "word for
    word" was tried first: it paraphrased and invented new call times in
    every run, so the line is returned by code instead.
  - In-context turn instruction in `backend/policy.py` now points at "your
    account of your movements (and what you must always claim)".

## router_v1.md (story data change, prompt unchanged)
- **2026-11-12** — The router marked questions about the 01:10 drop ("Why
  did the table drop take 11 minutes?") OUT_OF_CONTEXT for both guilty
  suspects, so Sarah declined and Danny improvised a different story. Fixed
  in `story_a.yaml`: their `knowledge_scope` now spells out the lock jam and
  radio call instead of "cover story (see alibi)" (the router never sees the
  alibi), and look-alike out-of-scope examples were reworded to "on previous
  nights". A router_v2 adding an explicit "own openings are always
  IN_CONTEXT" rule was tried and dropped: it scored 11/15 then 7/15 on
  `tests/cases.yaml`, versus 15/15 for v1 with the new scope data.
  `tests/cases.yaml` was rewritten for the Canalside suspects (it still
  referenced an older story's suspects and could not run).

<!--
Add new entries below as prompts evolve, e.g.:

## router_v2.md
- **YYYY-MM-DD** — Changed X because Y (what broke, what evidence showed it,
  what changed).
-->
