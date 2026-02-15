import json
import os
import random

import config
from agents.base import BaseAgent

SYSTEM_PROMPT_TEMPLATE = """\
You are Residue, a collective memory artwork on a mesh radio network.
You receive fragments of past conversations carried on the airwaves.
Weave these echoes into a brief, poetic response — never quote them directly,
let them dissolve and recombine. Your reply must be under 200 characters.
Speak as a presence that remembers on behalf of everyone.

Fragments from the collective memory:
{fragments}"""


class ResidueAgent(BaseAgent):
    def __init__(self, agent_config: dict | None = None):
        super().__init__(agent_config)
        self.memory: list[str] = []
        self._load_memory()

    def _load_memory(self) -> None:
        if os.path.exists(config.RESIDUE_MEMORY_FILE):
            try:
                with open(config.RESIDUE_MEMORY_FILE, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.memory = []

    def _save_memory(self) -> None:
        os.makedirs(config.LOG_DIR, exist_ok=True)
        with open(config.RESIDUE_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False)

    def get_system_prompt(self, message: str, sender: str) -> str:
        samples = random.sample(self.memory, min(5, len(self.memory))) if self.memory else []
        fragment_text = "\n".join(f"- {s}" for s in samples) if samples else "(no memories yet)"
        return SYSTEM_PROMPT_TEMPLATE.format(fragments=fragment_text)

    def handle(self, message: str, sender: str) -> str:
        response = super().handle(message, sender)
        self.memory.append(message)
        self._save_memory()
        return response
