"""Grow-method selection: a hand-written if/elif, exactly like saccade's
make_backend in __main__.py. No registry, no entry-points, that's YAGNI at one
method. Adding aeroponic/nft = one import + one branch here.
"""

from __future__ import annotations

from eden.methods.base import GrowMethod


def make_method(key: str) -> GrowMethod:
    if key == "dwc":
        from eden.methods.dwc import DWCMethod

        return DWCMethod()
    # if key == "aeroponic":
    #     from eden.methods.aeroponic import AeroponicMethod
    #     return AeroponicMethod()
    # if key == "nft":
    #     from eden.methods.nft import NFTMethod
    #     return NFTMethod()
    raise ValueError(f"unknown grow method: {key!r}")
