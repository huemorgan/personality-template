"""Diff helpers."""

from __future__ import annotations

from personality_template.apply import diff, how_to_apply, summarize_voice
from personality_template.catalog import load_catalog


def test_diff_only_changed_fields():
    current = {"tone": "friendly", "verbosity": "balanced", "persona": "old"}
    changes = {"tone": "dry", "verbosity": "balanced", "persona": "new"}
    rows = diff(current, changes)
    fields = {r["field"] for r in rows}
    assert fields == {"tone", "persona"}  # verbosity unchanged → excluded


def test_diff_empty_when_identical():
    cur = {"tone": "dry", "verbosity": "terse"}
    assert diff(cur, dict(cur)) == []


def test_diff_treats_missing_as_changed():
    rows = diff({}, {"tone": "dry"})
    assert rows == [{"field": "tone", "from": None, "to": "dry"}]


def test_summarize_voice_orders_knobs():
    cat = load_catalog()
    s = summarize_voice(cat.get("data").personality_changes())
    assert "professional" in s and " · " in s


def test_how_to_apply_mentions_manage_config():
    text = how_to_apply({"persona": "x"})
    assert "manage_config" in text and "approval" in text
