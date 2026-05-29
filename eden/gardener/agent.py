"""The Gardener: a plain Sonnet-class agent (NOT on the saccade glance->focus
harness yet — that's a two-way door for when saccade is eval-proven). It owns the
system prompt + the function-calling dispatch onto GardenerTools.

v1 is a STUB of the model loop on purpose — the directive scaffolds the
structure/interface-defining files; the control logic that matters
(schema/methods/tools/loop) is real. Wiring a specific SDK call is a fill-in.

The tool SCHEMAS below are the frozen contract Voice (the GPT Realtime voice
gateway) binds to when it calls the Gardener as a subagent: least-privilege, five
verbs, (zone, role) addressed.
"""

from __future__ import annotations

import json

from eden.gardener.tools import GardenerTools

TOOL_SCHEMAS = [
    {
        "name": "read",
        "description": "Current value of one sensor role in a zone.",
        "input_schema": {
            "type": "object",
            "properties": {"zone_id": {"type": "string"}, "role": {"type": "string"}},
            "required": ["zone_id", "role"],
        },
    },
    {
        "name": "history",
        "description": "Time series for a sensor role, for trend reasoning.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone_id": {"type": "string"},
                "role": {"type": "string"},
                "hours": {"type": "number"},
            },
            "required": ["zone_id", "role"],
        },
    },
    {
        "name": "actuate",
        "description": "The only verb that drives physical hardware. op=pulse|set|on|off.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone_id": {"type": "string"},
                "role": {"type": "string"},
                "op": {"type": "string", "enum": ["pulse", "set", "on", "off"]},
                "value": {"type": "number"},
                "duration_s": {"type": "number"},
                "reason": {"type": "string"},
            },
            "required": ["zone_id", "role", "op"],
        },
    },
    {
        "name": "set_state",
        "description": "Change non-physical state: advance stage, retune a band "
        "(key like 'ph.hi'), enable/disable. Never touches an actuator.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone_id": {"type": "string"},
                "key": {"type": "string"},
                "value": {},
                "reason": {"type": "string"},
            },
            "required": ["zone_id", "key", "value"],
        },
    },
    {
        "name": "journal",
        "description": "Append a keeper's-log note for a zone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone_id": {"type": "string"},
                "text": {"type": "string"},
                "structured": {"type": "object"},
            },
            "required": ["zone_id", "text"],
        },
    },
    {
        "name": "alert",
        "description": "Escalate to Jay (severity: info|warn|critical).",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone_id": {"type": "string"},
                "severity": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["zone_id", "severity", "text"],
        },
    },
]


class Gardener:
    def __init__(self, tools: GardenerTools, model: str, system_prompt: str) -> None:
        self.tools = tools
        self.model = model
        self.system_prompt = system_prompt

    def dispatch(self, name: str, args: dict):
        """Route a model tool call to GardenerTools. The whole agent->hardware
        path funnels through here, so it's the audit + least-privilege chokepoint."""
        from eden.schema import Action, ActOp

        if name == "read":
            return self.tools.read(args["zone_id"], args["role"])
        if name == "history":
            return self.tools.history(args["zone_id"], args["role"], args.get("hours", 24.0))
        if name == "actuate":
            action = Action(
                role=args["role"],
                op=ActOp(args["op"]),
                value=args.get("value"),
                duration_s=args.get("duration_s"),
                reason=args.get("reason", ""),
            )
            return self.tools.actuate(args["zone_id"], args["role"], action)
        if name == "set_state":
            return self.tools.set_state(args["zone_id"], args["key"], args["value"], args.get("reason", ""))
        if name == "journal":
            return self.tools.journal(args["zone_id"], args["text"], args.get("structured"))
        if name == "alert":
            return self.tools.alert(args["zone_id"], args["severity"], args["text"])
        raise ValueError(f"unknown tool: {name}")

    def run(self, instruction: str) -> str:
        """STUB: one agentic turn. Fill in with the Anthropic SDK call loop
        (messages + TOOL_SCHEMAS, dispatch each tool_use, feed results back). The
        contract above is what matters for the design; the SDK wiring is mechanical.
        """
        raise NotImplementedError(
            "wire the Anthropic SDK loop here; TOOL_SCHEMAS + dispatch() are ready"
        )


def journal_sink_factory(path: str):
    def sink(record: dict) -> None:
        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")

    return sink
