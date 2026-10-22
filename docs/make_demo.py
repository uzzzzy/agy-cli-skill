"""Rebuild docs/images/demo.gif: each transparent cut-out in docs/images/cutouts/ over a moving background.

    python docs/make_demo.py        (needs Pillow)
"""

from pathlib import Path

from PIL import Image, ImageDraw

IMAGES = Path(__file__).resolve().parent / "images"
CUTOUTS = ["wine-glass.png", "perfume.png", "scarf.png"]
PALETTES = [((30, 90, 200), (250, 190, 40)), ((24, 24, 28), (90, 220, 160)), ((240, 120, 160), (40, 60, 120))]
W, H = 640, 360
STRIPE = 36       # stripe width; the pattern repeats every 2 * STRIPE px, so the scroll loops seamlessly
FRAMES = 18       # per cut-out
FRAME_MS = 70


def background(offset, colors):
    base, stripe = colors
    bg = Image.new("RGB", (W, H), base)
    draw = ImageDraw.Draw(bg)
    for x in range(-H - 2 * STRIPE, W + 2 * STRIPE, 2 * STRIPE):
        x += offset
        draw.polygon([(x, 0), (x + STRIPE, 0), (x + STRIPE + H, H), (x + H, H)], fill=stripe)
    return bg


def fit(im):
    scale = min((W - 40) / im.width, (H - 24) / im.height)
    return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)


def main():
    frames = []
    for name, colors in zip(CUTOUTS, PALETTES):
        cut = fit(Image.open(IMAGES / "cutouts" / name).convert("RGBA"))
        pos = ((W - cut.width) // 2, (H - cut.height) // 2)
        for i in range(FRAMES):
            frame = background(i * 2 * STRIPE // FRAMES, colors).convert("RGBA")
            frame.alpha_composite(cut, pos)
            frames.append(frame.convert("RGB").quantize(colors=160, dither=Image.Dither.FLOYDSTEINBERG))
    out = IMAGES / "demo.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=FRAME_MS, loop=0, optimize=True)
    print(f"{out} ({out.stat().st_size / 1e6:.1f} MB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
