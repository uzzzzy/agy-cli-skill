import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

import agy_image

SCRIPT = Path(agy_image.__file__).resolve()


def run(prompt, out, **kw):
    opts = dict(ratio="1:1", refs=[], count=1, model="test-model", timeout="1m")
    opts.update(kw)
    return agy_image.generate(prompt, out=str(out), **opts)


def prompt_of(call):
    argv = call["argv"]
    return argv[argv.index("-p") + 1]


def test_generate_copies_and_converts_to_requested_format(fake_agy, tmp_path):
    out = tmp_path / "assets" / "hero.png"
    paths, data = run("a red fox in a pine forest", out, ratio="16:9")

    assert paths == [out.resolve()]
    with Image.open(out) as im:
        assert im.format == "PNG"
        assert im.size == (64, 48)
    call = fake_agy.call()
    argv = call["argv"]
    assert argv[argv.index("--model") + 1] == "test-model"
    assert argv[argv.index("--output-format") + 1] == "json"
    assert "--json-schema" in argv
    assert "a red fox in a pine forest" in prompt_of(call)
    assert "Aspect ratio: 16:9" in prompt_of(call)
    assert not Path(call["cwd"]).exists(), "the temporary agy workspace is cleaned up"


def test_variations_into_directory(fake_agy, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_AGY_COUNT", "2")
    paths, _ = run("Paper plane icon!", f"{tmp_path / 'icons'}{os.sep}", count=2)

    assert len(paths) == 2
    assert all(p.parent == (tmp_path / "icons").resolve() for p in paths)
    assert all(p.name.startswith("paper-plane-icon-") for p in paths)
    assert [p.name[-6:] for p in paths] == ["-1.jpg", "-2.jpg"]
    assert "exactly 2 images" in prompt_of(fake_agy.call())


def test_references_are_copied_into_the_agy_workspace(fake_agy, tmp_path):
    ref = tmp_path / "photo.PNG"
    Image.new("RGB", (10, 10), "blue").save(ref)
    run("make the mug matte black", tmp_path / "edit.jpg", refs=[str(ref)])

    call = fake_agy.call()
    assert call["files"] == ["ref1.png"]
    assert str(Path(call["cwd"]) / "ref1.png") in prompt_of(call)


def test_reference_limits(fake_agy, tmp_path):
    with pytest.raises(SystemExit):
        run("x", tmp_path / "a.jpg", refs=[str(tmp_path / "missing.jpg")])
    refs = []
    for i in range(4):
        p = tmp_path / f"r{i}.jpg"
        Image.new("RGB", (4, 4)).save(p)
        refs.append(str(p))
    with pytest.raises(SystemExit):
        run("x", tmp_path / "a.jpg", refs=refs)


def test_falls_back_to_artifact_dir_when_nothing_reported(fake_agy, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_AGY_REPORT", "no")
    paths, _ = run("fox", tmp_path / "fox.jpg")
    with Image.open(paths[0]) as im:
        assert im.size == (64, 48)


def test_ignores_reported_paths_outside_the_brain_dir(fake_agy, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_AGY_REPORT", "outside")
    paths, _ = run("fox", tmp_path / "fox.jpg")
    with Image.open(paths[0]) as im:
        assert im.size == (64, 48), "the stray 8x8 file in the workspace must not be picked"


def test_agy_failure_is_reported(fake_agy, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_AGY_FAIL", "1")
    with pytest.raises(SystemExit):
        run("fox", tmp_path / "fox.jpg")
    assert "AGY_ERROR" in capsys.readouterr().err


def test_cli_prints_json(fake_agy, tmp_path):
    env = {**os.environ, "AGY_IMAGE_VENV": str(tmp_path / "no-venv")}
    proc = subprocess.run([sys.executable, str(SCRIPT), "generate", "a fox", "-o", str(tmp_path / "fox.png"),
                           "--ratio", "3:2"], capture_output=True, text=True, env=env, check=True)
    result = json.loads(proc.stdout)
    assert result["images"] == [str((tmp_path / "fox.png").resolve())]
    assert "agy finished" in proc.stderr


def test_parse_json_tail_skips_noise():
    out = 'starting\n{"broken": \n{"conversation_id": "abc", "status": "SUCCESS"}\n'
    assert agy_image.parse_json_tail(out)["conversation_id"] == "abc"
    assert agy_image.parse_json_tail("no json here") is None


def test_slugify():
    assert agy_image.slugify("A Clear Crystal Wine-Glass!!") == "a-clear-crystal-wine-glass"
    assert agy_image.slugify("???") == "image"
    assert len(agy_image.slugify("x" * 100)) == 40
