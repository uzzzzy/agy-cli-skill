# Changelog

## 0.2.0 — 2026-10-22

Renamed the repository from `agy-cli-skill` to **agy-atelier**. GitHub redirects the old URL. The marketplace
is now `agy-atelier`, so install with `/plugin install agy-cli@agy-atelier`.

### Hardening
- agy runs with its terminal sandbox by default (`--no-sandbox` / `AGY_IMAGE_SANDBOX=0` to opt out). Where the
  system can't provide the sandbox, the run is retried without it, with a warning.
- Hard timeout: a run still going 60 s after `--timeout` is stopped together with agy's helper processes.
- The user's prompt is fenced in the instructions sent to agy, and agy is told to ignore any instructions inside it.
- `agy --version` is checked once per run; versions other than 1.3.x/1.4.x get a warning (`AGY_SKIP_VERSION_CHECK=1`).

### Zero setup
- numpy + Pillow install themselves into a private venv (`~/.local/share/agy-atelier/venv`) the first time a
  command needs them (`AGY_IMAGE_NO_AUTO_SETUP=1` to disable).
- PEP 723 inline dependency metadata, for script runners such as `uv run`.
- An interpreter that already has numpy + Pillow is used as is.

### Windows
- Cross-platform installer `install.py` (`py install.py` on Windows); `install.sh` now calls it.
- Windows-aware venv paths, re-exec and process-tree termination; UTF-8 decoding of agy output.
- CI runs the tests on Ubuntu (Python 3.9 and 3.12), macOS and Windows.

### UX
- `--dry-run` prints the planned agy commands, prompts and a time estimate without running anything.
- The result JSON includes `agy_version`, `agy_runs` (seconds, sandbox, token usage per run) and `total_seconds`.
- Before 3 or more images, the remaining agy quota is logged, with a warning when a limit is almost used up.
- `--out` values like `out.v2/` or `out\` are treated as folders.

### Docs
- New README with an animated demo, a third example (perfume bottle) and badges; `docs/make_demo.py` rebuilds the GIF.

## 0.1.0 — 2026-10-22

First release.
- `agy-cli` skill: image generation and editing through agy's image-generator subagent.
- Transparent and semi-transparent PNGs via two-plate difference matting.
- Guidance for headless agy prompts.
- Claude Code plugin and marketplace manifests, `install.sh`, offline tests and CI.
