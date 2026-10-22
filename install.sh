#!/usr/bin/env bash
# Kept for convenience: the installer itself is install.py (macOS, Linux and Windows). See --help.
exec python3 "$(dirname "${BASH_SOURCE[0]}")/install.py" "$@"
