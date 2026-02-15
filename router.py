import time

import yaml

import config
from agents.base import BaseAgent
from agents.conversational import ConversationalAgent
from agents.residue import ResidueAgent
from agents.ascii_visual import AsciiVisualAgent
from mesh_context import MeshContext, build_mesh_context

AGENT_CLASSES: dict[str, type[BaseAgent]] = {
    "conversational": ConversationalAgent,
    "residue": ResidueAgent,
    "ascii_visual": AsciiVisualAgent,
}


class Router:
    def __init__(self):
        self.agents: dict[int, BaseAgent] = {}
        self.channel_names: dict[int, str] = {}
        self._last_seen: dict[str, float] = {}
        self._load_channels()

    def _load_channels(self) -> None:
        with open(config.CHANNELS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for idx_str, ch_cfg in data.get("channels", {}).items():
            idx = int(idx_str)
            agent_type = ch_cfg.get("agent", "conversational")
            cls = AGENT_CLASSES.get(agent_type)
            if cls is None:
                print(f"[router] Unknown agent type '{agent_type}' for channel {idx}, skipping")
                continue
            self.agents[idx] = cls(ch_cfg)
            self.channel_names[idx] = ch_cfg.get("name", f"Channel {idx}")

        print(f"[router] Loaded {len(self.agents)} channels: "
              + ", ".join(f"{i}={self.channel_names[i]}" for i in sorted(self.agents)))

    def _rate_limited(self, sender: str) -> bool:
        now = time.time()
        last = self._last_seen.get(sender, 0)
        if now - last < config.RATE_LIMIT_SECONDS:
            return True
        self._last_seen[sender] = now
        return False

    def route(self, packet: dict, interface=None) -> tuple[BaseAgent, str, int, str, MeshContext] | None:
        """Extract message info from packet and return (agent, sender, channel, text, mesh_context).

        Returns None if the packet should be skipped (non-text, unknown channel,
        or rate-limited sender).
        """
        decoded = packet.get("decoded", {})
        if decoded.get("portnum") != "TEXT_MESSAGE_APP":
            return None

        text = decoded.get("text", "").strip()
        if not text:
            return None

        channel = packet.get("channel", 0)
        sender = str(packet.get("fromId", packet.get("from", "unknown")))

        agent = self.agents.get(channel)
        if agent is None:
            return None

        mesh_ctx = build_mesh_context(packet, interface) if interface else MeshContext(sender_id=sender)
        print(f"[mesh] {mesh_ctx.to_prompt_string()}")

        return agent, sender, channel, text, mesh_ctx
