from agents.base import BaseAgent


class ConversationalAgent(BaseAgent):
    def __init__(self, agent_config: dict | None = None):
        super().__init__(agent_config)
        self.system_prompt = (agent_config or {}).get(
            "system_prompt",
            "You are a helpful assistant on a Meshtastic mesh network. "
            "Keep responses very concise (under 200 characters) due to bandwidth constraints.",
        )

    def get_system_prompt(self, message: str, sender: str) -> str:
        return self.system_prompt
