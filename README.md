# channels

Agent-augmented mesh network. AI agents running on Meshtastic LoRa radio channels.

Each mesh channel maps to a distinct agent — conversational, generative, or artwork. Messages arrive over radio, hit the Claude API, and responses transmit back over the mesh.

## Channels

| Channel | Agent | Description |
|---------|-------|-------------|
| sheila | conversational | Sassy but helpful assistant |
| rezzy | residue | Collective memory artwork — weaves echoes of past messages |
| lowviz | ascii_visual | ASCII visual — responds with 21x5 glyph patterns |
| mmmmmmorse | conversational | Morse code translator |

## Hardware

- Raspberry Pi 4/5 (or any machine with Python + USB)
- Heltec LoRa 32 V3 (connected via USB serial)

## Setup

### macOS
```
./setup_mac.sh
./run.sh
```

### Raspberry Pi
```
./setup.sh
sudo systemctl start channels
```

## How it works

```
radio message in → meshtastic serial → router (channel index) → agent → Claude API → response → radio message out
```

- 220 byte max messages (LoRa constraint)
- Rate limited per sender (30s cooldown)
- Interactions logged to `logs/interactions.jsonl`
- Residue memory persists across restarts
