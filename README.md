# personality-template

A **Personality** section in Luna's left sidebar. Browse a gallery of famous
sci-fi helper AIs — Jarvis, Cortana, Data, Oracle, T-800, Baymax, Marvin, and
more — and apply one in a click. Applying reshapes Luna's settable prompt
surfaces (persona + tone, verbosity, formality, emoji use, proactivity, honesty,
and the signature emoji), so the agent's whole voice shifts. Reversible at any
time via **Reset to default Luna**.

The roster, research, and the per-character → Luna mapping live in
`plans/003-personality-template/RESEARCH-personalities.md`.

## How it works

- **Catalog** is data: `personality_template/presets.toml` (15 presets), each a
  bundle of *legal* Luna identity/personality values (validated at load).
- **Gallery UI** (`ui/`) is a left-pane iframe. Its **Apply** button writes the
  chosen preset to your identity via core's own `PUT /api/p/plugin-identity/`.
- **Agent path**: the `recommend-personality` skill lets Luna propose a fitting
  personality in chat. Setting it always goes through Luna's gated
  `manage_config` (an approval card) — nothing changes without your yes.

This plugin authors against `luna_sdk` only and never writes core identity
directly; every write goes through a sanctioned, approval-gated core surface.

## Tools

| Tool | Policy | Purpose |
|---|---|---|
| `personality_list()` | auto_approve / low | List the available personalities. |
| `personality_preview(id)` | auto_approve / low | One personality's voice + the exact change set. |

## Local test

```bash
cd plugins/personality-template
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest -q
```

## Avatars

Each preset ships a dry 3D-render profile avatar in `ui/avatars/<id>.png`
(generated for plan 003; original archetype interpretations, not exact
movie-character likenesses).

Source: https://github.com/huemorgan/personality-template
