"""The Gardener's tool surface — the agent's ENTIRE vocabulary, and the hardest
one-way door (it binds the prompt, learned behavior, and the voice-gateway
subagent contract). FIVE generic verbs over a (zone_id, role) address space. The
agent NEVER sees a tool named dose_ph_down() and NEVER sees an entity_id.

Why five, not the candidates' six:
  - DROPPED list_zones/describe_zone: runtime discovery for N=1 is YAGNI; the
    prompt states the one zone. Add them (read-only, additive => two-way door)
    when there's genuinely more than one zone to discover.
  - KEPT set_state as a SECOND write path. The frozen invariant is NOT "one write
    verb" — it's "only ONE write path reaches a physical actuator." Stage
    transitions, band retunes, enable/disable are legit agent writes that must
    NOT route through the reflex actuator cap.

Adding hardware / plants / methods adds DATA these tools already accept — never a
new tool. Least-privilege is enforced in CODE here (not in the prompt): actuate()
rejects any role that isn't a registered actuator, so the agent literally cannot
touch the always-on air pump.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from eden.schema import Action, ActOp, ActuationResult, Reading, Sample, Scope, Zone


class GardenerTools:
    """Bound to one instance's zones + an HA client + a journal sink. The agent
    calls these by name; the dispatch from the model's function-calling lives in
    gardener/agent.py."""

    def __init__(self, zones: dict[str, Zone], ha, journal_sink, profiles: dict) -> None:
        self.zones = zones
        self.ha = ha
        self.journal_sink = journal_sink  # callable(record: dict) -> None
        self.profiles = profiles

    # --- reads -----------------------------------------------------------------

    def read(self, zone_id: str, role: str) -> Reading:
        """Current value of one sensor role. Resolves role -> resource -> entity."""
        res = self._sensor(zone_id, role)
        s = self.ha.state(res.entity_id)
        raw = s.get("state")
        stale = raw in (None, "unknown", "unavailable")
        return Reading(
            role=role,
            value=float(raw) if not stale else float("nan"),
            unit=res.unit,
            ts=_ts(s.get("last_updated")),
            stale=stale,
        )

    def history(self, zone_id: str, role: str, hours: float = 24.0) -> list[Sample]:
        """Trend for diagnosis ('has pH crept up?'). Read-only."""
        res = self._sensor(zone_id, role)
        since = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
        out = []
        for pt in self.ha.history(res.entity_id, since):
            try:
                out.append(Sample(value=float(pt["state"]), ts=_ts(pt.get("last_updated"))))
            except (KeyError, ValueError):
                continue
        return out

    # --- the single PHYSICAL write path ----------------------------------------

    def actuate(self, zone_id: str, role: str, action: Action) -> ActuationResult:
        """The ONLY verb that reaches a physical actuator. The reflex layer (HA/
        ESPHome) is the authoritative clamp; this just dispatches the service call
        and reports back. Rejects sensor roles (least-privilege, in code)."""
        res = self._actuator(zone_id, role)
        domain, service, data = _to_service(res.entity_id, action)
        self.ha.call(domain, service, data)
        # The reflex layer enforces caps; v1 reports the requested action as applied
        # and relies on the reflex auto-off. (A future version can read back state
        # to detect clamping and set clamped=True.)
        return ActuationResult(ok=True, applied=data, clamped=False)

    # --- the NON-physical write path (audited, NOT actuator-capped) -------------

    def set_state(self, zone_id: str, key: str, value, reason: str = "") -> None:
        """Agent-driven config/state change: advance growth stage, retune a band,
        enable/disable a zone. Routed to the setpoint input_number helpers when
        it's a band (so the REFLEX layer sees it), journaled always. NEVER touches
        a physical actuator, so the safety invariant holds."""
        zone = self.zones[zone_id]
        if key.endswith((".lo", ".ideal", ".hi")):
            var, _, bound = key.partition(".")
            helper = f"input_number.eden_{zone_id}_{var}_{bound}"
            self.ha.call("input_number", "set_value", {"entity_id": helper, "value": value})
        elif key == "stage":
            zone.profile_id = value  # point the zone at the new-stage profile
        elif key == "enabled":
            zone.enabled = bool(value)
        self.journal_sink(
            {"kind": "state", "zone": zone_id, "key": key, "value": value, "reason": reason}
        )

    # --- narrative + escalation -------------------------------------------------

    def journal(self, zone_id: str, text: str, structured: dict | None = None) -> None:
        self.journal_sink(
            {"kind": "note", "zone": zone_id, "text": text, "structured": structured or {}}
        )

    def alert(self, zone_id: str, severity: str, text: str) -> None:
        """Escalate to the human. v1 routes via HA mobile notify; voice later
        (output channel, not architecture)."""
        self.ha.call("notify", "notify", {"message": f"[eden/{zone_id}/{severity}] {text}"})
        self.journal_sink({"kind": "alert", "zone": zone_id, "severity": severity, "text": text})

    # --- resolution (role -> resource -> entity); least-privilege guards --------

    def _sensor(self, zone_id: str, role: str):
        res = self.zones[zone_id].resource(role)
        if res.kind != "sensor":
            raise PermissionError(f"{role} is not a sensor in {zone_id}")
        return res

    def _actuator(self, zone_id: str, role: str):
        res = self.zones[zone_id].resource(role)
        if res.kind != "actuator":
            raise PermissionError(f"{role} is not an actuator in {zone_id}")
        if res.scope == Scope.SHARED:
            # A shared actuator (future nutrient tank pump feeding N zones) needs
            # write coordination so two zones don't double-dose. v1 has none; this
            # is where a serialize/merge step slots in — addressing is by res.id.
            pass
        return res


def _to_service(entity_id: str, action: Action) -> tuple[str, str, dict]:
    """Map an Action to an HA service call. domain is the entity prefix."""
    domain = entity_id.split(".", 1)[0]
    if action.op == ActOp.PULSE:
        # The reflex layer auto-offs after its cap; we just turn on. Pulse duration
        # is advisory — the ESPHome dose switch has its own safety auto-off.
        return domain, "turn_on", {"entity_id": entity_id}
    if action.op == ActOp.SET:
        return (
            "light",
            "turn_on",
            {"entity_id": entity_id, "brightness_pct": int((action.value or 0) * 100)},
        )
    if action.op == ActOp.ON:
        return domain, "turn_on", {"entity_id": entity_id}
    return domain, "turn_off", {"entity_id": entity_id}


def _ts(iso: str | None) -> float:
    if not iso:
        return 0.0
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0
