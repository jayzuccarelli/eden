"""The Gardener SDK loop, exercised with a scripted fake client (no network).
Mirrors the StubHA pattern: the fake returns canned API responses; we assert the
loop dispatches tool_use blocks, feeds results back, and returns the final text.
"""

from types import SimpleNamespace

from eden.config import load_instance
from eden.gardener.agent import Gardener
from eden.gardener.tools import GardenerTools
from eden.ha import StubHA

INSTANCE = "instance"


def _block(**kw):
    return SimpleNamespace(**kw)


class FakeClient:
    """Yields scripted responses in order; records the messages it was sent."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []
        self.messages = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self._responses.pop(0)


def _gardener(responses):
    zones, profiles = load_instance(INSTANCE)
    ha = StubHA(
        {"sensor.eden_z1_ph": {"state": "6.4", "last_updated": "2026-06-09T12:00:00+00:00"}}
    )
    journal = []
    tools = GardenerTools(zones, ha, journal.append, profiles)
    g = Gardener(tools, "claude-sonnet-5", "test prompt", client=FakeClient(responses))
    return g, ha, journal


def test_run_dispatches_tool_use_and_returns_final_text():
    g, ha, _ = _gardener(
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    _block(
                        type="tool_use",
                        id="tu_1",
                        name="read",
                        input={"zone_id": "z1", "role": "ph"},
                    ),
                ],
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[_block(type="text", text="pH is 6.4, slightly high.")],
            ),
        ]
    )
    out = g.run("check the garden")

    assert out == "pH is 6.4, slightly high."
    # The second request must carry the tool_result for tu_1 with the reading.
    second = g.client.requests[1]
    result_msg = second["messages"][-1]
    assert result_msg["role"] == "user"
    assert result_msg["content"][0]["tool_use_id"] == "tu_1"
    assert "6.4" in result_msg["content"][0]["content"]


def test_tool_error_goes_back_as_is_error():
    g, _, _ = _gardener(
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    # ph is a sensor — actuating it must hit the least-privilege
                    # PermissionError and come back as is_error, not crash.
                    _block(
                        type="tool_use",
                        id="tu_1",
                        name="actuate",
                        input={"zone_id": "z1", "role": "ph", "op": "on"},
                    ),
                ],
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[_block(type="text", text="understood, ph is read-only")],
            ),
        ]
    )
    out = g.run("turn on the ph")

    assert out == "understood, ph is read-only"
    result = g.client.requests[1]["messages"][-1]["content"][0]
    assert result["is_error"] is True
    assert "PermissionError" in result["content"]
