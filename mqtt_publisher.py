"""Publishes commands to the MQTT broker so the web app can react."""

import json
import os
import random
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

MQTT_BROKER = os.environ.get("MQTT_BROKER", "dweb2025.nohost.me")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "msh/afterhours/2/json/broadcasts/!webmistress")


def publish_command(command: str) -> bool:
    """Publish a command to the MQTT broker for the web app to pick up."""
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if MQTT_USERNAME:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)

        payload = json.dumps({
            "id": random.randint(100000, 999999),
            "from": 0,
            "type": "text",
            "payload": {"text": command},
            "sender": "!webmistress",
        })

        client.publish(MQTT_TOPIC, payload)
        client.disconnect()
        print(f"[mqtt] Published command: {command}")
        return True
    except Exception as e:
        print(f"[mqtt] Failed to publish: {e}")
        return False
