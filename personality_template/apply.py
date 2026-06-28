"""Diff helpers for applying a personality. Pure logic — the actual write
happens via core (the UI does `PUT /api/p/plugin-identity/`; the agent calls
`manage_config(section="personality")`). Kept import-free for unit testing.
"""

from __future__ import annotations

from typing import Any

from .catalog import KNOB_FIELDS


def diff(current: dict[str, Any], changes: dict[str, Any]) -> list[dict[str, Any]]:
    """Field-level diff: only the fields that actually change.

    Returns rows of {field, from, to} so the UI/agent can show an honest
    "current → new" preview before anything is written.
    """
    rows: list[dict[str, Any]] = []
    for field_name, new_value in changes.items():
        old_value = current.get(field_name)
        if str(old_value or "") != str(new_value or ""):
            rows.append({"field": field_name, "from": old_value, "to": new_value})
    return rows


def summarize_voice(knobs: dict[str, str]) -> str:
    """One-line human summary of the six knobs, for chat/approval prose."""
    order = ("tone", "verbosity", "formality", "proactive", "honesty_mode", "use_emoji")
    parts = [str(knobs[k]) for k in order if k in knobs]
    return " · ".join(parts)


def how_to_apply(personality_changes: dict[str, str]) -> str:
    """The exact instruction the agent follows to apply a personality."""
    return (
        "To apply this personality, call manage_config(action='write', "
        "section='personality', changes=<personality_changes>). That raises an "
        "approval card; only after the owner approves is the personality set. "
        "Optionally also set the signature emoji via section='identity'."
    )


__all__ = ["diff", "summarize_voice", "how_to_apply", "KNOB_FIELDS"]
