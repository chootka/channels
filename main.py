import signal
import sys
import traceback

import meshtastic
import meshtastic.serial_interface
from pubsub import pub

import config
import logger
from router import Router


router = Router()
interface = None


def on_receive(packet: dict, interface=None) -> None:
    try:
        result = router.route(packet)
        if result is None:
            return

        agent, sender, channel, text = result
        channel_name = router.channel_names.get(channel, f"Channel {channel}")
        print(f"[{channel_name}] {sender}: {text}")

        response = agent.handle(text, sender)
        print(f"[{channel_name}] -> {response}")

        iface = get_interface()
        if iface:
            iface.sendText(response, channelIndex=channel)

        logger.log_interaction(sender, channel, channel_name, text, response)

    except Exception:
        traceback.print_exc()


def get_interface():
    global interface
    return interface


def shutdown(signum, frame):
    print("\n[main] Shutting down...")
    iface = get_interface()
    if iface:
        iface.close()
    sys.exit(0)


def main():
    global interface
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    pub.subscribe(on_receive, "meshtastic.receive")

    print("[main] Connecting to Meshtastic device...")
    if config.SERIAL_PORT:
        interface = meshtastic.serial_interface.SerialInterface(config.SERIAL_PORT)
    else:
        interface = meshtastic.serial_interface.SerialInterface()

    print("[main] Listening for messages. Ctrl+C to quit.")

    # Keep the main thread alive
    while True:
        signal.pause()


if __name__ == "__main__":
    main()
