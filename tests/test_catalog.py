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


def test_every_preset_has_catchphrases_and_gif_terms():
    cat = load_catalog()
    for p in cat.personalities:
        assert p.catchphrases, f"{p.id} has no catchphrases"
        assert p.gif_terms, f"{p.id} has no gif_terms"
        assert all(c.strip() for c in p.catchphrases)
        assert all(t.strip() for t in p.gif_terms)


def test_applied_persona_names_the_character():
    """The persona actually written on apply must tell the agent WHO it is and
    fold in the catchphrases — that is what makes it talk like the character."""
    cat = load_catalog()
    t800 = cat.get("t800")
    applied = t800.personality_changes()["persona"]
    assert "T-800" in applied
    assert "Terminator" in applied
    assert "I'll be back." in applied
    assert "Hasta la vista, baby." in applied
    # base behavioral text is still present after the in-character preamble
    assert t800.persona in applied
    # and it is genuinely longer than the raw persona (preamble was added)
    assert len(applied) > len(t800.persona)


def test_gif_guidance_references_send_gif_tool():
    cat = load_catalog()
    applied = cat.get("cortana").personality_changes()["persona"]
    assert "send_gif" in applied
    assert "Cortana Halo" in applied  # a gif_terms entry surfaces in guidance


def test_card_exposes_apply_persona_and_flavor():
    cat = load_catalog()
    card = cat.get("baymax").as_card()
    assert card["apply_persona"] != card["persona"]
    assert "Baymax" in card["apply_persona"]
    assert card["catchphrases"] and card["gif_terms"]
