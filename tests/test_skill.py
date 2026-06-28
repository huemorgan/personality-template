"""The recommend-personality skill: registered on the manifest, body drives the
gated apply via manage_config, and its tools exist."""

from __future__ import annotations

from conftest import FakeContext

from personality_template import PersonalityTemplatePlugin


def test_skill_declared():
    skills = PersonalityTemplatePlugin.manifest.skills
    assert len(skills) == 1
    skill = skills[0]
    assert skill.name == "recommend-personality"
    assert skill.body.strip()


def test_skill_body_drives_gated_apply():
    skill = PersonalityTemplatePlugin.manifest.skills[0]
    body = skill.body
    assert "manage_config" in body
    assert "personality_preview" in body
    assert "approv" in body.lower()  # mentions approval discipline


async def test_skill_tools_are_registered():
    skill = PersonalityTemplatePlugin.manifest.skills[0]
    plugin = PersonalityTemplatePlugin()
    ctx = FakeContext()
    await plugin.on_load(ctx)
    for t in skill.tools:
        assert t in ctx.tool_registry.tools, f"skill tool {t} not registered"


async def test_capability_note_present():
    plugin = PersonalityTemplatePlugin()
    sections = await plugin.prompt_sections()
    assert sections and "Personality" in sections[0]
