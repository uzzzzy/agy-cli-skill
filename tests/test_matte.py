import numpy as np
from PIL import Image

import agy_image

H, W = 256, 320
SQUARE = (0.85, 0.15, 0.10)


def ground_truth():
    yy, xx = np.mgrid[0:H, 0:W]
    color = np.zeros((H, W, 3), np.float32)
    alpha = np.zeros((H, W), np.float32)
    square = (yy > 40) & (yy < 120) & (xx > 40) & (xx < 120)
    color[square], alpha[square] = SQUARE, 1.0
    circle = (yy - 150) ** 2 + (xx - 220) ** 2 < 60 ** 2
    color[circle], alpha[circle] = (0.2, 0.4, 0.9), 0.3
    strip = (yy > 200) & (yy < 235) & (xx > 30) & (xx < 290)
    color[strip], alpha[strip] = (0.9, 0.8, 0.3), ((xx - 30) / 260.0)[strip]
    return color, alpha


def save(arr, path):
    Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).save(path, quality=92)
    return path


def make_plates(tmp_path, shift=(3, -2), swap=True):
    color, alpha = ground_truth()
    a = alpha[..., None]
    white = color * a + (1 - a)
    black = color * a if swap else white
    black = np.roll(black, shift, axis=(0, 1))  # the edit pass nudged the subject
    return save(white, tmp_path / "w.jpg"), save(black, tmp_path / "b.jpg"), alpha


def test_recovers_partial_alpha_and_realigns(tmp_path):
    white, black, truth = make_plates(tmp_path)
    image, metrics, warnings = agy_image.difference_matte(white, black)
    rgba = np.asarray(image, np.float32) / 255

    assert warnings == []
    assert metrics["shift_px"] == [-2, 3]
    assert np.abs(rgba[..., 3] - truth).mean() < 0.01
    # 30 % glass-like circle stays see-through (levels remap: (0.3 - 0.03) / 0.94)
    assert abs(rgba[140:160, 210:230, 3].mean() - 0.287) < 0.03
    assert np.allclose(rgba[70:90, 70:90, :3].mean(axis=(0, 1)), SQUARE, atol=0.05)
    assert 0.2 < metrics["translucent_share"] < 0.9


def test_flags_plates_whose_background_was_not_swapped(tmp_path):
    white, black, _ = make_plates(tmp_path, shift=(0, 0), swap=False)
    _, metrics, warnings = agy_image.difference_matte(white, black)

    assert metrics["bg_black"] > 0.9
    assert "black plate background is not black enough" in warnings
    assert any("almost everything is opaque" in w for w in warnings)


def test_write_matte_trims_and_previews(tmp_path):
    white, black, _ = make_plates(tmp_path)
    result = agy_image.write_matte(white, black, tmp_path / "cut.png", max_shift=8, trim=True, preview=True)

    with Image.open(result["output"]) as im:
        assert im.mode == "RGBA"
        assert im.width < W and im.height < H
    with Image.open(result["preview"]) as prev:
        assert prev.size == tuple(result["size"])
