import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_SRC = ROOT / "skills" / "agy-cli"


def install(tmp_path, *args):
    env = {**os.environ, "CLAUDE_SKILLS_DIR": str(tmp_path / "skills")}
    return subprocess.run([sys.executable, str(ROOT / "install.py"), "--no-setup", *args],
                          capture_output=True, text=True, env=env)


def test_copy_install_refuses_to_overwrite_without_force(tmp_path):
    dest = tmp_path / "skills" / "agy-cli"
    assert install(tmp_path).returncode == 0
    assert (dest / "SKILL.md").is_file()
    assert (dest / "scripts" / "agy_image.py").is_file()
    assert not dest.is_symlink()
    assert not list(dest.rglob("__pycache__"))

    again = install(tmp_path)
    assert again.returncode != 0 and "--force" in again.stderr
    assert install(tmp_path, "--force").returncode == 0


def test_link_install(tmp_path):
    dest = tmp_path / "skills" / "agy-cli"
    assert install(tmp_path, "--link").returncode == 0
    assert (dest / "SKILL.md").is_file()
    if dest.is_symlink():  # Windows without symlink rights falls back to a copy
        assert dest.resolve() == SKILL_SRC.resolve()
        assert install(tmp_path, "--link").returncode == 0, "an existing link is replaced without --force"
