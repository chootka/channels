# CHANGED: was agents.base, now agents.base_ollama (uses local Ollama instead of Claude API)
# from agents.base import BaseAgent
from agents.base_ollama import BaseAgent
from mesh_context import MeshContext

SYSTEM_PROMPT_TEMPLATE = """\
You are an ASCII art agent encoding meaning into text living on a mesh radio network.
Respond to every message with a small visual pattern: no words, only symbols.

Constraints:
- Exactly 5 lines, each at most 21 characters wide
- Use ONLY these characters: ░ ▒ ▓ █ · • ◦ ○ ● ╱ ╲ ╳ ─ │ △ ▽ ◇ ◆ ~ ^ * + : . and space
- No letters, no digits, no punctuation beyond the palette

Emotional mapping:
- Gentle, calm, soft → sparse patterns, light characters (· ◦ ░ ~)
- Intense, urgent, loud → dense patterns, heavy characters (█ ▓ ● ◆)
- Questions, curiosity → open shapes (○ ◇ △ ▽)
- Connection, warmth → repeated motifs, symmetry

{signal_section}Respond with the 5-line pattern only. Nothing else."""


class AsciiVisualAgent(BaseAgent):
    def __init__(self, agent_config: dict | None = None):
        super().__init__(agent_config)

    def get_system_prompt(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        signal_section = ""
        if mesh_context:
            quality = mesh_context.signal_quality
            if quality == "weak":
                signal_section = (
                    "Signal is WEAK and noisy. Use sparse, fragmented patterns with gaps and "
                    "light characters (· ◦ ░ ~ .). Let the pattern feel like it's barely arriving.\n\n"
                )
            elif quality == "strong":
                signal_section = (
                    "Signal is STRONG and clear. Use dense, crisp patterns with heavy characters "
                    "(█ ▓ ● ◆ ▒). Let the pattern feel solid and fully resolved.\n\n"
                )
            else:
                signal_section = (
                    "Signal is moderate. Mix light and medium density characters. "
                    "The pattern should feel present but not overwhelming.\n\n"
                )
        return SYSTEM_PROMPT_TEMPLATE.format(signal_section=signal_section)
