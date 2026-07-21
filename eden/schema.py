"""The contracts every part of Eden speaks. Single source of truth.

Stdlib dataclasses only (mirrors saccade/schema.py) so the package installs and
tests run anywhere. These are the ONE-WAY-DOOR types: zone_id threads through
everything, sensors/actuators are addressed by ROLE (not entity_id), hardware
resolves to a RESOURCE that may be shared, and plant targets are pure DATA.

Nothing here knows about any specific garden, that lives in instance/ as YAML.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

# --- value objects the Gardener tools pass around -------------------------------


@dataclass
class Reading:
    """One current sensor value, role-addressed."""

    role: str
    value: float
    unit: str
    ts: float
    stale: bool = False  # True if HA reports the entity unavailable/old


@dataclass
class Sample:
    """One point in a history series."""

    value: float
    ts: float


class ActOp(StrEnum):
    PULSE = "pulse"  # run for duration_s then stop (dosing pump)
    SET = "set"  # set a level 0..1 (light brightness)
    ON = "on"
    OFF = "off"


@dataclass
class Action:
    """A desired effect on ONE actuator role. GrowMethod.plan() returns these;
    actuate() applies them. The reflex layer may CLAMP, clamped/applied report
    what actually happened so the agent learns the real limits empirically."""

    role: str
    op: ActOp
    value: float | None = None  # for SET (0..1)
    duration_s: float | None = None  # for PULSE
    reason: str = ""


@dataclass
class ActuationResult:
    ok: bool
    applied: dict  # what was actually sent after clamping
    clamped: bool = False
    reason: str = ""


# --- the domain entities (config-driven; instantiated from instance/ YAML) ------


class Scope(StrEnum):
    """Where a Resource physically lives. v1 is all ZONE. SHARED is the seam that
    lets a future single nutrient tank / shelf light / air pump feed N zones
    without re-plumbing actuate(), see README one-way door #2."""

    ZONE = "zone"
    SHARED = "shared"


@dataclass
class Resource:
    """A physical sensor or actuator, addressed by its own id. A Zone references
    a Resource by ROLE; the Resource holds the HA entity_id and its scope.

    This indirection (role -> resource -> entity_id) is what makes shared hardware
    a config edit instead of a rewrite. v1: every resource is scope=ZONE and owned
    by exactly one zone, so it reads like plain per-zone hardware.
    """

    id: str  # e.g. "z1.ph_probe", later "tank.nutrient_pump"
    role: str  # semantic handle: "ph", "ph_down_dose", "light"
    kind: str  # "sensor" | "actuator"
    entity_id: str  # HA entity, e.g. "sensor.eden_z1_ph"
    unit: str = ""
    scope: Scope = Scope.ZONE
    caps: dict = field(default_factory=dict)  # actuator hints (NON-authoritative;
    #   the reflex layer is the sole authority: see one-way door #6). e.g.
    #   {"op": "pulse", "max_duration_s": 2.0, "min_interval_s": 600}


@dataclass
class Band:
    """A target + acceptable range for one variable. The reflex layer's hard band
    is the input_number helper; this is the agent's policy view of the same."""

    target: float
    lo: float
    hi: float


@dataclass
class PlantProfile:
    """Targets-as-data for one species at one growth stage. A diverse plant or a
    stage transition is new DATA, never code. Keyed and shared across zones."""

    id: str  # "basil_genovese"
    species: str
    stage: str  # "vegetative" | "flowering" | ...
    bands: dict[str, Band]  # {"ph": Band(6.0,5.8,6.2), "water_temp": Band(...)}
    light_hours: float = 0.0
    light_brightness: float = 0.0  # 0..1 setpoint when on


@dataclass
class Zone:
    """The unit of control and isolation. v1 = one zone "z1". Everything the
    Gardener does is scoped to a zone. Adding pot #2 = appending a Zone in config.

    resources is role -> [Resource]. It is a LIST per role (not a single
    Resource) so redundant probes (two pH sensors voting) and shared ambient
    sensors fall out for free, v1 lists are length 1.
    """

    id: str  # "z1"
    display_name: str
    method: str  # grow-method key: "dwc"
    profile_id: str  # -> PlantProfile
    resources: dict[str, list[Resource]] = field(default_factory=dict)
    enabled: bool = True

    def resource(self, role: str) -> Resource:
        """Resolve a role to its (primary) Resource. The single place that knows
        role -> hardware. v1 returns the first; aggregation/voting slots in here."""
        return self.resources[role][0]
