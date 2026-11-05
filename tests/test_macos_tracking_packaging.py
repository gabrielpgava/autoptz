"""Packaging regression tests for the macOS ARM64 advanced tracker."""

from __future__ import annotations

from pathlib import Path

from autoptz import _tracking_selftest


ROOT = Path(__file__).resolve().parents[1]


def test_arm64_build_enables_and_checks_advanced_tracking() -> None:
    script = (ROOT / "packaging" / "build_macos.sh").read_text(encoding="utf-8")
    assert 'if [[ "${ARCH}" == "arm64" ]]' in script
    assert "INSTALL_ARGS+=(--with-tracking)" in script
    assert '"${PY}" -m autoptz --check-tracking' in script
    assert '"${APP}/Contents/MacOS/AutoPTZ" --check-tracking' in script


def test_build_does_not_skip_required_preflight_with_skip_install() -> None:
    script = (ROOT / "packaging" / "build_macos.sh").read_text(encoding="utf-8")
    assert script.index('SKIP_INSTALL:-0') < script.index('"${PY}" -m autoptz --check-tracking')


def test_tracking_preflight_returns_failure_when_torch_is_missing(monkeypatch) -> None:
    import importlib

    original = importlib.import_module

    def reject_torch(name: str, *args, **kwargs):
        missing_modules = {
            "torch",
            "boxmot",
            "boxmot.trackers",
            "boxmot.reid",
            "boxmot.appearance.reid_auto_backend",
        }
        if name in missing_modules:
            raise ImportError("simulated missing optional tracking stack")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", reject_torch)
    result = _tracking_selftest.check_tracking_runtime()
    assert result["ok"] is False
    assert any("PyTorch import failed" in error for error in result["errors"])
    assert any("BoxMOT import failed" in error for error in result["errors"])
    assert result["neural_engine_verified"] is False
    assert result["reid_weights_tested"] is False


def test_tracking_preflight_cli_exit_code(monkeypatch, capsys) -> None:
    import json

    monkeypatch.setattr(
        _tracking_selftest,
        "check_tracking_runtime",
        lambda: {"ok": False, "errors": ["failed"]},
    )
    assert _tracking_selftest.run_tracking_preflight() == 1
    output = json.loads(capsys.readouterr().out)
    assert output["errors"] == ["failed"]
