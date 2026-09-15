"""
core/wine_runner.py — Isolierter Micro-Prefix Launcher für .exe & .msi Dateien.
Ermöglicht Windows-Umsteigern das direkte Ausführen von Windows-Programmen ohne Systemmüll.
"""

from __future__ import annotations
import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple

BOTTLES_BASE_DIR = Path.home() / ".local" / "share" / "cachy-winbridge" / "prefixes"

class WineRunner:
    """Führt Windows-Programme in sauberen, isolierten Wine-Prefixen aus."""

    @classmethod
    def is_wine_available(cls) -> bool:
        return bool(shutil.which("wine"))

    @classmethod
    def run_executable(cls, exe_path: str, isolated: bool = True) -> Tuple[bool, str]:
        if not cls.is_wine_available():
            return False, "Wine ist nicht installiert. Bitte installiere es mit: 'sudo pacman -S wine wine-mono wine-gecko'"

        target = Path(exe_path).resolve()
        if not target.exists():
            return False, f"Datei existiert nicht: {exe_path}"

        suffix = target.suffix.lower()
        if suffix not in [".exe", ".msi"]:
            return False, f"Nicht unterstütztes Format: {suffix} (nur .exe und .msi)"

        if isolated:
            # Einzigartiger Prefix basierend auf dem Dateinamen
            app_id = hashlib.md5(str(target).encode()).hexdigest()[:8]
            prefix_dir = BOTTLES_BASE_DIR / f"app_{target.stem}_{app_id}"
        else:
            prefix_dir = BOTTLES_BASE_DIR / "default_sandbox"

        prefix_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix_dir)
        env["WINEDEBUG"] = "-all"
        env["DXVK_HUD"] = "compiler"

        cmd = ["wine"]
        if suffix == ".msi":
            cmd = ["wine", "msiexec", "/i", str(target)]
        else:
            cmd = ["wine", str(target)]

        try:
            subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True, f"Programm '{target.name}' im isolierten Prefix gestartet:\n{prefix_dir}"
        except Exception as e:
            return False, f"Fehler beim Start: {e}"
