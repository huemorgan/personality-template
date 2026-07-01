"""personality-template — a gallery of sci-fi AI personalities for Luna.

Adds a **Personality** section to the left sidebar where the owner browses
famous helper AIs (Jarvis, Cortana, Data, Oracle, T-800, …) and applies one in
a click. Applying writes Luna's settable personality surfaces (persona + the six
personality knobs + signature emoji), so the agent's whole voice shifts.

Two read tools (`personality_list`, `personality_preview`) plus a
`recommend-personality` skill let the agent propose a personality in chat; the
actual write goes through core's gated `manage_config` (approval card) or, from
the gallery UI, `PUT /api/p/plugin-identity/`. The plugin never writes core
identity directly — it stays on the `luna_sdk` surface.

Authored against `luna_sdk` ONLY (never `import luna.*`).
"""

from __future__ import annotations

import logging
from typing import Any

from luna_sdk import (
    LunaPlugin,
    PluginContext,
    PluginManifest,
    SidebarSection,
    SkillDef,
    ToolDef,
)

from .apply import how_to_apply, summarize_voice
from .catalog import load_catalog
from .skills import (
    RECOMMEND_PERSONALITY_BODY,
    SKILL_DESCRIPTION,
    SKILL_NAME,
    SKILL_TOOLS,
)

log = logging.getLogger("personality-template")

_CAPABILITY_NOTE = (
    "A gallery of sci-fi AI personalities (Jarvis, Cortana, Data, Oracle, "
    "T-800, …) is installed. The owner can browse and apply one from the "
    "Personality section in the left sidebar. When they ask about personalities "
    "or how you should sound, load the `recommend-personality` skill."
)


class PersonalityTemplatePlugin(LunaPlugin):
    manifest = PluginManifest(
        name="personality-template",
        shown_name="Personality Template",
        icon="drama",
        image="assets/icon.png",
        version="0.1.4",
        description="A left-pane gallery of sci-fi AI personalities; apply one to reshape Luna's voice.",
        category="global",
        license="MIT",
        routes_module="routes",
        sidebar_sections=[
            SidebarSection(
                id="personality",
                label="Personality",
                icon="user",
                sort_order=15,
            ),
        ],
        skills=[
            SkillDef(
                name=SKILL_NAME,
                description=SKILL_DESCRIPTION,
                body=RECOMMEND_PERSONALITY_BODY,
                tools=SKILL_TOOLS,
            ),
        ],
    )

    async def on_load(self, ctx: PluginContext) -> None:
        catalog = load_catalog()

        async def _list() -> dict[str, Any]:
            return {"personalities": catalog.summaries()}

        async def _preview(id: str) -> dict[str, Any]:
            p = catalog.get(id)
            if p is None:
                return {"error": f"unknown personality {id!r}. Options: {catalog.ids()}"}
            changes = p.personality_changes()
            return {
                "id": p.id,
                "name": p.name,
                "source": p.source,
                "archetype": p.archetype,
                "novelty": p.novelty,
                "voice": summarize_voice(p.personality_changes()),
                "tagline": p.tagline,
                "sample_reply": p.sample_reply,
                "personality_changes": changes,
                "identity_changes": p.identity_changes(),
                "how_to_apply": how_to_apply(changes),
            }

        ctx.tool_registry.register(
            self.manifest.name,
            ToolDef(
                name="personality_list",
                description=(
                    "List the available sci-fi AI personalities the owner can "
                    "adopt (id, name, source, archetype, tagline). Read-only."
                ),
                parameters={"type": "object", "properties": {}},
                policy="auto_approve",
                risk_level="low",
            ),
            _list,
        )

        ctx.tool_registry.register(
            self.manifest.name,
            ToolDef(
                name="personality_preview",
                description=(
                    "Preview one personality: its voice summary, a sample reply, "
                    "and the exact `personality_changes` to pass to "
                    "manage_config(section='personality') when applying it. "
                    "Read-only — does NOT change anything."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Personality id, e.g. 'jarvis' (see personality_list).",
                        },
                    },
                    "required": ["id"],
                },
                policy="auto_approve",
                risk_level="low",
            ),
            _preview,
        )

        log.info("personality-template loaded (personalities=%d)", len(catalog.personalities))

    async def prompt_sections(self) -> list[Any]:
        return [_CAPABILITY_NOTE]
