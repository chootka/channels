from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

import config

WARN_COOLDOWNS = {1: 5, 2: 30}  # warn count → cooldown seconds


@dataclass
class ControlState:
    mode: str = "admin_channel"  # "admin_channel" | "allowlist" | "anarchy"
    admin_channel: int = 3
    allowlist: set[str] = field(default_factory=set)
    banlist: set[str] = field(default_factory=set)
    prompt_overrides: dict[int, str] = field(default_factory=dict)
    warns: dict[str, int] = field(default_factory=dict)  # node_id → warn count
    cooldowns: dict[str, float] = field(default_factory=dict, repr=False)  # node_id → expiry timestamp (runtime only)

    def save(self) -> None:
        os.makedirs(os.path.dirname(config.CONTROL_STATE_FILE), exist_ok=True)
        data = {
            "mode": self.mode,
            "admin_channel": self.admin_channel,
            "allowlist": sorted(self.allowlist),
            "banlist": sorted(self.banlist),
            "prompt_overrides": {str(k): v for k, v in self.prompt_overrides.items()},
            "warns": self.warns,
        }
        with open(config.CONTROL_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls) -> ControlState:
        if not os.path.exists(config.CONTROL_STATE_FILE):
            return cls()
        try:
            with open(config.CONTROL_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(
                mode=data.get("mode", "admin_channel"),
                admin_channel=data.get("admin_channel", 3),
                allowlist=set(data.get("allowlist", [])),
                banlist=set(data.get("banlist", [])),
                prompt_overrides={int(k): v for k, v in data.get("prompt_overrides", {}).items()},
                warns=data.get("warns", {}),
            )
        except (json.JSONDecodeError, KeyError):
            return cls()

    def is_on_cooldown(self, node_id: str) -> bool:
        expiry = self.cooldowns.get(node_id)
        if expiry is None:
            return False
        if time.time() < expiry:
            return True
        del self.cooldowns[node_id]
        return False


_state: ControlState | None = None


def get_state() -> ControlState:
    global _state
    if _state is None:
        _state = ControlState.load()
    return _state


def is_control_command(text: str) -> bool:
    return text.startswith("!")


def is_authorized(sender: str, channel: int, state: ControlState) -> bool:
    if sender in state.banlist:
        return False
    if channel == state.admin_channel:
        return True
    if state.mode == "anarchy":
        return True
    if state.mode == "allowlist":
        return sender in state.allowlist
    # admin_channel mode: only the admin channel is allowed (handled above)
    return False


def _is_admin_channel(channel: int, state: ControlState) -> bool:
    return channel == state.admin_channel


VALID_MODES = {"admin_channel", "allowlist", "anarchy"}


def handle_command(text: str, sender: str, channel: int, router) -> str:
    state = get_state()

    if not is_authorized(sender, channel, state):
        return "denied"

    parts = text.split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "!status":
        return (
            f"mode={state.mode} "
            f"allow={len(state.allowlist)} "
            f"ban={len(state.banlist)} "
            f"warns={len(state.warns)} "
            f"overrides={len(state.prompt_overrides)}"
        )

    if cmd == "!persona":
        if not arg:
            return "usage: !persona <prompt>"
        state.prompt_overrides[channel] = arg
        state.save()
        return f"persona set on ch{channel}"

    if cmd == "!reset":
        if channel in state.prompt_overrides:
            del state.prompt_overrides[channel]
            state.save()
            return f"ch{channel} reset to default"
        return f"ch{channel} already default"

    # Admin-only commands below
    if not _is_admin_channel(channel, state):
        return "admin-only command"

    if cmd == "!mode":
        if arg not in VALID_MODES:
            return f"usage: !mode <{'|'.join(sorted(VALID_MODES))}>"
        state.mode = arg
        state.save()
        return f"mode={arg}"

    if cmd == "!allow":
        if not arg:
            return "usage: !allow <node_id>"
        state.allowlist.add(arg)
        state.save()
        return f"allowed {arg}"

    if cmd == "!ban":
        if not arg:
            return "usage: !ban <node_id>"
        state.banlist.add(arg)
        state.save()
        return f"banned {arg}"

    if cmd == "!unban":
        if not arg:
            return "usage: !unban <node_id>"
        state.banlist.discard(arg)
        state.save()
        return f"unbanned {arg}"

    if cmd == "!warn":
        if not arg:
            return "usage: !warn <node_id>"
        count = state.warns.get(arg, 0) + 1
        state.warns[arg] = count
        if count >= 3:
            state.banlist.add(arg)
            del state.warns[arg]
            state.save()
            return f"warn 3/3 — {arg} has been banned"
        cooldown = WARN_COOLDOWNS[count]
        state.cooldowns[arg] = time.time() + cooldown
        state.save()
        return f"warn {count}/3 — {arg} on {cooldown}s cooldown"

    return "unknown command"
