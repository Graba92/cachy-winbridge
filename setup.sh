#!/usr/bin/env bash
# Setup-Skript für Cachy-WinBridge auf CachyOS / Arch Linux
set -e

echo "🪟 Installiere Abhängigkeiten für Cachy-WinBridge..."

# Systempakete prüfen / installieren
if command -v pacman &> /dev/null; then
    echo "Paketmanager pacman erkannt. Installiere Systemwerkzeuge falls nötig..."
    sudo pacman -S --needed --noconfirm python python-rich python-textual udisks2 ntfs-3g btrfs-progs
fi

echo "✔ Bereit! Starte das Dashboard mit ./run.sh oder 'python app.py tui'"
