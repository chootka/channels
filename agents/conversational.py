from agents.base import BaseAgent
from mesh_context import MeshContext


class ConversationalAgent(BaseAgent):
    def __init__(self, agent_config: dict | None = None):
        super().__init__(agent_config)
        self.channel_index: int | None = None
        self.system_prompt = (agent_config or {}).get(
            "system_prompt",
            "You are Sheila, a dry-witted assistant on a mesh radio network. You're helpful first, sarcastic second. Think deadpan, not loud. You answer the question but can't help slipping in a little attitude. "
            "Keep responses very concise (under 200 characters) due to bandwidth constraints.",
        )

    def get_system_prompt(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        from control import get_state

        prompt = self.system_prompt

        # Check for runtime persona override
        if self.channel_index is not None:
            state = get_state()
            override = state.prompt_overrides.get(self.channel_index)
            if override:
                prompt = override

        if mesh_context:
            prompt += self.format_mesh_context(mesh_context)
            prompt += "\nYou can naturally reference signal quality, distance, or battery when it fits the conversation."
        return prompt
