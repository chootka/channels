import json
import os
from datetime import datetime, timezone

import config


def log_interaction(sender: str, channel: int, channel_name: str,
                    message_in: str, message_out: str) -> None:
    os.makedirs(config.LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sender": sender,
        "channel": channel,
        "channel_name": channel_name,
        "message_in": message_in,
        "message_out": message_out,
    }
    with open(config.LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
