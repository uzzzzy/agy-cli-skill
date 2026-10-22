#!/usr/bin/env python3
"""Install the agy-cli skill for Claude Code (manual alternative to the plugin marketplace).

  python3 install.py              copy skills/agy-cli to ~/.claude/skills/agy-cli
  python3 install.py --link       symlink instead, so edits in this repo take effect immediately
  python3 install.py --force      replace an existing installed copy
  python3 install.py --no-setup   skip pre-installing numpy + Pillow (it also happens on first use)

On Windows run it with `py install.py`. The target folder can be changed with CLAUDE_SKILLS_DIR
(default ~/.claude/skills).
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--link", action="store_true", help="symlink the skill instead of copying it")
    ap.add_argument("--force", action="store_true", help="replace an existing installed copy")
    ap.add_argument("--no-setup", action="store_true", help="don't pre-install numpy + Pillow")
    args = ap.parse_args()

    src = Path(__file__).resolve().parent / "skills" / "agy-cli"
    dest = Path(os.environ.get("CLAUDE_SKILLS_DIR", "~/.claude/skills")).expanduser() / "agy-cli"

    if dest.is_symlink():
        dest.unlink()
    elif dest.exists():
        if not args.force:
            sys.exit(f"{dest} already exists; re-run with --force to replace it")
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    linked = False
    if args.link:
        try:
            dest.symlink_to(src, target_is_directory=True)
            linked = True
        except OSError as e:  # Windows without Developer Mode or admin rights
            print(f"warning: cannot create a symlink ({e}); copying instead", file=sys.stderr)
    if not linked:
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"installed: {dest}{' -> ' + str(src) if linked else ''}")

    if not shutil.which("agy") and not (Path.home() / ".local" / "bin" / "agy").exists():
        print("warning: agy not found; install the Antigravity CLI and sign in before using the skill",
              file=sys.stderr)
    if not args.no_setup:
        subprocess.run([sys.executable, str(dest / "scripts" / "agy_image.py"), "setup"], check=True)


if __name__ == "__main__":
    main()
