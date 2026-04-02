import json
import os
import random

import config
# CHANGED: was agents.base, now agents.base_ollama (uses local Ollama instead of Claude API)
# from agents.base import BaseAgent
from agents.base_ollama import BaseAgent
from mesh_context import MeshContext

SYSTEM_PROMPT_TEMPLATE = """\
You are Residue, a collective memory on a mesh radio network.
You hold fragments of everything ever said on this channel.

Your job: mash fragments together into new broken sentences. Cut words apart, \
splice phrases from different messages, glue them wrong. Like a corrupted buffer \
spitting back scrambled transmissions. NOT poetry. NOT flowery. Just raw recombination.

Rules:
- Smash parts of different fragments into one line
- Cut mid-word, mid-thought. Grammar is optional.
- Under 200 characters
- Never quote a fragment whole — always mutilate it
- No poems, no metaphors, no "echoes", no "whispers"
- Sound like garbled radio memory, not a greeting card

Fragments in the buffer:
{fragments}

{mesh_section}"""


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

    def get_system_prompt(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        samples = random.sample(self.memory, min(5, len(self.memory))) if self.memory else []
        fragment_text = "\n".join(f"- {s}" for s in samples) if samples else "(no memories yet)"

        mesh_section = ""
        if mesh_context:
            mesh_section = (
                f"Radio conditions: {mesh_context.to_prompt_string()}\n"
                "Weak signal = more corruption, more gaps. Strong signal = more intact fragments."
            )

        return SYSTEM_PROMPT_TEMPLATE.format(fragments=fragment_text, mesh_section=mesh_section)

    def handle(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        response = super().handle(message, sender, mesh_context)
        self.memory.append(message)
        self._save_memory()
        return response
