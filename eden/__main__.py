"""Wire it together and run one Gardener pass. Mirrors saccade's __main__:
flat Config, hand-wired construction, `python -m eden`.

    python -m eden            # one control + reasoning pass over all zones
"""

from __future__ import annotations

import os

from eden.config import Config, load_instance
from eden.gardener.agent import Gardener, journal_sink_factory
from eden.gardener.tools import GardenerTools
from eden.ha import HA, now
from eden.loop import run_once

TICK_INSTRUCTION = (
    "Routine tending pass. Check current readings and recent trends for every "
    "zone, act if something is out of band, journal what you observed, and stay "
    "quiet if all is well."
)


def main() -> None:
    c = Config()
    zones, profiles = load_instance(c.instance_dir)
    ha = HA(c.ha_url, c.ha_token)
    sink = journal_sink_factory(c.journal_path)
    tools = GardenerTools(zones, ha, sink, profiles)

    # Deterministic reflex-tier policy pass (runs without the model).
    run_once(zones, tools, profiles, recent_by_zone={}, now=now())

    print(f"eden, zones={list(zones)} model={c.gardener_model}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set; skipping the agentic pass")
        return

    with open(os.path.join(c.instance_dir, "prompt.md")) as f:
        system_prompt = f.read()
    gardener = Gardener(tools, c.gardener_model, system_prompt)
    print(gardener.run(TICK_INSTRUCTION))


if __name__ == "__main__":
    main()
