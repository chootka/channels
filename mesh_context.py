from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MeshContext:
    sender_name: str = "unknown"
    sender_id: str = "unknown"
    snr: float | None = None
    rssi: int | None = None
    hops: int | None = None
    battery: int | None = None
    channel_util: float | None = None
    position: tuple[float, float, int] | None = None  # (lat, lon, alt)
    nodes_active: int = 0
    nodes_total: int = 0

    def to_prompt_string(self) -> str:
        parts = [f"node:{self.sender_name}"]
        if self.snr is not None:
            parts.append(f"snr:{self.snr:.1f}dB")
        if self.rssi is not None:
            parts.append(f"rssi:{self.rssi}dBm")
        if self.hops is not None:
            parts.append(f"hops:{self.hops}")
        if self.battery is not None:
            parts.append(f"bat:{self.battery}%")
        if self.channel_util is not None:
            parts.append(f"ch_util:{self.channel_util:.1f}%")
        if self.position:
            lat, lon, alt = self.position
            parts.append(f"pos:{lat:.4f},{lon:.4f},alt{alt}m")
        if self.nodes_total:
            parts.append(f"mesh:{self.nodes_active}/{self.nodes_total}nodes")
        return " | ".join(parts)

    @property
    def signal_quality(self) -> str:
        """Categorize signal as strong/moderate/weak/unknown."""
        if self.snr is None:
            return "unknown"
        if self.snr > 5:
            return "strong"
        if self.snr > -5:
            return "moderate"
        return "weak"


def build_mesh_context(packet: dict, interface) -> MeshContext:
    ctx = MeshContext()

    sender_num = packet.get("from")
    ctx.sender_id = str(packet.get("fromId", sender_num or "unknown"))

    # Signal info from packet
    ctx.snr = packet.get("rxSnr")
    ctx.rssi = packet.get("rxRssi")

    # Calculate hops
    hop_start = packet.get("hopStart")
    hop_limit = packet.get("hopLimit")
    if hop_start is not None and hop_limit is not None:
        ctx.hops = hop_start - hop_limit

    # Node database info
    nodes = getattr(interface, "nodes", None) or {}
    ctx.nodes_total = len(nodes)
    ctx.nodes_active = sum(
        1 for n in nodes.values()
        if n.get("lastHeard") and n.get("isFavorite", True)
    )

    # Sender node info
    node = nodes.get(ctx.sender_id) or {}
    ctx.sender_name = node.get("user", {}).get("longName", ctx.sender_id)

    metrics = node.get("deviceMetrics", {})
    if metrics.get("batteryLevel") is not None:
        ctx.battery = int(metrics["batteryLevel"])
    if metrics.get("channelUtilization") is not None:
        ctx.channel_util = float(metrics["channelUtilization"])

    pos = node.get("position", {})
    lat = pos.get("latitude")
    lon = pos.get("longitude")
    if lat is not None and lon is not None:
        alt = pos.get("altitude", 0)
        ctx.position = (lat, lon, alt)

    return ctx
