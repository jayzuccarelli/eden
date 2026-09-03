"""A throwaway Home Assistant stand-in for running Eden with no HA and no hardware.

Speaks the three REST endpoints eden/ha.py actually uses:

    GET  /api/states/<entity_id>
    GET  /api/history/period/<iso>?filter_entity_id=<entity_id>
    POST /api/services/<domain>/<service>

Sensor values drift a little each read so `history` and repeated ticks look
alive. Actuator calls are printed and remembered, so you can see the dose the
loop actually fired. Nothing here is part of eden/ — it is a dev harness.

    uv run python tools/mock_ha.py            # port 8123, token-free
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 8123

# The starting world: pH sits ABOVE the basil profile's band (5.8..6.2) so the
# very first tick has something real to correct.
STATE: dict[str, str] = {
    "sensor.eden_z1_ph": "6.47",
    "sensor.eden_z1_water_temp": "21.4",
    "binary_sensor.eden_z1_air_pump_ok": "on",
    "switch.eden_z1_ph_down_dose": "off",
    "light.eden_z1_grow_light": "on",
    "input_number.eden_z1_ph_hi": "6.2",
    "input_number.eden_z1_ph_lo": "5.8",
}

SERVICE_LOG: list[tuple[str, str, dict]] = []


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _drift(entity_id: str) -> None:
    """Nudge a sensor slightly, the way a real reservoir wanders between reads."""
    if entity_id == "sensor.eden_z1_ph":
        STATE[entity_id] = f"{float(STATE[entity_id]) + random.uniform(-0.02, 0.03):.2f}"
    elif entity_id == "sensor.eden_z1_water_temp":
        STATE[entity_id] = f"{float(STATE[entity_id]) + random.uniform(-0.1, 0.1):.1f}"


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload: object, code: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler's naming)
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/states/"):
            entity_id = path.removeprefix("/api/states/")
            if entity_id not in STATE:
                self._send({"message": "Entity not found."}, 404)
                return
            _drift(entity_id)
            self._send(
                {
                    "entity_id": entity_id,
                    "state": STATE[entity_id],
                    "attributes": {},
                    "last_updated": _now_iso(),
                }
            )
            return

        if path.startswith("/api/history/period/"):
            entity_id = parse_qs(parsed.query).get("filter_entity_id", [""])[0]
            base = float(STATE.get(entity_id, "0") or 0)
            now = datetime.now(UTC)
            series = [
                {
                    "entity_id": entity_id,
                    "state": f"{base - 0.3 + i * 0.05:.2f}",
                    "last_updated": (now - timedelta(hours=6 - i * 0.5)).isoformat(),
                }
                for i in range(12)
            ]
            self._send([series])
            return

        self._send({"message": "Not found."}, 404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/api/services/"):
            self._send({"message": "Not found."}, 404)
            return

        domain, _, service = path.removeprefix("/api/services/").partition("/")
        length = int(self.headers.get("Content-Length") or 0)
        data = json.loads(self.rfile.read(length) or b"{}")
        SERVICE_LOG.append((domain, service, data))
        print(f"  <- SERVICE {domain}.{service} {data}", flush=True)

        entity_id = data.get("entity_id", "")
        if domain == "input_number" and service == "set_value":
            STATE[entity_id] = str(data.get("value"))
        elif service == "turn_on":
            STATE[entity_id] = "on"
            if entity_id == "switch.eden_z1_ph_down_dose":
                # Stand in for the ESPHome auto-off + the acid actually landing.
                ph = "sensor.eden_z1_ph"
                STATE[ph] = f"{float(STATE[ph]) - 0.18:.2f}"
                STATE[entity_id] = "off"
                print(f"  ** dose pulsed; pH now {STATE[ph]}", flush=True)
        elif service == "turn_off":
            STATE[entity_id] = "off"

        self._send([])

    def log_message(self, *args: object) -> None:
        """Silence the default per-request access log; we print what matters."""


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"mock Home Assistant on http://127.0.0.1:{PORT}  (Ctrl-C to stop)")
    print(f"seed pH = {STATE['sensor.eden_z1_ph']}  (basil band is 5.8..6.2)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\nstopped after {len(SERVICE_LOG)} service calls")


if __name__ == "__main__":
    main()
