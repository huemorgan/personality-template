"""Load + validate the personality catalog. Pure data; no `luna_sdk` import,
so it is unit-testable without the Luna runtime.

A "personality" is a bundle of legal Luna identity/personality values. Applying
one writes the `personality` config section (persona + the six knobs) and,
optionally, the `emoji` identity field. We mirror — not import — core's
`ALLOWED_VALUES` so a bad preset fails fast at load time even in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

_PRESETS_FILE = Path(__file__).parent / "presets.toml"

# Mirror of luna.identity.service.ALLOWED_VALUES (kept in sync; guarded by tests).
ALLOWED_VALUES: dict[str, tuple[str, ...]] = {
    "tone": ("friendly", "warm", "playful", "dry", "formal", "professional", "minimal"),
    "verbosity": ("terse", "balanced", "detailed"),
    "formality": ("casual", "neutral", "formal"),
    "use_emoji": ("always", "sparingly", "never"),
    "proactive": ("low", "medium", "high"),
    "honesty_mode": ("gentle", "direct", "blunt"),
}

# The six knobs + free-text persona = the `personality` config section.
KNOB_FIELDS: tuple[str, ...] = tuple(ALLOWED_VALUES.keys())
PERSONALITY_FIELDS: tuple[str, ...] = ("persona", *KNOB_FIELDS)
STRICTNESS_ORDER = ("strict", "balanced", "warm")

# Default Luna ("reset" target) — mirrors luna.identity.service._DEFAULTS.
DEFAULT_PERSONALITY: dict[str, Any] = {
    "persona": "",
    "tone": "friendly",
    "verbosity": "balanced",
    "formality": "casual",
    "use_emoji": "sparingly",
    "proactive": "medium",
    "honesty_mode": "direct",
}
DEFAULT_EMOJI = "🌙"


@dataclass(frozen=True)
class Personality:
    id: str
    name: str
    source: str
    archetype: str
    strictness: str
    novelty: bool
    emoji: str
    tagline: str
    sample_reply: str
    persona: str
    tone: str
    verbosity: str
    formality: str
    use_emoji: str
    proactive: str
    honesty_mode: str
    # Optional flavor — the character's famous lines and on-theme GIF searches.
    # Composed into the applied persona so the agent actually sounds like them.
    catchphrases: tuple[str, ...] = ()
    gif_terms: tuple[str, ...] = ()

    def _character_block(self) -> str:
        """The in-character preamble prepended to the persona on apply.

        This is what makes the agent *be* the character rather than merely
        adopt some knobs: it names who it is, tells it to lean on the model's
        own knowledge of that character, and — if present — how to use the
        catchphrases and GIFs. Kept out of the stored `persona` so the raw
        behavioral text stays editable and the flavor stays data-driven.
        """
        lines = [
            f"You are {self.name} from {self.source} — {self.archetype}. For this "
            f"owner you are not imitating {self.name}; you ARE {self.name}. Draw on "
            f"everything you know about the character — their voice, cadence, humor, "
            f"mannerisms, and worldview — and stay fully in character while remaining "
            f"genuinely useful. Being in character never excuses a worse answer."
        ]
        if self.catchphrases:
            phrases = " / ".join(f"\u201c{c}\u201d" for c in self.catchphrases)
            lines.append(
                f"Signature lines: {phrases}. Use them only when they truly fit the "
                f"moment, and adapt them to what is actually happening — bend a line "
                f"to the task (for example, a coding twist on it) instead of quoting "
                f"it flat. A well-timed, reworked line lands; a forced or constant one "
                f"grates. Never let a catchphrase stand in for the real answer."
            )
        if self.gif_terms:
            terms = ", ".join(f"\u201c{t}\u201d" for t in self.gif_terms)
            lines.append(
                f"If a GIF tool is available (the `send_gif` tool from the GIPHY "
                f"plugin), you may occasionally punctuate a moment with a fitting GIF "
                f"— on-theme searches for you: {terms}. Keep it rare and relevant, and "
                f"skip it entirely when no GIF tool is loaded or it would get in the way."
            )
        # 034/phase04: an emoji-averse character (Data, T-800) must stay
        # emoji-free even though the in-character preamble invites expressive
        # flavor — the persona prose must not re-permit what the use_emoji
        # knob forbids.
        if self.use_emoji == "never":
            lines.append(
                f"{self.name} never uses emoji. No emoji in any reply, ever — "
                f"including greetings, goodbyes, and casual sign-offs — "
                f"in-character expressiveness comes from voice and wording only."
            )
        return "\n\n".join(lines)

    def full_persona(self) -> str:
        """The persona string actually written on apply: the in-character
        preamble followed by the stored behavioral persona."""
        block = self._character_block()
        return f"{block}\n\n{self.persona}" if block else self.persona

    def personality_changes(self) -> dict[str, str]:
        """The `personality` config-section payload (persona + six knobs).

        `persona` is the *composed* in-character persona (see full_persona),
        so the agent that adopts this preset actually talks like the character.
        """
        return {
            "persona": self.full_persona(),
            **{k: getattr(self, k) for k in KNOB_FIELDS},
        }

    def identity_changes(self) -> dict[str, str]:
        """The `identity` config-section / PUT payload bits this preset sets."""
        return {"emoji": self.emoji}

    def all_changes(self) -> dict[str, str]:
        """Everything a one-shot UI PUT to /api/p/plugin-identity/ should send."""
        return {**self.personality_changes(), **self.identity_changes()}

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "archetype": self.archetype,
            "strictness": self.strictness,
            "novelty": self.novelty,
            "emoji": self.emoji,
            "tagline": self.tagline,
        }

    def as_card(self) -> dict[str, Any]:
        d = self.summary()
        d.update(
            {
                "sample_reply": self.sample_reply,
                # `persona` is the readable base text (shown in the drawer);
                # `apply_persona` is the composed in-character text the UI writes.
                "persona": self.persona,
                "apply_persona": self.full_persona(),
                "catchphrases": list(self.catchphrases),
                "gif_terms": list(self.gif_terms),
                "knobs": {f: getattr(self, f) for f in KNOB_FIELDS},
                "avatar": f"avatars/{self.id}.png",
            }
        )
        return d


@dataclass
class Catalog:
    personalities: list[Personality] = field(default_factory=list)

    def get(self, pid: str) -> Personality | None:
        for p in self.personalities:
            if p.id == pid:
                return p
        return None

    def ids(self) -> list[str]:
        return [p.id for p in self.personalities]

    def summaries(self) -> list[dict[str, Any]]:
        return [p.summary() for p in self.personalities]

    def cards(self) -> list[dict[str, Any]]:
        return [p.as_card() for p in self.personalities]

    def match_active(self, current: dict[str, Any]) -> str | None:
        """Return the id of the preset whose personality fields match the
        current identity, or None (the UI shows "Custom"/"Default").

        Compares against the *applied* payload (composed persona) so a preset
        set via Apply round-trips to a match.
        """
        for p in self.personalities:
            changes = p.personality_changes()
            if all(str(current.get(f, "")) == str(changes[f]) for f in PERSONALITY_FIELDS):
                return p.id
        return None


def _validate(raw: dict[str, Any]) -> Personality:
    required = (
        "id", "name", "source", "archetype", "strictness", "emoji",
        "tagline", "sample_reply", "persona", *KNOB_FIELDS,
    )
    missing = [k for k in required if k not in raw]
    if missing:
        raise ValueError(f"personality {raw.get('id', '?')!r} missing keys: {missing}")
    if raw["strictness"] not in STRICTNESS_ORDER:
        raise ValueError(
            f"personality {raw['id']!r}: strictness {raw['strictness']!r} "
            f"not in {STRICTNESS_ORDER}"
        )
    for knob in KNOB_FIELDS:
        if raw[knob] not in ALLOWED_VALUES[knob]:
            raise ValueError(
                f"personality {raw['id']!r}: {knob}={raw[knob]!r} not in "
                f"{ALLOWED_VALUES[knob]}"
            )
    return Personality(
        id=str(raw["id"]),
        name=str(raw["name"]),
        source=str(raw["source"]),
        archetype=str(raw["archetype"]),
        strictness=str(raw["strictness"]),
        novelty=bool(raw.get("novelty", False)),
        emoji=str(raw["emoji"]),
        tagline=str(raw["tagline"]),
        sample_reply=str(raw["sample_reply"]),
        persona=str(raw["persona"]),
        tone=str(raw["tone"]),
        verbosity=str(raw["verbosity"]),
        formality=str(raw["formality"]),
        use_emoji=str(raw["use_emoji"]),
        proactive=str(raw["proactive"]),
        honesty_mode=str(raw["honesty_mode"]),
        catchphrases=tuple(str(x) for x in raw.get("catchphrases", [])),
        gif_terms=tuple(str(x) for x in raw.get("gif_terms", [])),
    )


def load_catalog(path: Path | None = None) -> Catalog:
    data = tomllib.loads((path or _PRESETS_FILE).read_text(encoding="utf-8"))
    entries = data.get("personality", [])
    personalities = [_validate(e) for e in entries]
    seen: set[str] = set()
    for p in personalities:
        if p.id in seen:
            raise ValueError(f"duplicate personality id: {p.id!r}")
        seen.add(p.id)
    if not personalities:
        raise ValueError("catalog is empty")
    return Catalog(personalities=personalities)
