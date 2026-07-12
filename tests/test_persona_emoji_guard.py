"""034/phase04: emoji-averse presets must carry an explicit no-emoji guard in
their composed persona, so the in-character preamble (catchphrases, GIFs,
expressiveness) can never re-permit what the use_emoji knob forbids."""

from __future__ import annotations

from personality_template.catalog import load_catalog

GUARD_SNIPPET = "never uses emoji"


def test_never_presets_carry_guard():
    cat = load_catalog()
    never = [p for p in cat.personalities if p.use_emoji == "never"]
    assert never, "catalog has no use_emoji=never presets?"
    for p in never:
        persona = p.full_persona()
        assert GUARD_SNIPPET in persona, f"{p.id} missing no-emoji guard"
        assert "No emoji in any reply, ever" in persona, p.id


def test_data_guard_wording():
    p = load_catalog().get("data")
    assert p is not None and p.use_emoji == "never"
    assert "Data never uses emoji" in p.full_persona()


def test_non_never_presets_unguarded():
    cat = load_catalog()
    johnny = cat.get("johnny")
    assert johnny is not None and johnny.use_emoji == "always"
    assert GUARD_SNIPPET not in johnny.full_persona()
    for p in cat.personalities:
        if p.use_emoji != "never":
            assert GUARD_SNIPPET not in p.full_persona(), p.id
