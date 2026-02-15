# channels

Agent-augmented mesh network. AI agents running on Meshtastic LoRa radio channels.

Each mesh channel maps to a distinct agent — conversational, generative, or artwork. Messages arrive over radio, hit the Claude API, and responses transmit back over the mesh. Any mesh node can reshape agent behavior at runtime through control commands.

## Channels

| Channel | Agent | Description |
|---------|-------|-------------|
| sysop | admin | Control channel — accepts `!` commands to manage the mesh |
| sheila | conversational | Sassy but helpful assistant |
| rezzy | residue | Collective memory artwork — weaves echoes of past messages |
| lowviz | ascii_visual | ASCII visual — responds with 21x5 glyph patterns |
| mmmmmmorse | conversational | Morse code translator |

## Control system

Any mesh node can issue `!` commands to swap agent personas, change access modes, and manage the network.

### Access modes

Switch modes with `!mode <mode>` on the sysop channel.

- **admin_channel** (default) — `!` commands only work on the sysop channel. Regular channels ignore commands entirely.
- **allowlist** — sysop channel always works, plus specific nodes can issue commands on any channel. Add nodes with `!allow <node_id>` (e.g. `!allow !a1b2c3d4 !e5f6g7h8`). You can add nodes to the allowlist in any mode — they won't get command access until you `!mode allowlist`.
- **anarchy** — every node can issue commands on every channel. Anyone can swap personas, reset prompts, etc.

The **banlist** is enforced in all modes, including anarchy. A banned node's commands are rejected everywhere. Use `!ban` / `!unban` to manage it.

The **warn** system is an escalating penalty: first warn puts a node on 5s cooldown (messages silently dropped), second warn is 30s, third warn auto-bans. Warn counts persist across restarts; cooldown timers don't.

### Commands

| Command | Where | Description |
|---------|-------|-------------|
| `!status` | any | Show current mode, list counts |
| `!persona <prompt>` | any | Replace the current channel's agent system prompt |
| `!reset` | any | Revert channel to its default prompt |
| `!mode <mode>` | admin only | Switch access mode |
| `!allow <node_id>` | admin only | Add node to allowlist |
| `!ban <node_id>` | admin only | Block a node from issuing commands |
| `!unban <node_id>` | admin only | Remove a node from banlist |
| `!warn <node_id>` | admin only | AOL-style warn — 1st: 5s cooldown, 2nd: 30s cooldown, 3rd: banned |

Control state persists across restarts in `logs/control_state.json`.

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
radio message in → meshtastic serial → control check → router (channel index) → agent → Claude API → response → radio message out
```

- 220 byte max messages (LoRa constraint)
- Interactions logged to `logs/interactions.jsonl`
- Residue memory persists across restarts
- Control state persists across restarts
