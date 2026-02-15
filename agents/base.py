import anthropic

import config


class BaseAgent:
    def __init__(self, agent_config: dict | None = None):
        agent_config = agent_config or {}
        self.model = agent_config.get("model", config.DEFAULT_MODEL)
        self.max_tokens = agent_config.get("max_tokens", config.DEFAULT_MAX_TOKENS)
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def get_system_prompt(self, message: str, sender: str) -> str:
        return "You are a helpful assistant. Be very concise."

    def get_user_content(self, message: str, sender: str) -> str:
        return message

    def handle(self, message: str, sender: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.get_system_prompt(message, sender),
            messages=[{"role": "user", "content": self.get_user_content(message, sender)}],
        )
        text = response.content[0].text
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
