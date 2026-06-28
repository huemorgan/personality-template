"""Test-only stub for `luna_sdk`.

`luna_sdk` is provided by the Luna runtime at load time, not installed from PyPI.
To unit-test the plugin's logic (and let the package import) without a full Luna,
we register a minimal stand-in with the names the plugin imports. The real
contract is exercised inside Luna.
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from typing import Any


def _install_luna_sdk_stub() -> None:
    if "luna_sdk" in sys.modules:
        return

    mod = types.ModuleType("luna_sdk")

    @dataclass
    class ToolDef:
        name: str
        description: str = ""
        parameters: dict | None = None
        policy: str = "auto_approve"
        risk_level: str = "low"
        sensitive_args: list = field(default_factory=list)
        skill_gated: bool = False

    @dataclass
    class SkillDef:
        name: str
        description: str = ""
        body: str = ""
        plugin: str | None = None
        tools: list = field(default_factory=list)

    @dataclass
    class SidebarSection:
        id: str
        label: str
        icon: str = "file-text"
        sort_order: int = 50

    class PluginManifest:
        def __init__(self, **kw: Any) -> None:
            self.name = kw.get("name", "")
            self.version = kw.get("version", "")
            self.description = kw.get("description", "")
            self.category = kw.get("category")
            self.license = kw.get("license")
            self.routes_module = kw.get("routes_module")
            self.sidebar_sections = kw.get("sidebar_sections", [])
            self.skills = kw.get("skills", [])
            self.tools = kw.get("tools", [])

    class PluginContext:  # pragma: no cover - structural stand-in
        tool_registry: Any
        skill_registry: Any
        events: Any

    class LunaPlugin:  # pragma: no cover - structural stand-in
        manifest: PluginManifest

        async def on_load(self, ctx: "PluginContext") -> None: ...

    def get_current_user():  # pragma: no cover - not exercised in unit tests
        return None

    mod.ToolDef = ToolDef
    mod.SkillDef = SkillDef
    mod.SidebarSection = SidebarSection
    mod.PluginManifest = PluginManifest
    mod.PluginContext = PluginContext
    mod.LunaPlugin = LunaPlugin
    mod.get_current_user = get_current_user
    sys.modules["luna_sdk"] = mod


_install_luna_sdk_stub()


class FakeToolRegistry:
    """Records tool registrations made during on_load."""

    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}
        self.handlers: dict[str, Any] = {}

    def register(self, plugin: str, tool_def: Any, handler: Any, **_kw: Any) -> None:
        self.tools[tool_def.name] = tool_def
        self.handlers[tool_def.name] = handler


class FakeContext:
    def __init__(self) -> None:
        self.plugin_name = "personality-template"
        self.tool_registry = FakeToolRegistry()
