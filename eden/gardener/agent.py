"""The Gardener: a plain Sonnet-class agent (NOT on the saccade glance->focus
harness yet — that's a two-way door for when saccade is eval-proven). It owns the
system prompt + the function-calling dispatch onto GardenerTools.

run() is a manual agentic loop (not the SDK tool runner) on purpose: every
hardware-touching call must route through dispatch(), the audit + least-privilege
chokepoint. Uses adaptive thinking; the model id comes from config (EDEN_MODEL).

The tool SCHEMAS below are the frozen contract Voice (the GPT Realtime voice
gateway) binds to when it calls the Gardener as a subagent: least-privilege, five
verbs, (zone, role) addressed.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from eden.gardener.tools import GardenerTools

# Runaway guard: one tending pass should be a handful of reads + at most a couple
# of actuations. If the model is still calling tools after this many turns,
# something is wrong — crash the tick loudly rather than burn tokens.
MAX_TURNS = 25

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
    def __init__(self, tools: GardenerTools, model: str, system_prompt: str, client=None) -> None:
        self.tools = tools
        self.model = model
        self.system_prompt = system_prompt
        self.client = client  # injectable for tests; created lazily in run()

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
            return self.tools.set_state(
                args["zone_id"], args["key"], args["value"], args.get("reason", "")
            )
        if name == "journal":
            return self.tools.journal(args["zone_id"], args["text"], args.get("structured"))
        if name == "alert":
            return self.tools.alert(args["zone_id"], args["severity"], args["text"])
        raise ValueError(f"unknown tool: {name}")

    def run(self, instruction: str) -> str:
        """One agentic tending pass: messages + TOOL_SCHEMAS, dispatch each
        tool_use through the audit chokepoint, feed results back, return the
        final text. Manual loop (not the SDK tool runner) on purpose — every
        hardware-touching call must route through dispatch()."""
        if self.client is None:
            import anthropic

            self.client = anthropic.Anthropic()

        messages: list[dict[str, Any]] = [{"role": "user", "content": instruction}]
        for _ in range(MAX_TURNS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                thinking={"type": "adaptive"},
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
            if response.stop_reason != "tool_use":
                return "".join(b.text for b in response.content if b.type == "text")

            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    out = self.dispatch(block.name, block.input)
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": _result_json(out),
                        }
                    )
                except (PermissionError, KeyError, ValueError) as e:
                    # Expected tool-level errors (least-privilege rejections, bad
                    # zone/role) go back to the model so it can self-correct.
                    # Infra failures (HA down) propagate and crash the tick.
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"{type(e).__name__}: {e}",
                            "is_error": True,
                        }
                    )
            messages.append({"role": "user", "content": results})

        raise RuntimeError(f"gardener exceeded {MAX_TURNS} turns in one pass")


def _result_json(value: object) -> str:
    """Serialize a GardenerTools return (dataclass, list of dataclasses, or
    None) into tool_result content."""
    if value is None:
        return "ok"
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    elif isinstance(value, list):
        value = [asdict(v) if is_dataclass(v) and not isinstance(v, type) else v for v in value]
    return json.dumps(value, default=str)


def journal_sink_factory(path: str):
    def sink(record: dict) -> None:
        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")

    return sink
