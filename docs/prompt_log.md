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

<!--
Add new entries below as prompts evolve, e.g.:

## router_v2.md
- **YYYY-MM-DD** — Changed X because Y (what broke, what evidence showed it,
  what changed).
-->
