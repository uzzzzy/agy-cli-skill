# agy-cli-skill

A [Claude Code](https://claude.com/claude-code) skill that drives the **Google Antigravity CLI (`agy`)**, so Claude can:

- **Generate images** from text, in 7 aspect ratios, with 1–4 variations per run.
- **Edit or combine images**: pass up to 3 reference images.
- **Make transparent and semi-transparent PNGs** of things that are hard to cut out, like glass, liquids, sheer
  fabric, smoke and veils, with real partial alpha instead of a hard cut-out.
- **Run headless prompts** on Antigravity's models (Gemini, Claude, GPT-OSS) for second opinions or delegated tasks.

You ask in plain language ("make a transparent PNG of a wine glass for the landing page") and Claude runs the
bundled script, checks the result and saves it where your project needs it.

| Clear glass | Sheer chiffon scarf |
|---|---|
| ![Wine glass: white plate, black plate, transparent result, result over stripes](docs/images/wine-glass.jpg) | ![Scarf: white plate, black plate, transparent result, result over stripes](docs/images/scarf.jpg) |

*Each sheet shows the white plate, the black plate, the transparent PNG on a checkerboard, and the same PNG over
stripes; the stripes stay visible through the glass and the fabric.*

## Requirements

- macOS or Linux with Python 3.9+
- The Antigravity CLI (`agy`), installed and signed in (run `agy` once interactively)
- Claude Code

## Install

**As a Claude Code plugin** (recommended):

```
/plugin marketplace add uzzzzy/agy-cli-skill
/plugin install agy-cli@agy-cli-skill
```

Then create the script's Python environment once (numpy + Pillow, stored in `~/.local/share/agy-cli-skill/venv`).
Claude does this on first use when needed, or run it yourself with the script path from the installed plugin:

```bash
python3 <plugin-dir>/skills/agy-cli/scripts/agy_image.py setup
```

**Manually** (copies the skill to `~/.claude/skills/agy-cli` and runs `setup`):

```bash
git clone https://github.com/uzzzzy/agy-cli-skill.git
cd agy-cli-skill
./install.sh            # or ./install.sh --link to symlink while developing
```

Use one method, not both, or Claude will see the skill twice.

## Usage

Just ask Claude, for example:

- "Generate a 16:9 hero image of a cozy workspace for `public/images/hero.png`"
- "Edit `photo.jpg` so the mug is matte black"
- "Give me 3 icon variations of a paper airplane"
- "Make a transparent PNG of a floating sheer pink scarf"
- "Ask Gemini through agy to review this function"

The script can also be used directly:

```bash
IMG=skills/agy-cli/scripts/agy_image.py

python3 $IMG generate "A cozy minimalist workspace, soft morning light" -o out/hero.png --ratio 16:9
python3 $IMG generate "Make the mug matte black, keep everything else" --ref photo.jpg -o out/
python3 $IMG generate "Flat vector app icon of a paper airplane" -n 3 -o out/icons/
python3 $IMG transparent "A clear crystal wine glass half filled with red wine" -o out/wine.png --trim
python3 $IMG transparent "same product" --white product_on_white.jpg -o out/product.png
python3 $IMG matte --white a_white.jpg --black a_black.jpg -o out/a.png
```

Each run prints one JSON object on stdout (paths, plus quality metrics for transparent output). A single agy
image run takes about 40–60 seconds. See [`skills/agy-cli/SKILL.md`](skills/agy-cli/SKILL.md) for every option.

## How transparency works

Image models can't output an alpha channel, so `transparent` makes two **plates** and solves for alpha:

1. Generate the subject on flat pure white.
2. Use that image as a reference and have it edited onto flat pure black, with the subject unchanged.
3. Over a background of level `k`, each pixel is `P = a·C + (1 − a)·k`, so with both plates
   `a = 1 − (P_white − P_black)`, and the colour `C` follows from either plate.

This is classic difference (triangulation) matting. Unlike background removers, it keeps glass, liquid and
thin fabric see-through. The script also auto-aligns small shifts between the plates, checks the result
(background purity, plates that don't match, nothing or everything opaque), regenerates the black plate when a
check fails, and writes `NAME.png`, `NAME.preview.png` (checkerboard) and both plates so you can re-matte
without generating again.

**Limits:** a PNG has a single alpha per pixel, so strongly tinted glass keeps an averaged tint, and the edit
pass can change tiny details. Always look at the preview.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AGY_IMAGE_MODEL` | `gemini-3.8-flash-low` | agy model that orchestrates image runs (`agy models` lists them) |
| `AGY_IMAGE_VENV` | `~/.local/share/agy-cli-skill/venv` | Where `setup` puts numpy + Pillow |
| `AGY_BIN` | `agy` on `PATH`, else `~/.local/bin/agy` | agy executable |
| `AGY_BRAIN_DIR` | `~/.gemini/antigravity-cli/brain` | Where agy stores conversation artifacts |
| `CLAUDE_SKILLS_DIR` | `~/.claude/skills` | Target folder for `install.sh` |

## A note on safety

`agy` is a full agent. If `toolPermission` in `~/.gemini/antigravity-cli/settings.json` is `always-proceed`,
headless runs execute commands and edit files without asking. The image script runs agy in a throwaway temp
folder and tells it not to touch files; the skill instructs Claude to do the same for other agy tasks.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

The tests use a fake `agy`, so they need no network or Antigravity account. CI runs them on every push.

## License

[MIT](LICENSE). Not affiliated with Google or Anthropic. Generated images are subject to the terms of the
Antigravity service you use.
