import requests

import config
from mesh_context import MeshContext

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "tinyllama"  # Change to "llama3.2:3b" if you have 8GB RAM


class BaseAgent:
    def __init__(self, agent_config: dict | None = None):
        agent_config = agent_config or {}
        self.model = agent_config.get("model", OLLAMA_MODEL)
        self.max_tokens = agent_config.get("max_tokens", config.DEFAULT_MAX_TOKENS)

    def format_mesh_context(self, ctx: MeshContext) -> str:
        return f"\n\n[Mesh radio context: {ctx.to_prompt_string()}]"

    def get_system_prompt(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        prompt = "You are a helpful assistant. Be very concise."
        if mesh_context:
            prompt += self.format_mesh_context(mesh_context)
        return prompt

    def get_user_content(self, message: str, sender: str) -> str:
        return message

    def handle(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        system_prompt = self.get_system_prompt(message, sender, mesh_context)
        user_content = self.get_user_content(message, sender)

        response = requests.post(OLLAMA_URL.replace("/api/generate", "/api/chat"), json={
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        })

        text = response.json()["message"]["content"]
        return self._truncate(text)

    @staticmethod
    def _truncate(text: str, max_bytes: int = config.MAX_MESSAGE_BYTES) -> str:
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text
        truncated = encoded[:max_bytes]
        # Decode safely, ignoring partial multibyte chars at the end
        text = truncated.decode("utf-8", errors="ignore")
        # Break at last space to avoid cutting a word
        parts = text.rsplit(" ", 1)
        if len(parts) > 1:
            text = parts[0]
        return text + "…"
