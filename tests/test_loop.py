"""Loop + tools over a StubHA, no network. Proves: (1) the loop is method-
agnostic and drives the right HA service for an out-of-band reading, (2) actuate
rejects sensor roles (least-privilege in code), (3) the method swap doesn't touch
the loop (run a fake method through the same loop)."""

from eden.gardener.tools import GardenerTools
from eden.ha import StubHA
from eden.loop import tick
from eden.methods.base import ReflexSpec
from eden.schema import Action, ActOp, Band, PlantProfile, Resource, Zone

PROFILE = PlantProfile("basil_genovese", "basil", "vegetative", {"ph": Band(6.0, 5.8, 6.2)})


def _zone():
    return Zone(
        id="z1",
        display_name="Z1",
        method="dwc",
        profile_id="basil_genovese",
        resources={
            "ph": [Resource("z1.ph", "ph", "sensor", "sensor.eden_z1_ph", "pH")],
            "water_temp": [
                Resource("z1.wt", "water_temp", "sensor", "sensor.eden_z1_water_temp", "C")
            ],
            "ph_down_dose": [
                Resource("z1.dose", "ph_down_dose", "actuator", "switch.eden_z1_ph_down_dose")
            ],
            "light": [Resource("z1.light", "light", "actuator", "light.eden_z1_grow_light")],
        },
    )


def _tools(ha):
    return GardenerTools(
        {"z1": _zone()}, ha, journal_sink=lambda r: None, profiles={"basil_genovese": PROFILE}
    )


def test_out_of_band_ph_triggers_dose_service():
    ha = StubHA(
        states={
            "sensor.eden_z1_ph": {"state": "6.5", "last_updated": ""},
            "sensor.eden_z1_water_temp": {"state": "21", "last_updated": ""},
        }
    )
    tools = _tools(ha)
    tick(_zone(), tools, {"basil_genovese": PROFILE}, recent=[], now=0.0)
    assert any(
        c[1] == "turn_on" and c[2]["entity_id"] == "switch.eden_z1_ph_down_dose" for c in ha.calls
    )


def test_actuate_rejects_sensor_role():
    tools = _tools(StubHA())
    try:
        tools.actuate("z1", "ph", Action(role="ph", op=ActOp.ON))
        raise AssertionError("should reject a sensor role")
    except PermissionError:
        pass


def test_loop_is_method_agnostic():
    """A fake method with different roles runs through the SAME tick() unchanged,
    this is the proof that aeroponic/nft drop in without editing the loop."""
    import eden.loop as looplib

    class FakeMethod:
        key = "fake"
        required_sensors = {"ph"}
        required_actuators = {"light"}
        tick_interval_s = 60

        def plan(self, readings, recent, profile, now):
            return [Action(role="light", op=ActOp.SET, value=0.5)]

        def reflex_spec(self):
            return ReflexSpec()

    orig = looplib.make_method
    looplib.make_method = lambda key: FakeMethod()
    try:
        ha = StubHA(states={"sensor.eden_z1_ph": {"state": "6.0", "last_updated": ""}})
        z = _zone()
        z.method = "fake"
        tick(z, _tools(ha), {"basil_genovese": PROFILE}, recent=[], now=0.0)
        assert any(c[2].get("entity_id") == "light.eden_z1_grow_light" for c in ha.calls)
    finally:
        looplib.make_method = orig
