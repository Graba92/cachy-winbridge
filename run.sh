#!/usr/bin/env bash
# Quick Launcher für Cachy-WinBridge
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
python3 "$DIR/app.py" "$@"
