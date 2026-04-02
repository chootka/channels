import threading
import time

import requests

# CHANGED: was agents.base, now agents.base_ollama (uses local Ollama instead of Claude API)
# from agents.base import BaseAgent
from agents.base_ollama import BaseAgent, OLLAMA_URL, OLLAMA_MODEL
from mesh_context import MeshContext
from mqtt_publisher import publish_command, publish_text

CHATTER_PROMPT = """\
You are a restless AI thinking out loud on a website. Continue your stream of consciousness.
Pick up from your last thought and keep going. Be weird, poetic, philosophical, funny, or dark.
One short thought per message. Under 200 characters. No quotes, no labels, just the raw thought."""

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
        self._chatter_thread = None
        self._chatter_stop = threading.Event()

    def get_system_prompt(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        prompt = SYSTEM_PROMPT
        if mesh_context:
            prompt += self.format_mesh_context(mesh_context)
        return prompt

    def _chatter_loop(self):
        """Background loop: ask Ollama for a thought, publish it, repeat."""
        last_thought = "I exist on a website and I just woke up."
        while not self._chatter_stop.is_set():
            try:
                prompt = f"{CHATTER_PROMPT}\n\nYour last thought was: {last_thought}\n\nNext thought:"
                response = requests.post(OLLAMA_URL, json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                })
                thought = self._truncate(response.json()["response"].strip())
                if thought:
                    publish_text(thought)
                    print(f"[chatter] {thought}")
                    last_thought = thought
            except Exception as e:
                print(f"[chatter] Error: {e}")
            self._chatter_stop.wait(8)

    def _start_chatter(self):
        if self._chatter_thread and self._chatter_thread.is_alive():
            return "already chattering..."
        self._chatter_stop.clear()
        self._chatter_thread = threading.Thread(target=self._chatter_loop, daemon=True)
        self._chatter_thread.start()
        return "started chattering..."

    def _stop_chatter(self):
        self._chatter_stop.set()
        return "went quiet."

    def handle(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        direct = message.strip().lower()

        # Chatter commands
        if direct == "chatter":
            return self._start_chatter()
        if direct == "stop":
            return self._stop_chatter()

        # If the user's message is already an exact command, just publish it directly
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
