import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "agy-cli"


def load(name):
    return json.loads((ROOT / ".claude-plugin" / name).read_text())


def test_plugin_manifest():
    plugin = load("plugin.json")
    assert plugin["name"] == "agy-cli"
    assert re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])
    assert plugin["description"]


def test_marketplace_points_at_this_repo():
    market = load("marketplace.json")
    assert market["name"] == "agy-atelier"
    assert market["owner"]["name"]
    entry = {p["name"]: p for p in market["plugins"]}["agy-cli"]
    assert entry["source"] == "./"
    assert load("plugin.json")["repository"].endswith("/agy-atelier")


def test_skill_frontmatter():
    text = (SKILL_DIR / "SKILL.md").read_text()
    frontmatter = text.split("---")[1]
    name = re.search(r"^name: (.+)$", frontmatter, re.M).group(1).strip()
    description = re.search(r"^description: (.+)$", frontmatter, re.M).group(1).strip()
    assert name == SKILL_DIR.name
    assert 0 < len(description) <= 1024
    assert (SKILL_DIR / "scripts" / "agy_image.py").is_file()
