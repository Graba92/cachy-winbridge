"""
core/migrator.py — Windows Savegame & AppData Entdecker & Migrator.
Findet alte Spielstände, Konfigurationen und Dokumente auf gemounteten Windows-Partitionen.
"""

from __future__ import annotations
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class DiscoveredSavegame:
    game_title: str
    source_path: str
    size_mb: float
    user_name: str
    category: str

class WindowsMigrator:
    """Sucht nach Windows-Benutzerprofilen und Spielständen."""

    SEARCH_ROOTS = [
        Path("/mnt"),
        Path("/run/media"),
        Path("/media")
    ]

    COMMON_SAVE_PATHS = [
        ("Saved Games", "Direkte Spielstände"),
        ("Documents/My Games", "My Games Dokumente"),
        ("AppData/Local", "Lokale AppData"),
        ("AppData/Roaming", "Roaming AppData")
    ]

    @classmethod
    def find_windows_users(cls, custom_root: Optional[str] = None) -> List[Path]:
        """Sucht nach 'Users'-Verzeichnissen auf Windows-Laufwerken."""
        roots = [Path(custom_root)] if custom_root else cls.SEARCH_ROOTS
        users_found: List[Path] = []

        for r in roots:
            if not r.exists():
                continue
            for entry in r.glob("**/Users/*"):
                if entry.is_dir() and entry.name not in ["Public", "Default", "Default User", "All Users"]:
                    # Prüfen ob typische Windows-Ordner vorliegen
                    if (entry / "AppData").exists() or (entry / "Documents").exists() or (entry / "Saved Games").exists():
                        users_found.append(entry)

        return users_found

    @classmethod
    def scan_savegames(cls, custom_root: Optional[str] = None) -> List[DiscoveredSavegame]:
        """Sucht nach typischen Savegames in den gefundenen Profilen."""
        profiles = cls.find_windows_users(custom_root)
        saves: List[DiscoveredSavegame] = []

        for prof in profiles:
            uname = prof.name
            for sub, cat in cls.COMMON_SAVE_PATHS:
                target_dir = prof / sub
                if not target_dir.exists():
                    continue

                try:
                    for item in target_dir.iterdir():
                        if item.is_dir():
                            # Ordnergröße ermitteln
                            total_bytes = 0
                            try:
                                for f in item.rglob("*"):
                                    if f.is_file():
                                        total_bytes += f.stat().st_size
                            except Exception:
                                pass

                            size_mb = round(total_bytes / (1024 * 1024), 2)
                            if size_mb > 0.01:
                                saves.append(DiscoveredSavegame(
                                    game_title=item.name,
                                    source_path=str(item),
                                    size_mb=size_mb,
                                    user_name=uname,
                                    category=cat
                                ))
                except Exception:
                    continue

        return saves

    @classmethod
    def copy_savegame(cls, source_path: str, target_dir: str) -> bool:
        src = Path(source_path)
        dest = Path(target_dir) / src.name
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            return True
        except Exception:
            return False
