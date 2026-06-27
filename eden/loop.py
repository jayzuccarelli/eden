"""The grow-method-AGNOSTIC control loop. It never names DWC, never names a pump,
never hardcodes pH. It reads the zone's method, asks plan() for desired Actions,
and applies each through the single actuate() write path (reflex-clamped).

Identical for every method and every zone — adding a method or a zone never edits
this file. That's the test the directive demands.

Note the two adversarial fixes wired in:
  - recent_actions is fetched and passed INTO plan() (dead-time/overshoot guard),
    keeping plan() pure.
  - actions are grouped by RESOURCE before applying, so a future shared actuator
    (one tank pump, N zones) gets coordinated writes instead of double-dosing.
"""

from __future__ import annotations

from collections import defaultdict

from eden.methods import make_method
from eden.schema import Action, Zone


def tick(zone: Zone, tools, profiles: dict, recent: list[Action], now: float) -> list[Action]:
    """One control tick for one zone. Pure-ish: reads via tools, returns the
    Actions it applied (so the caller can feed them back as `recent` next tick)."""
    if not zone.enabled:
        return []
    method = make_method(zone.method)
    profile = profiles[zone.profile_id]

    readings = {role: tools.read(zone.id, role) for role in method.required_sensors}
    actions = method.plan(readings, recent, profile, now)

    # Group by the resolved resource so SHARED hardware is coordinated, not raced.
    by_resource: dict[str, list[Action]] = defaultdict(list)
    for a in actions:
        by_resource[zone.resource(a.role).id].append(a)

    applied: list[Action] = []
    for _resource_id, group in by_resource.items():
        for a in group:  # v1: one action per resource; merge step lands here later
            tools.actuate(zone.id, a.role, a)
            applied.append(a)
    return applied


def run_once(
    zones: dict[str, Zone], tools, profiles: dict, recent_by_zone: dict, now: float
) -> None:
    """Tick every zone once. The Gardener calls this on its slow cadence (cron /
    interval). Fast life-critical loops are NOT here — they're in the reflex tier."""
    for zone in zones.values():
        recent = recent_by_zone.get(zone.id, [])
        applied = tick(zone, tools, profiles, recent, now)
        recent_by_zone[zone.id] = applied
