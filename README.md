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

## Meshtastic Channel Config

The app routes by **channel index** (the number), not by name. The channel index on the device must match what's in `channels.yaml`.

| Index | Name | PSK | Notes |
|-------|------|-----|-------|
| 0 | (your primary) | default (AQ==) | Your existing primary channel |
| 1 | (your secondary) | default (AQ==) | Optional — e.g. MQTT channel |
| 2 | (empty/skip) | — | — |
| 3 | sysop | default (AQ==) | Admin agent |
| 4 | sheila | default (AQ==) | Conversational agent |
| 5 | rezzy | default (AQ==) | Memory/residue agent |
| 6 | lowviz | default (AQ==) | ASCII art agent |
| 7 | mmmmmmorse | default (AQ==) | Morse code agent |

- **PSK**: Use the default key (`AQ==`) or no key — just make sure all devices on the mesh use the same key per channel
- **Uplink/Downlink**: Not needed — the app talks directly over USB serial, not MQTT
- **No other special settings** — just the channel name and index

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
┌───────────────────────────────────────────────────────────┐
│  Someone sends a message on a Meshtastic channel          │
└────────────────────────┬──────────────────────────────────┘
                    LoRa radio
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│  Meshtastic device (USB serial)                           │
└────────────────────────┬──────────────────────────────────┘
                    USB serial
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│  main.py                                                  │
│  Receives packet, passes to router, sends response back   │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│  router.py                                                │
│                                                           │
│  1. Is it a text message? (ignore GPS, telemetry)         │
│  2. Is it a control command? → control.py                 │
│  3. Is the sender rate-limited? → drop                    │
│  4. Look up agent by channel index                        │
│  5. Build mesh context (signal, battery, hops, position)  │
│  6. Dispatch to agent                                     │
└──────────┬──────────────────────────┬─────────────────────┘
           │                          │
           ▼                          ▼
┌────────────────────┐  ┌──────────────────────────────────┐
│  mesh_context.py   │  │  channels.yaml                   │
│                    │  │                                  │
│  Extracts from     │  │  Maps channel index → agent:     │
│  packet:           │  │  3: sysop (admin)                │
│  • signal (SNR)    │  │  4: sheila (conversational)      │
│  • battery         │  │  5: rezzy (memory/residue)       │
│  • hops            │  │  6: lowviz (ASCII art)           │
│  • GPS position    │  │  7: mmmmmmorse (Morse code)      │
│  • node count      │  │                                  │
└────────────────────┘  └──────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│  agents/base.py — THE API CALL                            │
│                                                           │
│  system_prompt = "You are Sheila, a dry-witted..."        │
│                + "[Mesh context: snr:10.5dB | hops:1]"   │
│                                                           │
│  response = client.messages.create(                       │
│      model="claude-sonnet-4-5-20250929",                  │
│      system=system_prompt,                                │
│      messages=[{"role": "user", "content": text}],        │
│  )                                                        │
│                                                           │
│  Truncate to 220 bytes (LoRa limit)                       │
└────────────────────────┬──────────────────────────────────┘
                         │
                    response text
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│  main.py → interface.sendText(response, channelIndex)     │
│  → USB serial → Meshtastic device → LoRa → sender        │
└───────────────────────────────────────────────────────────┘
```

- 220 byte max messages (LoRa constraint)
- Interactions logged to `logs/interactions.jsonl`
- Residue memory persists across restarts
- Control state persists across restarts

For a detailed walkthrough of every file, see [architecture.md](architecture.md).
