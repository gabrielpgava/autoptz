# Apple Silicon / NDI tracking roadmap

**Status:** iterative work in `gabrielpgava/autoptz`; upstream baseline v2.2.0.

## Mission

Build a reliable macOS ARM64 workflow for live-event PTZ cameras receiving NDI.
The primary target is explicitly selected by the operator. Preserve identity
through occlusions and crossings, avoid unexpected retargeting, and prioritize
safe, stable pan/tilt movement over artificially high detection FPS.

## Measured success criteria

- Real arm64, not an x86_64 process running under Rosetta.
- Verify the *effective* tracker and ReID backend at runtime, not importability.
- For each model: record CPU vs Core ML latency p50/p95 and measure how the
  Core ML model partitions operators across CPU/GPU/Neural Engine in Xcode.
  The existence of `CoreMLExecutionProvider` alone is **not** proof of ANE use.
- Measure NDI capture, conversion/copy, inference, tracking, target-lock,
  control-loop and PTZ send latency independently.
- Test fixed recorded clips, including single person, identical outfits,
  crossovers, back turns, long-distance/wide-stage subjects, occlusions,
  LED backgrounds and low-light/high-contrast changes.
- Record ID switches per sequence, lost/recovery time, tracking failure rate,
  detection recall, framing error, stop latency and PTZ motion smoothness.
- Fail safely: when evidence becomes ambiguous or stale, stop physical movement,
  keep the target identity, and wait for reliable reacquisition.

## TODO phases

### P0: truthful diagnostics and detection reliability
- [x] Safe IoU fallback if BoxMOT fails to initialize; report the **real** tracker.
- [x] Adjust the default small-person cutoff for wide shots (2% frame height);
      existing saved profiles require manual adjustment.
- [x] Configure the ARM64 build to install BoxMOT/Torch and require a source and
      frozen-bundle runtime preflight before packaging succeeds.
- [ ] Confirm the preflight on macOS CI and test actual OSNet model loading and
      reacquisition on a real M-series Mac (the import-only ReID check does not
      validate downloadable weights).
- [ ] Record runtime backends, model names and latency in a concise report.
- [ ] Run the existing `tools/bench/ep_compare.py` and full tracking benchmark
      on an actual Apple Silicon Mac and preserve the results.

### P1: selected-person tracking
- [ ] Separate low-confidence detections for the tracker's association stage
      without exposing weak boxes as confirmed operator targets.
- [ ] Replace stale detection replay on skipped frames with timestamped prediction
      (test against `detect_interval=1/2/4` and both tracker backends).
- [ ] Establish measured accuracy for YOLO11n/s/m before selecting a new default.
- [ ] Validate appearance re-identification and face+body fusion; require margin
      over the runner-up before any target switch.
- [ ] Ensure the release build either ships a functioning appearance backend or
      clearly warns that stable identity tracking is unavailable.

### P2: Apple Silicon acceleration / NDI
- [ ] Benchmark ORT/CoreML `MLProgram` against direct Core ML models exported
      from canonical weights. Use compute units from profile evidence.
- [ ] Investigate Core ML-compatible appearance embeddings as an alternative to
      a full BoxMOT/PyTorch dependency for macOS.
- [ ] Profile NDI FourCC conversion, unnecessary copies and source timestamp age.
- [ ] Test latest-frame semantics and avoid commanding the camera using stale
      observations when decoding/inference stalls.

### P3: physical PTZ calibration and release
- [ ] Compare legacy PD+OneEuro control vs bounded jerk/deceleration profiles.
- [ ] Preserve emergency stop and stop-on-loss while improving normal stops.
- [ ] Model pan/tilt acceleration and zoom-dependent speed for actual camera models.
- [ ] Validate 30-minute real-camera soak tests, multi-person switches and
      camera reconnects; build unsigned ARM64 test DMGs for field verification.
- [ ] Route the fork's in-app updater to `gabrielpgava/autoptz` releases
      (the upstream default is `AutoPTZ/autoptz`) and validate rollback safety.
- [ ] Confirm third-party model/data licensing before commercial distribution.

## Working practice

Use short feature branches and PRs against `main`. Add regression tests before
changing inference/identity/PTZ behavior. Keep Linux/Windows support and
non-accelerated fallback intact. Use synthetic tests for CI and real NDI/PTZ
hardware for final acceptance. Never advertise the Neural Engine as active
without verifying operator placement on an Apple Silicon machine.

### Local macOS baseline

```bash
python tools/install.py --editable --with-tracking
python tools/bench/ep_compare.py --runs 50
python -m autoptz --log-level INFO
```

For a prebuilt DMG, verify its embedded tracker/runtime independently: a source
venv test does **not** prove the DMG includes the same dependencies.
