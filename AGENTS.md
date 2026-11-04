# Agent guide: AutoPTZ Apple Silicon fork

This fork extends upstream AutoPTZ; preserve the project's cross-platform
contracts and keep `main` usable during live productions.

## Primary objective

Reliable operator-selected presenter tracking from NDI video on Apple Silicon,
with transparent accelerator use and stable/safe physical PTZ motion. See
[docs/apple-silicon-roadmap.md](docs/apple-silicon-roadmap.md).

## Workflow

1. Read the roadmap and the current module/test before changing it.
2. Work in a short-lived `feat/`, `fix/` or `perf/` branch and create a PR
   **only within `gabrielpgava/autoptz`**; do not push experimental changes
   directly to `main`. NEVER create a pull request, issue, branch or commit in
   `AutoPTZ/autoptz` (upstream). Treat upstream as read-only reference material.
3. Use conventional commits and maintain corresponding tests/docs.
4. Keep feature flags for changes that affect identity switching, inference
   cadence, model loading, or physical PTZ movement.
5. Never silently claim Core ML or ANE use based on provider names alone.
   Report exact configured provider, effective backend, measured latency and
   disabled/fallback features.
6. Maintain backwards compatibility for user camera configuration; document
   default changes separately from migrations of saved profiles.
7. Preserve emergency stop/stop-on-loss and do not retarget ambiguously.
8. Run `ruff check autoptz/ tests/ tools/`, `ruff format --check`,
   `mypy autoptz/engine/runtime/ autoptz/config/`, pytest and selftest where
   dependencies are available. Clearly state which checks were not run.
9. Use GitHub Actions for ARM64/macOS CI; physical NDI/PTZ and ANE placement
   must be verified on a real Mac before a production release.

## Incremental TODO rule

Every PR should close a small, testable roadmap item. Do not bundle an
unverified full native rewrite, model replacement and PTZ controller change in
one PR. Mark TODO items completed only when their acceptance conditions are
verified, and keep pending hardware validation explicitly checked as pending.

## Safety and licensing

Respect AGPL-3.0 and third-party model licensing. Do not embed unlicensed
recognition weights, user footage or biometric templates in the repository.
