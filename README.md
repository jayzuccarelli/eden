# Eden

[![check](https://github.com/jayzuccarelli/eden/actions/workflows/ci.yml/badge.svg)](https://github.com/jayzuccarelli/eden/actions/workflows/ci.yml)

An AI-tended hydroponic garden. A Claude "Gardener" agent autonomously tends a
living grow system through Home Assistant. The point is the agentic AI-keeper
story, not the vegetables.

**v1 scope:** ONE DWC bucket, ONE basil plant. **v1 structure:** built for N
zones, diverse plants, and new grow methods, without rewrites. *Narrow scope,
right structure.*

## Two tiers (hard boundary)

1. **Reflex**: ESPHome on the XIAO + Home Assistant automations/blueprints.
   Deterministic safety: keep pH in band, cap any dose to a short pulse, run the
   light schedule, alert if the air pump dies. **Runs even if the agent is
   offline.** Sole authority for hard caps.
2. **Gardener**: a plain Sonnet-class agent (`eden/gardener/`) with tools scoped
   ONLY to the garden. Reads sensor history, sets policy/dosing, journals, alerts.
   A realtime voice agent can call it as a subagent and inherits exactly its
   five-verb surface, least privilege.

The agent is never in a fast/life-critical loop. Mist-style sub-minute cycles
(future aeroponics) live in the reflex tier, declared by `GrowMethod.reflex_spec()`.

## The one-way doors (get these right now: they're irreversible)

1. **zone_id threaded through everything**, even at N=1. Entity ids, tool calls,
   history, setpoints, journal are all zone-scoped. Adding pot #2 = a config block.
2. **Generic role-addressed tool API.** Five verbs (`read`, `actuate`,
   `set_state`, `journal`, `alert`, plus `history`) over a `(zone, role)` space.
   The agent never sees `dose_ph_down()` or an entity_id. New hardware/plants/
   methods add DATA the tools already accept, never a new tool. `actuate` is the
   ONLY path to a physical actuator; `set_state` handles non-physical state and
   never touches hardware.
3. **Sensors/actuators addressed by ROLE → RESOURCE → entity_id.** A `Resource`
   carries a `scope` (`zone` | `shared`). v1 is all `zone`, but addressing by
   resource-id means a future shared nutrient tank / shelf light feeding multiple
   zones is a config edit + a write-coordination step at the `actuate` chokepoint,
   not a re-plumb. ("Zones never share state" is physically false at v2; this
   is the fix.)
4. **GrowMethod is the one strategy seam.** The loop calls `method.plan(readings,
   recent_actions, profile, now) -> [Action]` and never names DWC or a pump.
   `plan()` takes recent actions (dead-time/overshoot guard) and stays pure.
   Methods also declare `reflex_spec()`: what must live in firmware/HA. DWC is
   the only method today; aeroponic/NFT are new files in `eden/methods/` that drop
   in with zero loop edits.
5. **HA entity namespacing `eden_<zone>_<role>` from the first entity.** HA history
   is keyed by entity_id; shipping `sensor.eden_ph` then adding a bucket orphans
   the basil's history. The ESPHome config is a zone-templated package; zone 2 is
   a 3-line include with `zone: z2`.
6. **Setpoint → reflex handoff via HA `input_number` helpers.** HA automations can
   only read HA state, not a Python store. `set_state(z, "ph.hi", v)` writes
   `input_number.eden_z1_ph_hi`; the reflex blueprint reads it. The band survives
   an agent crash and the agent/reflex contract is real, not decorative.
7. **Domain vs instance separation.** `eden/` imports nothing from `instance/`.
   `instance/` is YAML + prompt + secrets (the future "Hortus"). Extraction =
   rename a directory, `pip install eden`. No code moves.

## Reflex automations live in your HA config (single source of truth)

The per-zone guard is an **HA blueprint** (`reflex/eden_zone_guard.blueprint.yaml`),
deployed into your Home Assistant config under `blueprints/automation/eden/`. Zone 2's
guard is a blueprint *instantiation*, not a forked automation. Eden does not keep a
drifting mirror, the HA config is where HA loads it.

## Layout

```
eden/                 reusable domain logic (the future framework)
  schema.py           Zone / Resource / PlantProfile / Reading / Action / ...
  config.py           flat Config + instance YAML loader (saccade dotenv pattern)
  ha.py               thin HA REST client + StubHA for tests (no ABC: HA is always HA)
  loop.py             method-agnostic control loop
  methods/
    base.py           GrowMethod Protocol + ReflexSpec (agent-tier + safety-tier seams)
    dwc.py            the v1 method
    __init__.py       make_method() if/elif (saccade make_backend pattern)
  gardener/
    tools.py          the 5-verb (+history) tool surface; least-privilege in code
    agent.py          Sonnet-class agent: TOOL_SCHEMAS + the manual tool-use loop
instance/             personal config = future "Hortus" (data only, no logic)
  zones.yaml          the single z1 block: role -> resource -> entity_id + caps
  profiles/*.yaml     plant targets-as-data
  prompt.md           Gardener voice
esphome/
  eden-zone.yaml      multi-zone-ready firmware template (zone-prefixed entities)
  eden-z1.yaml        zone 1 include
reflex/
  eden_zone_guard.blueprint.yaml   HA reflex guard (deployed to ha-config)
tests/                pure-function plan() tests + loop-over-StubHA tests
```

## Run

Tooling is [uv](https://docs.astral.sh/uv/) + [ruff](https://docs.astral.sh/ruff/).

```
uv sync                # create .venv, install deps + dev tools (pinned by uv.lock)
uv run pytest          # no HA needed (StubHA)
uv run ruff check      # lint
uv run ruff format     # format
uv run python -m eden  # one pass over all zones (needs instance/.env)
```

## Build the physical garden

Eden runs on a free compute base (a box with Home Assistant + a Claude API key)
plus off-the-shelf hydroponic hardware. **[docs/hardware.md](docs/hardware.md)** is
the full bill of materials, every part, where to buy it, the verified XIAO
ESP32-S3 pinout, and the germination steps to go from empty bucket to basil.

**[BUILD.md](BUILD.md)** is the step-by-step assembly guide. Read its Safety
section first: this build puts mains-powered equipment beside an open bucket of
water and has you handle a corrosive liquid.

## Deliberately NOT built (YAGNI: add when a 2nd method/zone is real)

No plugin registry / entry-points, no central Intent dispatch, no relational
config registry, no agent-side safety mirror (reflex is sole authority), no
`required_*` validation pass, no `list_zones`/`describe_zone` discovery, no
websocket transport, no DB, no saccade glance→focus integration, no aeroponic/NFT
code. Each is a two-way door behind the seams above.
