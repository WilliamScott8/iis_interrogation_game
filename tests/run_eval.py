#!/usr/bin/env python3
"""
Offline prompt eval: runs tests/cases.yaml through the real router against
the real story data and reports accuracy. This checks the router prompt
(prompts/router_v1.md), not the UI — run it after any change to that prompt
or to a suspect's knowledge_scope / out_of_scope_examples.

Usage:
    python tests/run_eval.py
Requires a valid API key in .streamlit/secrets.toml.
"""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import router  # noqa: E402

STORY_PATH = Path(__file__).resolve().parent.parent / "story" / "story_a.yaml"
CASES_PATH = Path(__file__).resolve().parent / "cases.yaml"


def main() -> int:
    story = yaml.safe_load(STORY_PATH.read_text())
    suspects_by_id = {s["id"]: s for s in story["suspects"]}
    cases = yaml.safe_load(CASES_PATH.read_text())

    passed = 0
    for case in cases:
        suspect = suspects_by_id[case["suspect_id"]]
        actual = router.classify_question(case["question"], suspect)
        ok = actual == case["expected"]
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {suspect['name']!r} / {case['question']!r} -> {actual} (expected {case['expected']})")

    print(f"\n{passed}/{len(cases)} cases passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
