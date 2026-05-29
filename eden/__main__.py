"""Wire it together and run one Gardener pass. Mirrors saccade's __main__:
flat Config, hand-wired construction, `python -m eden`.

    python -m eden            # one control + reasoning pass over all zones
"""

from __future__ import annotations

from eden.config import Config, load_instance
from eden.gardener.agent import Gardener, journal_sink_factory
from eden.gardener.tools import GardenerTools
from eden.ha import HA, now
from eden.loop import run_once


def main() -> None:
    c = Config()
    zones, profiles = load_instance(c.instance_dir)
    ha = HA(c.ha_url, c.ha_token)
    sink = journal_sink_factory(c.journal_path)
    tools = GardenerTools(zones, ha, sink, profiles)

    # Deterministic reflex-tier policy pass (runs without the model).
    run_once(zones, tools, profiles, recent_by_zone={}, now=now())

    # Agentic pass (stubbed until the SDK loop is wired — see agent.py).
    print(f"eden — zones={list(zones)} model={c.gardener_model}")
    _ = Gardener(tools, c.gardener_model, system_prompt="(see instance/prompt.md)")


if __name__ == "__main__":
    main()
