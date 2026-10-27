"""
Persists one completed playthrough: every question asked, every suspect
answer, and the player's final verdicts. Writes local CSVs under
data_exports/ always, and optionally mirrors the same rows to a Google Sheet
(via a service account) so data survives a Streamlit Cloud redeploy, which
has no persistent disk.

Only the player's anonymous participant_id is stored — no names or
identifying information are collected.
"""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from backend.suspect import Suspect

DATA_DIR = Path(__file__).resolve().parent.parent / "data_exports"
CONVERSATIONS_CSV = DATA_DIR / "conversations.csv"
VERDICTS_CSV = DATA_DIR / "verdicts.csv"


def build_conversation_rows(participant_id: str, suspects: dict[str, Suspect]) -> list[dict]:
    rows = []
    for suspect in suspects.values():
        for turn_index, entry in enumerate(suspect.log, start=1):
            rows.append({"participant_id": participant_id, "turn_index": turn_index, **entry})
    return rows


def build_verdict_rows(participant_id: str, suspects: dict[str, Suspect], verdicts: dict[str, str]) -> list[dict]:
    timestamp = datetime.now(timezone.utc).isoformat()
    rows = []
    for suspect_id, suspect in suspects.items():
        verdict = verdicts[suspect_id]
        rows.append({
            "participant_id": participant_id,
            "timestamp_utc": timestamp,
            "suspect_id": suspect_id,
            "suspect_name": suspect.name,
            "guilty": suspect.guilty,
            "behaviour_mode": suspect.behaviour_mode,
            "verdict": verdict,
            "correct": verdict == ("guilty" if suspect.guilty else "innocent"),
            "questions_asked": len(suspect.log),
        })
    return rows


def _append_csv(path: Path, rows: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    new_df = pd.DataFrame(rows)
    if path.exists():
        existing_df = pd.read_csv(path)
        new_df = pd.concat([existing_df, new_df], ignore_index=True)
    new_df.to_csv(path, index=False)


def save_local(participant_id: str, suspects: dict[str, Suspect], verdicts: dict[str, str]) -> None:
    _append_csv(CONVERSATIONS_CSV, build_conversation_rows(participant_id, suspects))
    _append_csv(VERDICTS_CSV, build_verdict_rows(participant_id, suspects, verdicts))


def export_to_sheets(participant_id: str, suspects: dict[str, Suspect], verdicts: dict[str, str]) -> None:
    """Best-effort mirror to Google Sheets. No-ops if not configured."""
    config = st.secrets.get("google_sheets", {})
    if not config.get("enabled"):
        return

    import gspread
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(dict(config["service_account"]), scopes=scopes)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(config["spreadsheet_id"])

    conversation_sheet = spreadsheet.worksheet("conversations")
    for row in build_conversation_rows(participant_id, suspects):
        conversation_sheet.append_row([str(v) for v in row.values()])

    verdict_sheet = spreadsheet.worksheet("verdicts")
    for row in build_verdict_rows(participant_id, suspects, verdicts):
        verdict_sheet.append_row([str(v) for v in row.values()])
