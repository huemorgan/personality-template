"""Data manifest <-> PluginManifest agreement, and the no-core-import guard."""

from __future__ import annotations

import re
from pathlib import Path

from conftest import FakeContext

from personality_template import PersonalityTemplatePlugin

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

_PKG = Path(__file__).resolve().parents[1] / "personality_template"
_TOML = _PKG / "luna-plugin.toml"


def _manifest_toml() -> dict:
    return tomllib.loads(_TOML.read_text(encoding="utf-8"))


def test_identity_matches():
    data = _manifest_toml()
    m = PersonalityTemplatePlugin.manifest
    assert data["name"] == m.name == "personality-template"
    assert data["version"] == m.version
    assert data["entry"] == "personality_template"


def test_tool_count_consistent():
    data = _manifest_toml()
    declared = data["requires"]["tools"]
    listed = data.get("tools", [])
    assert declared == len(listed) == 2


async def test_registered_tools_match_toml():
    data = _manifest_toml()
    listed_names = {t["name"] for t in data["tools"]}
    plugin = PersonalityTemplatePlugin()
    ctx = FakeContext()
    await plugin.on_load(ctx)
    assert set(ctx.tool_registry.tools) == listed_names


def test_no_forbidden_core_imports():
    """Plugins import `luna_sdk` only — never `import luna.` / `from luna.`."""
    bad = re.compile(r"^\s*(from|import)\s+luna(\.|\s|$)")
    offenders: list[str] = []
    for py in _PKG.rglob("*.py"):
        for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if bad.match(line) and "luna_sdk" not in line:
                offenders.append(f"{py.name}:{i}: {line.strip()}")
    assert not offenders, "forbidden core imports:\n" + "\n".join(offenders)
