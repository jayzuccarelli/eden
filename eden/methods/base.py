"""GrowMethod: the ONE place where behavior (not data) varies by cultivation
technique. DWC today; aeroponics / NFT are new files later that drop in WITHOUT
touching loop.py, the tool API, the entity contract, or the data model.

Mirrors saccade/sensors/base.py: a tiny Protocol, concrete impls in sibling
files, selected by a config string via if/elif (see methods/__init__.py). No
registry, no entry-points, no validate() pass — that machinery is YAGNI at one
method and is a cheap two-way door to add when a SECOND method exists.

Two things the candidates' first cut got wrong and this fixes:

1. plan() takes RECENT ACTIONS, not just current readings. pH/EC have long dead
   time (a dose takes 10+ min to register). A controller that re-doses every tick
   because "pH still high" overshoots. State is PASSED IN (not fetched inside) so
   plan() stays a pure function — still trivially stub-testable.

2. A method declares its REFLEX requirements, not only its agent-side cadence.
   The two-tier split means life-critical fast loops live in firmware/HA, not in
   the agent. DWC's reflex spec = dose-pulse cap + light schedule. Aeroponics'
   reflex spec = the mist duty-cycle ITSELF (roots desiccate in minutes; that
   cannot live behind the network in a Python tick). reflex_spec is the seam on
   the SAFETY tier; required_* + tick_interval_s is the seam on the AGENT tier.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from eden.schema import Action, PlantProfile, Reading


@runtime_checkable
class GrowMethod(Protocol):
    # AGENT-tier contract -------------------------------------------------------
    key: str                      # "dwc" | "aeroponic" | "nft"
    required_sensors: set[str]    # roles the method reads, e.g. {"ph","water_temp"}
    required_actuators: set[str]  # roles it drives, e.g. {"ph_down_dose","light"}
    tick_interval_s: int          # how often the AGENT reasons (DWC ~minutes)

    def plan(
        self,
        readings: dict[str, Reading],
        recent_actions: list[Action],
        profile: PlantProfile,
        now: float,
    ) -> list[Action]:
        """Pure function: given current state + what was recently done + targets,
        return desired Actions. No I/O. Caller applies them through actuate(),
        where the reflex layer clamps. Empty list = nothing to do this tick."""
        ...

    # SAFETY-tier contract ------------------------------------------------------
    def reflex_spec(self) -> "ReflexSpec":
        """Declare what MUST run in the reflex layer (ESPHome/HA) for this method
        to be safe when the agent is offline. The garden survives a dead agent
        because THIS runs in firmware/HA, never in plan(). Implemented once per
        method as HA blueprint instantiation + ESPHome config (see reflex/)."""
        ...


from dataclasses import dataclass, field  # noqa: E402 (kept near its only user)


@dataclass
class ReflexSpec:
    """The firmware/HA-resident guarantees a method needs. This is DECLARATIVE —
    eden does not run it; it's the spec you implement in esphome/*.yaml +
    reflex/*.yaml (HA blueprint) once per method. Naming it here is what stops a
    new fast method from relitigating the agent/reflex boundary."""

    dose_caps: dict = field(default_factory=dict)      # role -> {max_pulse_s, min_interval_s}
    schedules: dict = field(default_factory=dict)      # role -> {on_hours, ...}
    duty_cycles: dict = field(default_factory=dict)    # role -> {on_s, off_s}  (aero mist)
    alerts: list = field(default_factory=list)         # e.g. ["air_pump_ok"]
