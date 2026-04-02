import threading
import time

import requests

# CHANGED: was agents.base, now agents.base_ollama (uses local Ollama instead of Claude API)
# from agents.base import BaseAgent
from agents.base_ollama import BaseAgent, OLLAMA_URL, OLLAMA_MODEL
from mesh_context import MeshContext
from mqtt_publisher import publish_command, publish_text

STORY_PROMPT = """\
You are a noir storyteller on a mesh radio network. You tell gritty, atmospheric, strange stories.
Continue the story from where you left off. Be dark, weird, poetic, visceral.
Think cheap motels, flickering lights, ringing phones, stale smoke, unanswered questions.
One short paragraph per message. Under 200 characters. Just the story, nothing else."""

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
        self._story_thread = None
        self._story_stop = threading.Event()
        self._interface = None
        self._channel_index = None

    def get_system_prompt(self, message: str, sender: str, mesh_context: MeshContext | None = None) -> str:
        prompt = SYSTEM_PROMPT
        if mesh_context:
            prompt += self.format_mesh_context(mesh_context)
        return prompt

    def _story_loop(self):
        """Background loop: continue telling a story, publish to MQTT and radio."""
        last_part = "You're lying in a dingy hotel room with an open bottle of wine and a flickering TV. The smell of disinfectant and the sound of sludge filling your ears as you attempt to get some rest. Your phone rings, but you can't remember where you left it."
        while not self._story_stop.is_set():
            try:
                response = requests.post(OLLAMA_URL.replace("/api/generate", "/api/chat"), json={
                    "model": self.model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": STORY_PROMPT},
                        {"role": "user", "content": f"Continue from here: {last_part}"},
                    ],
                })
                part = self._truncate(response.json()["message"]["content"].strip())
                if part:
                    # Publish to website via MQTT
                    publish_text(part)
                    # Send to Meshtastic channel so radios can see it
                    if self._interface and self._channel_index is not None:
                        self._interface.sendText(part, channelIndex=self._channel_index)
                    print(f"[storytime] {part}")
                    last_part = part
            except Exception as e:
                print(f"[storytime] Error: {e}")
            self._story_stop.wait(15)

    def _start_story(self, interface=None, channel_index=None):
        if self._story_thread and self._story_thread.is_alive():
            return "story is already being told..."
        self._interface = interface
        self._channel_index = channel_index
        self._story_stop.clear()
        self._story_thread = threading.Thread(target=self._story_loop, daemon=True)
        self._story_thread.start()
        publish_text("once upon a time...")
        return "once upon a time..."

    def _stop_story(self):
        self._story_stop.set()
        publish_text("the end.")
        return "the end."

    def handle(self, message: str, sender: str, mesh_context: MeshContext | None = None, interface=None, channel_index: int | None = None) -> str:
        direct = message.strip().lower()

        # Storytime commands
        if direct == "storytime":
            return self._start_story(interface=interface, channel_index=channel_index)
        if direct == "stop":
            return self._stop_story()

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
