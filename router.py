import time

import yaml

import config
import control
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
        self._admin_channels: set[int] = set()
        self._load_channels()

    def _load_channels(self) -> None:
        with open(config.CHANNELS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for idx_str, ch_cfg in data.get("channels", {}).items():
            idx = int(idx_str)
            agent_type = ch_cfg.get("agent", "conversational")
            if agent_type == "admin":
                self._admin_channels.add(idx)
                self.channel_names[idx] = ch_cfg.get("name", f"Channel {idx}")
                if "system_prompt" in ch_cfg:
                    agent = ConversationalAgent(ch_cfg)
                    if hasattr(agent, "channel_index"):
                        agent.channel_index = idx
                    self.agents[idx] = agent
                continue
            cls = AGENT_CLASSES.get(agent_type)
            if cls is None:
                print(f"[router] Unknown agent type '{agent_type}' for channel {idx}, skipping")
                continue
            agent = cls(ch_cfg)
            if hasattr(agent, "channel_index"):
                agent.channel_index = idx
            self.agents[idx] = agent
            self.channel_names[idx] = ch_cfg.get("name", f"Channel {idx}")

        all_channels = sorted(set(self.agents) | self._admin_channels)
        print(f"[router] Loaded {len(all_channels)} channels: "
              + ", ".join(f"{i}={self.channel_names[i]}" for i in all_channels))

    def _rate_limited(self, sender: str) -> bool:
        now = time.time()
        last = self._last_seen.get(sender, 0)
        if now - last < config.RATE_LIMIT_SECONDS:
            return True
        self._last_seen[sender] = now
        return False

    def route(self, packet: dict, interface=None) -> tuple[BaseAgent, str, int, str, MeshContext] | tuple[str, str, int] | None:
        """Route a packet.

        Returns one of:
        - (agent, sender, channel, text, mesh_context) for normal agent dispatch
        - (response, sender, channel) for control command responses
        - None if the packet should be skipped
        """
        decoded = packet.get("decoded", {})
        if decoded.get("portnum") != "TEXT_MESSAGE_APP":
            return None

        text = decoded.get("text", "").strip()
        if not text:
            return None

        channel = packet.get("channel", 0)
        sender = str(packet.get("fromId", packet.get("from", "unknown")))

        # Control commands: intercept before agent dispatch
        if control.is_control_command(text):
            if channel in self._admin_channels or channel in self.agents:
                response = control.handle_command(text, sender, channel, self)
                return response, sender, channel
            return None

        agent = self.agents.get(channel)
        if agent is None:
            return None

        # Enforce warn cooldowns on normal messages
        state = control.get_state()
        if state.is_on_cooldown(sender):
            print(f"[router] {sender} is on cooldown, dropping message")
            return None

        mesh_ctx = build_mesh_context(packet, interface) if interface else MeshContext(sender_id=sender)
        print(f"[mesh] {mesh_ctx.to_prompt_string()}")

        return agent, sender, channel, text, mesh_ctx
