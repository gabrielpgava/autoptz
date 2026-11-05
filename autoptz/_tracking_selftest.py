"""Packaging preflight for the optional BoxMOT / appearance-tracking runtime.

This is intentionally separate from the foundation selftest. ARM64 release
builds must fail instead of silently shipping only the lightweight IoU tracker.
No camera, network access, OSNet weights or UI is required here.

Successful import/initialization does NOT prove that a downloaded ReID model
can run, or that any Core ML graph uses the Neural Engine.
"""

from __future__ import annotations

import importlib
import json
import platform
import sys
from typing import Any


def check_tracking_runtime() -> dict[str, Any]:
    """Inspect the real runtime with no downloads or camera access."""
    report: dict[str, Any] = {
        "platform": sys.platform,
        "architecture": platform.machine(),
        "torch_version": None,
        "mps_available": False,
        "boxmot_version": None,
        "tracker_backend": None,
        "reid_api": None,
        "reid_weights_tested": False,
        "neural_engine_verified": False,
        "ok": False,
        "errors": [],
    }
    errors: list[str] = []

    try:
        torch = importlib.import_module("torch")
        report["torch_version"] = str(getattr(torch, "__version__", "unknown"))
        mps = getattr(getattr(torch, "backends", None), "mps", None)
        if mps is not None:
            report["mps_available"] = bool(mps.is_available())
    except Exception as exc:  # noqa: BLE001 - a preflight must report every failure
        errors.append(f"PyTorch import failed: {type(exc).__name__}: {exc}")

    try:
        boxmot = importlib.import_module("boxmot")
        report["boxmot_version"] = str(getattr(boxmot, "__version__", "unknown"))
        trackers = importlib.import_module("boxmot.trackers")
        missing = [
            name for name in ("BotSort", "ByteTrack", "DeepOcSort")
            if not hasattr(trackers, name)
        ]
        if missing:
            errors.append(f"BoxMOT tracker API missing: {', '.join(missing)}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"BoxMOT import failed: {type(exc).__name__}: {exc}")

    # Match the two ReID APIs that BodyReID supports; checking a module spec is
    # not sufficient because a frozen import can still fail at runtime.
    for module_name, symbol in (
        ("boxmot.reid", "ReID"),
        ("boxmot.appearance.reid_auto_backend", "ReidAutoBackend"),
    ):
        try:
            module = importlib.import_module(module_name)
            if callable(getattr(module, symbol, None)):
                report["reid_api"] = f"{module_name}.{symbol}"
                break
        except Exception:  # noqa: BLE001 - try the compatible alternate API
            continue
    if report["reid_api"] is None:
        errors.append("No compatible BoxMOT OSNet ReID API could be imported")

    try:
        import numpy as np

        from autoptz.engine.pipeline.detect import BBox, Detection
        from autoptz.engine.pipeline.track import Tracker

        # A simple artificial target confirms that an actual BoT-SORT instance
        # is usable, not only installed. No weights are fetched for this test.
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        frame[40:200, 80:150] = 192
        tracker = Tracker(tracker_type="botsort")
        tracker.update([Detection(BBox(80, 40, 150, 200), conf=0.95)], frame, fps=30.0)
        report["tracker_backend"] = tracker.backend_name
        if tracker.backend_name != "botsort":
            errors.append(
                f"Expected BoT-SORT, but runtime selected {tracker.backend_name!r}"
            )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"BoT-SORT initialization/update failed: {type(exc).__name__}: {exc}")

    report["errors"] = errors
    report["ok"] = not errors
    return report


def run_tracking_preflight() -> int:
    """Print machine-readable evidence; return nonzero on degraded runtime."""
    result = check_tracking_runtime()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result["ok"] else 1
