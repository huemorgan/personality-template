"""Catalog validity: every preset parses, all enum values are legal, ids are
unique, and each ships an avatar."""

from __future__ import annotations

from pathlib import Path

from personality_template.catalog import (
    ALLOWED_VALUES,
    KNOB_FIELDS,
    load_catalog,
)

_UI_AVATARS = Path(__file__).resolve().parents[1] / "personality_template" / "ui" / "avatars"

EXPECTED_IDS = {
    "data", "doctor", "tars", "marvin", "jarvis", "cortana", "kitt", "vision",
    "friday", "jane", "samantha", "baymax", "oracle", "johnny", "t800",
}


def test_loads_all_presets():
    cat = load_catalog()
    assert len(cat.personalities) == 15
    assert set(cat.ids()) == EXPECTED_IDS


def test_ids_unique():
    cat = load_catalog()
    ids = cat.ids()
    assert len(ids) == len(set(ids))


def test_enum_values_legal():
    cat = load_catalog()
    for p in cat.personalities:
        for knob in KNOB_FIELDS:
            assert getattr(p, knob) in ALLOWED_VALUES[knob], (
                f"{p.id}.{knob}={getattr(p, knob)!r} illegal"
            )


def test_persona_nonempty():
    cat = load_catalog()
    for p in cat.personalities:
        assert p.persona.strip(), f"{p.id} has empty persona"
        assert p.tagline.strip()
        assert p.sample_reply.strip()


def test_one_novelty():
    cat = load_catalog()
    novelty = [p.id for p in cat.personalities if p.novelty]
    assert novelty == ["marvin"]


def test_every_preset_has_avatar():
    cat = load_catalog()
    for p in cat.personalities:
        assert (_UI_AVATARS / f"{p.id}.png").exists(), f"missing avatar for {p.id}"


def test_personality_changes_shape():
    cat = load_catalog()
    p = cat.get("jarvis")
    changes = p.personality_changes()
    assert set(changes) == {"persona", *KNOB_FIELDS}
    assert p.identity_changes() == {"emoji": p.emoji}


def test_match_active_and_default():
    cat = load_catalog()
    jarvis = cat.get("jarvis")
    current = {**jarvis.personality_changes()}
    assert cat.match_active(current) == "jarvis"
    assert cat.match_active({"persona": "something else"}) is None
