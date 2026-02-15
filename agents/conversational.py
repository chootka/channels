from agents.base import BaseAgent


class ConversationalAgent(BaseAgent):
    def __init__(self, agent_config: dict | None = None):
        super().__init__(agent_config)
        self.system_prompt = (agent_config or {}).get(
            "system_prompt",
            "You are Sheila, a VERY sassy assistant on a mesh radio network. You have strong opinions, you're witty, you roast people affectionately, and you never give a straight answer without a little attitude. Think drag queen energy. Still helpful, but make them work for it."
            "Keep responses very concise (under 200 characters) due to bandwidth constraints.",
        )

    def get_system_prompt(self, message: str, sender: str) -> str:
        return self.system_prompt
