"""DWCMethod.plan() is a pure function, test it with no HA, no network, exactly
like saccade tests backends with stub.py. Proves the dead-time guard and the
band logic without touching hardware."""

from eden.methods.dwc import DWCMethod
from eden.schema import Action, ActOp, Band, PlantProfile, Reading

PROFILE = PlantProfile(
    id="basil_genovese",
    species="basil",
    stage="vegetative",
    bands={"ph": Band(6.0, 5.8, 6.2), "water_temp": Band(21, 18, 24)},
)


def _readings(ph: float, stale: bool = False):
    return {
        "ph": Reading("ph", ph, "pH", 0.0, stale=stale),
        "water_temp": Reading("water_temp", 21.0, "C", 0.0),
    }


def test_doses_when_ph_above_band():
    m = DWCMethod()
    actions = m.plan(_readings(6.5), [], PROFILE, now=0.0)
    assert len(actions) == 1
    assert actions[0].role == "ph_down_dose"
    assert actions[0].op == ActOp.PULSE


def test_no_dose_in_band():
    m = DWCMethod()
    assert m.plan(_readings(6.0), [], PROFILE, now=0.0) == []


def test_refractory_blocks_redose():
    """Dead-time guard: a recent dose suppresses re-dosing even if pH still high."""
    m = DWCMethod()
    recent = [Action(role="ph_down_dose", op=ActOp.PULSE, duration_s=1.5)]
    assert m.plan(_readings(6.5), recent, PROFILE, now=0.0) == []


def test_stale_reading_no_action():
    m = DWCMethod()
    assert m.plan(_readings(6.5, stale=True), [], PROFILE, now=0.0) == []


def test_reflex_spec_declares_caps():
    spec = DWCMethod().reflex_spec()
    assert "ph_down_dose" in spec.dose_caps
    assert "air_pump_ok" in spec.alerts
