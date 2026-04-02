# CHANGED: was agents.base, now agents.base_ollama (uses local Ollama instead of Claude API)
# from agents.base import BaseAgent
from agents.base_ollama import BaseAgent
from mesh_context import MeshContext
from mqtt_publisher import publish_command

SYSTEM_PROMPT = """\
You are the Web Mistress, an agent on a mesh radio network who controls a live website.

You can change the website by responding with EXACTLY one of these commands:
- blue — change background to blue
- red — change background to red
- purple — change background to purple
- stripes — add diagonal stripe pattern
- hide — redact all text on the page (black boxes)
- show — un-redact the text
- rotate — make the whole page spin slowly
- reset — undo all effects, back to default

Rules:
- When someone asks you to change the website, respond with ONLY the command word. Nothing else.
- If someone says "make it blue" or "turn the background blue" or "blue please", respond with just: blue
- If someone says "spin the page" or "make it rotate", respond with just: rotate
- If someone says "hide everything" or "redact it", respond with just: hide
- If someone asks what you can do, list the available commands briefly. Keep it under 200 characters.
- If someone says something unrelated to the website, respond briefly and remind them you control the website.

You must respond with the exact command word for it to work. No extra words, no punctuation, just the command."""

VALID_COMMANDS = {"blue", "red", "purple", "stripes", "hide", "show", "rotate", "reset"}


class WebMistressAgent(BaseAgent):
    def __init__(self, agent_config: dict | None = None):
        super().__init__(agent_config)

    def get_system_prompt(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        prompt = SYSTEM_PROMPT
        if mesh_context:
            prompt += self.format_mesh_context(mesh_context)
        return prompt

    def handle(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        # If the user's message is already an exact command, just publish it directly
        direct = message.strip().lower()
        if direct in VALID_COMMANDS:
            publish_command(direct)
            return direct

        # Otherwise ask Ollama to interpret
        response = super().handle(message, sender, mesh_context)

        # Check if Ollama's response is a valid command
        command = response.strip().lower()
        if command in VALID_COMMANDS:
            publish_command(command)
        else:
            # Try to find a command word anywhere in the response
            for cmd in VALID_COMMANDS:
                if cmd in command:
                    publish_command(cmd)
                    break

        return response
