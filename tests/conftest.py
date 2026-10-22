import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "agy-cli" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import agy_image  # noqa: E402

# Stand-in for the real `agy`, run through `python agy.py` (AGY_BIN ending in .py) so it also works on Windows.
# It answers --version and /usage, records each image run in FAKE_AGY_LOG (JSON lines), writes images into the
# brain dir the way the image-generator subagent does, and prints agy's JSON result line.
# Behaviour is steered by FAKE_AGY_* env vars.
FAKE_AGY = r'''
import json, os, sys, time, uuid
from pathlib import Path
from PIL import Image

argv = sys.argv[1:]
if argv == ["--version"]:
    print(os.environ.get("FAKE_AGY_VERSION", "1.4.5"))
    sys.exit(0)
prompt = argv[argv.index("-p") + 1] if "-p" in argv else ""
if prompt == "/usage":
    left = float(os.environ.get("FAKE_AGY_QUOTA", "0.5"))
    buckets = [{"window": w, "remaining_fraction": left, "reset_time": "2026-10-30T00:00:00Z"} for w in ("weekly", "5h")]
    groups = [{"name": "Gemini Models", "buckets": buckets}, {"name": "Claude and GPT models", "buckets": buckets}]
    print(json.dumps({"conversation_id": "", "status": "SUCCESS", "command": {"name": "usage", "data": {"groups": groups}}}))
    sys.exit(0)
if os.environ.get("FAKE_AGY_FAIL"):
    print('AGY_ERROR: {"status": "RESOURCE_EXHAUSTED", "retryable": false}', file=sys.stderr)
    sys.exit(3)
if os.environ.get("FAKE_AGY_SANDBOX_FAIL") and "--sandbox" in argv:
    print("error: the terminal sandbox is not supported on this system", file=sys.stderr)
    sys.exit(1)
time.sleep(float(os.environ.get("FAKE_AGY_SLEEP", "0")))
with open(os.environ["FAKE_AGY_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"argv": argv, "cwd": os.getcwd(), "files": sorted(os.listdir("."))}) + "\n")

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
                  "usage": {"total_tokens": 1234}, "structured_output": {"images": images}}))
'''


@pytest.fixture
def fake_agy(tmp_path, monkeypatch):
    exe = tmp_path / "agy.py"
    exe.write_text(FAKE_AGY, encoding="utf-8")
    brain = tmp_path / "brain"
    brain.mkdir()
    log = tmp_path / "agy-calls.jsonl"
    monkeypatch.setenv("AGY_BIN", str(exe))
    monkeypatch.setenv("AGY_BRAIN_DIR", str(brain))
    monkeypatch.setenv("FAKE_AGY_LOG", str(log))
    monkeypatch.setattr(agy_image, "BRAIN_DIR", brain)
    monkeypatch.setattr(agy_image, "RUNS", [])
    monkeypatch.setattr(agy_image, "_AGY_VERSION", None)

    def calls():
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]

    return SimpleNamespace(exe=exe, brain=brain, calls=calls, call=lambda: calls()[-1])
