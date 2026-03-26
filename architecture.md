# Channels Architecture

## Message Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MESHTASTIC RADIO                             │
│                                                                     │
│  Someone sends a message on a channel (e.g. channel 4: "sheila")   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                          LoRa radio
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MESHTASTIC DEVICE (USB)                          │
│                                                                     │
│  Heltec ESP32 / T-Beam connected to your computer via USB serial   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                          USB serial
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  main.py                                                            │
│                                                                     │
│  • Connects to Meshtastic device via serial                        │
│  • Subscribes to incoming messages (pub/sub)                       │
│  • Passes packets to the router                                    │
│  • Sends responses back over radio                                 │
│                                                                     │
│  pub.subscribe(on_receive, "meshtastic.receive")                   │
│                     │                                               │
│                     │  packet arrives                               │
│                     ▼                                               │
│          router.route(packet, interface)                            │
│                     │                                               │
│                     │  returns (agent, sender, channel, text, ctx)  │
│                     ▼                                               │
│          agent.handle(text, sender, mesh_context=ctx)               │
│                     │                                               │
│                     │  returns response text                        │
│                     ▼                                               │
│          interface.sendText(response, channelIndex=channel)         │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               │ packet
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  router.py                                                          │
│                                                                     │
│  1. Is it a text message?                                          │
│     └─ No → ignore (GPS, telemetry, etc.)                          │
│                                                                     │
│  2. Is it a control command? (e.g. !ban, !warn)                    │
│     └─ Yes → control.py handles it, return response                │
│                                                                     │
│  3. Is the sender rate-limited?                                    │
│     └─ Yes → drop the message                                      │
│                                                                     │
│  4. What channel did it come from?                                 │
│     └─ Look up the agent for that channel                          │
│                                                                     │
│  5. Build mesh context from packet metadata                        │
│     └─ mesh_context.py extracts signal, battery, hops, etc.       │
│                                                                     │
│  6. Return (agent, sender, channel, text, mesh_context)            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
┌──────────────────────┐          ┌──────────────────────────────────┐
│  mesh_context.py     │          │  channels.yaml                   │
│                      │          │                                  │
│  Extracts from the   │          │  Defines which agent runs on     │
│  Meshtastic packet:  │          │  which channel:                  │
│                      │          │                                  │
│  • sender name/ID    │          │  3: sysop (admin, BBS operator)  │
│  • SNR (signal)      │          │  4: sheila (dry-witted helper)   │
│  • RSSI (signal)     │          │  5: rezzy (memory/residue)       │
│  • hop count         │          │  6: lowviz (ASCII art only)      │
│  • battery level     │          │  7: mmmmmmorse (Morse code)      │
│  • GPS position      │          │                                  │
│  • channel util      │          │  Each channel specifies:         │
│  • node count        │          │  • agent type                    │
│                      │          │  • name                          │
│  Injected into the   │          │  • system prompt                 │
│  system prompt so    │          │                                  │
│  Claude can reference│          │                                  │
│  network conditions. │          │                                  │
└──────────────────────┘          └──────────────────────────────────┘
                               │
                               │ agent.handle(text, sender, mesh_context)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  agents/                                                            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  base.py — THE API CALL                                     │   │
│  │                                                             │   │
│  │  1. Build system prompt                                     │   │
│  │     "You are Sheila, a dry-witted assistant..."             │   │
│  │     + "[Mesh context: snr:10.5dB | hops:1 | bat:87%]"     │   │
│  │                                                             │   │
│  │  2. Call Claude API                                         │   │
│  │     client.messages.create(                                 │   │
│  │         model = "claude-sonnet-4-5-20250929",               │   │
│  │         system = system_prompt,                             │   │
│  │         messages = [{"role": "user", "content": text}],     │   │
│  │     )                                                       │   │
│  │                                                             │   │
│  │  3. Truncate response to 220 bytes (LoRa limit)            │   │
│  │                                                             │   │
│  │  4. Return response text                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          ▲                                          │
│          ┌───────────────┼───────────────┐                         │
│          │               │               │                         │
│  ┌───────┴──────┐ ┌─────┴──────┐ ┌──────┴───────┐                │
│  │conversational│ │  residue   │ │ ascii_visual  │                │
│  │              │ │            │ │              │                 │
│  │ Custom       │ │ Weaves     │ │ Responds in  │                │
│  │ system       │ │ memory     │ │ 5-line ASCII │                │
│  │ prompt from  │ │ from past  │ │ art only.    │                │
│  │ channels.yaml│ │ interactions│ │ No words.    │                │
│  │              │ │ with       │ │              │                 │
│  │ Can be       │ │ simulated  │ │              │                 │
│  │ overridden   │ │ corruption.│ │              │                │
│  │ at runtime.  │ │            │ │              │                 │
│  └──────────────┘ └────────────┘ └──────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               │ response text
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CLAUDE API                                   │
│                                                                     │
│  Anthropic's servers process the request and return a response.    │
│  This is the only part that requires internet.                     │
│                                                                     │
│  model: claude-sonnet-4-5-20250929                                 │
│  max_tokens: 128                                                    │
│  API key: from environment variable ANTHROPIC_API_KEY              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                          response text
                          (truncated to 220 bytes)
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACK TO main.py                                 │
│                                                                     │
│  interface.sendText(response, channelIndex=channel)                │
│                                                                     │
│  → Response sent over USB serial to Meshtastic device              │
│  → Device broadcasts over LoRa                                     │
│  → Original sender sees the reply on their radio                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Supporting Files

```
┌──────────────────────────────────────────────────────────────┐
│  config.py — All settings in one place                       │
│                                                              │
│  • ANTHROPIC_API_KEY (from environment variable)             │
│  • SERIAL_PORT (auto-detect or set manually)                 │
│  • DEFAULT_MODEL ("claude-sonnet-4-5-20250929")              │
│  • MAX_MESSAGE_BYTES (220 — LoRa limit)                      │
│  • RATE_LIMIT_SECONDS (10 — per-sender cooldown)             │
│  • Log file paths                                            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  control.py — Admin commands                                 │
│                                                              │
│  Commands: !ban, !unban, !warn, !status, !persona, !mode     │
│  Access modes: admin_channel, allowlist, anarchy             │
│  Manages bans, warnings, cooldowns                           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  logger.py — Interaction logging                             │
│                                                              │
│  Saves every interaction to logs/interactions.jsonl          │
│  Fields: timestamp, sender, channel, input, output           │
└──────────────────────────────────────────────────────────────┘
```
