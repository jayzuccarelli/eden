"""DWC (Deep Water Culture): roots permanently submerged in one oxygenated
reservoir. Chemistry drifts slowly, so the AGENT tick is minutes-scale. The
only fast/life-critical things (dose cap, light schedule, air-pump alert) live
in the REFLEX layer per reflex_spec() — never in plan().

This is the ONLY GrowMethod in v1. Aeroponic/NFT are new files; nothing here or
in loop.py changes when they're added.
"""

from __future__ import annotations

from eden.methods.base import GrowMethod, ReflexSpec
from eden.schema import Action, ActOp, PlantProfile, Reading


class DWCMethod:
    key = "dwc"
    required_sensors = {"ph", "water_temp"}
    required_actuators = {"ph_down_dose", "light"}
    tick_interval_s = 300  # 5 min; chemistry drifts slowly

    def __init__(self, dose_pulse_s: float = 1.5, refractory_s: float = 900) -> None:
        # Two-way-door constants: tune freely from observed behavior.
        self.dose_pulse_s = dose_pulse_s
        self.refractory_s = refractory_s  # don't re-dose until a dose registers

    def plan(
        self,
        readings: dict[str, Reading],
        recent_actions: list[Action],
        profile: PlantProfile,
        now: float,
    ) -> list[Action]:
        actions: list[Action] = []

        ph = readings.get("ph")
        ph_band = profile.bands["ph"]
        if ph and not ph.stale and ph.value > ph_band.hi:
            # Dead-time guard: skip if we dosed within the refractory window — the
            # last dose may not have registered yet (overshoot prevention).
            if not self._dosed_recently(recent_actions, "ph_down_dose", now):
                actions.append(
                    Action(
                        role="ph_down_dose",
                        op=ActOp.PULSE,
                        duration_s=self.dose_pulse_s,
                        reason=f"pH {ph.value:.2f} > {ph_band.hi}",
                    )
                )

        # Photoperiod is a REFLEX-tier schedule (survives agent offline). The agent
        # only sets brightness policy; it does not run the on/off clock. v1 keeps
        # this minimal — light scheduling is fully in reflex/esphome.
        return actions

    def _dosed_recently(self, recent: list[Action], role: str, now: float) -> bool:
        # recent_actions carry no ts here for simplicity; the caller filters to the
        # refractory window before passing them in (see loop.py). Presence => recent.
        return any(a.role == role for a in recent)

    def reflex_spec(self) -> ReflexSpec:
        return ReflexSpec(
            dose_caps={"ph_down_dose": {"max_pulse_s": 2.0, "min_interval_s": 600}},
            schedules={"light": {"on_hours": 14}},
            alerts=["air_pump_ok"],
        )


# satisfies the Protocol
_check: GrowMethod = DWCMethod()
