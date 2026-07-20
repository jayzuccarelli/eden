"""Runtime config + instance loader. Everything tunable lives here (mirrors
saccade/config.py: flat dataclass, stdlib dotenv autoload, no magic constants).

This module is the boundary: it loads the instance YAML (the future "Hortus")
into the domain dataclasses from schema.py. eden/ imports NOTHING from instance/;
it only reads the YAML path this config points at. Extraction later = rename the
instance dir, change one path. No code moves.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

from eden.schema import Band, PlantProfile, Resource, Scope, Zone


def _apply_dotenv(path: str) -> None:
    try:
        with open(path) as f:
            lines = f.readlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip("\"'"))


_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_apply_dotenv(os.path.join(_repo_root, "instance", ".env"))


@dataclass
class Config:
    ha_url: str = os.environ.get("EDEN_HA_URL", "http://localhost:8123")
    ha_token: str = os.environ.get("EDEN_HA_TOKEN", "")
    instance_dir: str = os.environ.get("EDEN_INSTANCE", os.path.join(_repo_root, "instance"))
    gardener_model: str = os.environ.get("EDEN_MODEL", "claude-sonnet-5")
    journal_path: str = os.environ.get("EDEN_JOURNAL", "journal.jsonl")
    # Agent reasoning cadence (separate from method.tick_interval_s and from the
    # reflex tick). Two-way door: a cron/interval calls run_once this often.
    gardener_interval_s: int = int(os.environ.get("EDEN_INTERVAL", "1800"))


def load_instance(instance_dir: str) -> tuple[dict[str, Zone], dict[str, PlantProfile]]:
    """Parse instance/zones.yaml + instance/profiles/*.yaml into domain objects.
    A flat dict + tiny resolution, NOT a relational registry (that's YAGNI for
    one ~4-device zone). Split into more files / a DB later if it grows."""
    with open(os.path.join(instance_dir, "zones.yaml")) as f:
        raw = yaml.safe_load(f)

    profiles: dict[str, PlantProfile] = {}
    prof_dir = os.path.join(instance_dir, "profiles")
    for fn in os.listdir(prof_dir):
        if not fn.endswith((".yaml", ".yml")):
            continue
        with open(os.path.join(prof_dir, fn)) as f:
            p = yaml.safe_load(f)
        profiles[p["id"]] = PlantProfile(
            id=p["id"],
            species=p["species"],
            stage=p["stage"],
            bands={k: Band(**v) for k, v in p["bands"].items()},
            light_hours=p.get("light_hours", 0.0),
            light_brightness=p.get("light_brightness", 0.0),
        )

    zones: dict[str, Zone] = {}
    for z in raw["zones"]:
        resources: dict[str, list[Resource]] = {}
        for r in z["resources"]:
            res = Resource(
                id=r["id"],
                role=r["role"],
                kind=r["kind"],
                entity_id=r["entity_id"],
                unit=r.get("unit", ""),
                scope=Scope(r.get("scope", "zone")),
                caps=r.get("caps", {}),
            )
            resources.setdefault(res.role, []).append(res)
        zones[z["id"]] = Zone(
            id=z["id"],
            display_name=z["display_name"],
            method=z["method"],
            profile_id=z["profile_id"],
            resources=resources,
            enabled=z.get("enabled", True),
        )
    return zones, profiles
