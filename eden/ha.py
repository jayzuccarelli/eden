"""Thin Home Assistant client — the ONLY coupling to HA. Bearer token + REST,
the exact pattern proven in saccade/speakers/home_assistant.py (POST
/api/services/<domain>/<service>, GET /api/states/<entity_id>).

One real impl (HA is always HA — no provider-swap axis, so no ABC), plus a
StubHA for tests so the loop and tools run without a live HA. REST/get-states is
the v1 transport; swap to websocket later behind the same two methods if polling
proves insufficient (two-way door).
"""

from __future__ import annotations

import json
import time
import urllib.request


class HA:
    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token

    def _req(self, path: str, body: dict | None = None) -> dict | list:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.url}{path}",
            data=data,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST" if data is not None else "GET",
        )
        raw = urllib.request.urlopen(req, timeout=10).read()
        return json.loads(raw) if raw else {}

    def state(self, entity_id: str) -> dict:
        """GET /api/states/<entity_id> -> {state, attributes, last_updated, ...}."""
        return self._req(f"/api/states/{entity_id}")  # type: ignore[return-value]

    def history(self, entity_id: str, since_iso: str) -> list[dict]:
        out = self._req(f"/api/history/period/{since_iso}?filter_entity_id={entity_id}")
        return out[0] if out else []  # type: ignore[index]

    def call(self, domain: str, service: str, data: dict) -> None:
        """POST /api/services/<domain>/<service>. Used for actuator commands AND
        for writing setpoint input_number helpers the reflex layer reads."""
        self._req(f"/api/services/{domain}/{service}", data)


class StubHA:
    """Scripted fake (saccade's stub.py pattern). Records calls; returns canned
    states so tests exercise the loop/tools with no network."""

    def __init__(self, states: dict[str, dict] | None = None) -> None:
        self.states = states or {}
        self.calls: list[tuple[str, str, dict]] = []

    def state(self, entity_id: str) -> dict:
        return self.states.get(
            entity_id, {"state": "unknown", "attributes": {}, "last_updated": ""}
        )

    def history(self, entity_id: str, since_iso: str) -> list[dict]:
        return []

    def call(self, domain: str, service: str, data: dict) -> None:
        self.calls.append((domain, service, data))


def now() -> float:
    return time.time()
