import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "agy-cli" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import agy_image  # noqa: E402

# Stand-in for the real `agy`: records how it was called, writes images into the brain dir the way the
# image-generator subagent does, and prints agy's JSON result line. Behaviour is steered by FAKE_AGY_* env vars.
FAKE_AGY = r'''#!{python}
import json, os, sys, uuid
from pathlib import Path
from PIL import Image

if os.environ.get("FAKE_AGY_FAIL"):
    print('AGY_ERROR: {"status": "RESOURCE_EXHAUSTED", "retryable": false}', file=sys.stderr)
    sys.exit(3)
Path(os.environ["FAKE_AGY_LOG"]).write_text(json.dumps(
    {"argv": sys.argv[1:], "cwd": os.getcwd(), "files": sorted(os.listdir("."))}))

conv = str(uuid.uuid4())
conv_dir = Path(os.environ["AGY_BRAIN_DIR"]) / conv
conv_dir.mkdir(parents=True)
images = []
for i in range(int(os.environ.get("FAKE_AGY_COUNT", "1"))):
    p = conv_dir / f"img_{i}.jpg"
    Image.new("RGB", (64, 48), (200, 30 * i, 40)).save(p)
    os.utime(p, (1000 + i, 1000 + i))
    images.append(str(p))

mode = os.environ.get("FAKE_AGY_REPORT", "yes")
if mode == "no":
    images = []
elif mode == "outside":
    stray = Path.cwd() / "stray.jpg"
    Image.new("RGB", (8, 8)).save(stray)
    images = [str(stray)]
print("some log line")
print(json.dumps({"conversation_id": conv, "status": "SUCCESS", "response": "done",
                  "structured_output": {"images": images}}))
'''


@pytest.fixture
def fake_agy(tmp_path, monkeypatch):
    exe = tmp_path / "agy"
    exe.write_text(FAKE_AGY.replace("{python}", sys.executable))
    exe.chmod(0o755)
    brain = tmp_path / "brain"
    brain.mkdir()
    log = tmp_path / "agy-call.json"
    monkeypatch.setenv("AGY_BIN", str(exe))
    monkeypatch.setenv("AGY_BRAIN_DIR", str(brain))
    monkeypatch.setenv("FAKE_AGY_LOG", str(log))
    monkeypatch.setattr(agy_image, "BRAIN_DIR", brain)
    return SimpleNamespace(exe=exe, brain=brain, call=lambda: json.loads(log.read_text()))
