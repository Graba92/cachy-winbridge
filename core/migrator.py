"""
core/migrator.py — Windows Savegame & AppData Entdecker & Migrator.
Findet alte Spielstände, Konfigurationen und Dokumente auf gemounteten Windows-Partitionen.
"""

from __future__ import annotations
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

@dataclass
class SteamAppInfo:
    appid: int
    name: str
    install_dir: str
    library_path: Path
    compatdata_user_dir: Optional[Path] = None

@dataclass
class DiscoveredSavegame:
    game_title: str
    source_path: str
    size_mb: float
    user_name: str
    category: str
    matched_appid: Optional[int] = None
    matched_app_name: Optional[str] = None
    proton_target_dir: Optional[str] = None
    is_proton_ready: bool = False

class SteamProtonManager:
    """Verwaltet Steam-Bibliotheken, AppIDs und Proton Compatdata-Prefixe."""

    KNOWN_GAME_APPIDS: Dict[str, int] = {
        "cyberpunk 2077": 1091500,
        "elden ring": 1245620,
        "baldurs gate 3": 1086940,
        "baldur's gate 3": 1086940,
        "the witcher 3": 292030,
        "witcher 3": 292030,
        "skyrim special edition": 489830,
        "skyrim": 489830,
        "fallout 4": 377160,
        "starfield": 1716740,
        "red dead redemption 2": 1174180,
        "hogwarts legacy": 990080,
        "dark souls iii": 374320,
        "dark souls 3": 374320,
        "dark souls remastered": 570940,
        "sekiro": 814380,
        "palworld": 1623730,
        "helldivers 2": 553850,
        "black myth: wukong": 2358720,
        "black myth wukong": 2358720,
        "god of war": 1593500,
        "monster hunter: world": 582010,
        "monster hunter world": 582010,
        "armored core vi": 1887720,
        "lies of p": 1627720,
        "ghost of tsushima": 2215430,
        "horizon zero dawn": 1151640,
        "stardew valley": 413150,
        "gta v": 271590,
        "grand theft auto v": 271590,
    }

    @classmethod
    def find_steam_libraries(cls) -> List[Path]:
        """Ermittelt alle lokalen Steam-Bibliotheken (Native, Flatpak, Sekundärplatten)."""
        candidates = [
            Path.home() / ".local/share/Steam",
            Path.home() / ".steam/root",
            Path.home() / ".steam/steam",
            Path.home() / ".var/app/com.valvesoftware.Steam/.local/share/Steam"
        ]
        libraries: List[Path] = []
        for cand in candidates:
            if cand.exists() and cand.is_dir() and cand not in libraries:
                libraries.append(cand.resolve())

        # libraryfolders.vdf parsen, um externe SSDs/HDDs zu finden
        for lib in list(libraries):
            vdf = lib / "steamapps" / "libraryfolders.vdf"
            if vdf.exists():
                try:
                    content = vdf.read_text(encoding="utf-8", errors="ignore")
                    matches = re.findall(r'"path"\s+"([^"]+)"', content)
                    for m in matches:
                        p = Path(m).resolve()
                        if p.exists() and p not in libraries:
                            libraries.append(p)
                except Exception:
                    pass

        return libraries

    @classmethod
    def get_installed_apps(cls) -> Dict[int, SteamAppInfo]:
        """Scannt alle appmanifest_*.acf Dateien nach installierten Spielen."""
        apps: Dict[int, SteamAppInfo] = {}
        for lib in cls.find_steam_libraries():
            steamapps = lib / "steamapps"
            if not steamapps.exists():
                continue

            for manifest in steamapps.glob("appmanifest_*.acf"):
                try:
                    txt = manifest.read_text(encoding="utf-8", errors="ignore")
                    appid_match = re.search(r'"appid"\s+"(\d+)"', txt)
                    name_match = re.search(r'"name"\s+"([^"]+)"', txt)
                    installdir_match = re.search(r'"installdir"\s+"([^"]+)"', txt)

                    if appid_match and name_match:
                        appid = int(appid_match.group(1))
                        name = name_match.group(1)
                        installdir = installdir_match.group(1) if installdir_match else ""

                        # Prüfen ob compatdata-Ordner existiert
                        compat_user = steamapps / "compatdata" / str(appid) / "pfx" / "drive_c" / "users" / "steamuser"
                        user_dir = compat_user if compat_user.exists() else None

                        apps[appid] = SteamAppInfo(
                            appid=appid,
                            name=name,
                            install_dir=installdir,
                            library_path=lib,
                            compatdata_user_dir=user_dir
                        )
                except Exception:
                    continue
        return apps

    @classmethod
    def match_savegame_to_steam(cls, title: str, installed: Dict[int, SteamAppInfo]) -> Tuple[Optional[int], Optional[str]]:
        """Findet die passende Steam-AppID über installierte Spiele oder die Referenz-Datenbank."""
        norm_title = re.sub(r'[^a-zA-Z0-9]', '', title).lower()

        # 1. Direkter Abgleich mit installierten Steam-Manifesten
        for appid, info in installed.items():
            norm_name = re.sub(r'[^a-zA-Z0-9]', '', info.name).lower()
            if norm_title and (norm_title in norm_name or norm_name in norm_title):
                return appid, info.name

        # 2. Abgleich mit Referenz-Datenbank bekannter Proton-Hits
        for known_name, appid in cls.KNOWN_GAME_APPIDS.items():
            norm_known = re.sub(r'[^a-zA-Z0-9]', '', known_name).lower()
            if norm_title and (norm_title in norm_known or norm_known in norm_title):
                return appid, known_name.title()

        return None, None

    @classmethod
    def resolve_proton_target(cls, save_category: str, game_title: str, appid: int, installed: Dict[int, SteamAppInfo]) -> Tuple[Optional[Path], bool]:
        """Berechnet den exakten Zielpfad im Proton-Prefix drive_c/users/steamuser/..."""
        prefix_user_dir: Optional[Path] = None

        if appid in installed and installed[appid].compatdata_user_dir:
            prefix_user_dir = installed[appid].compatdata_user_dir
        else:
            # Fallback: In allen Bibliotheken nach compatdata/<appid> suchen
            for lib in cls.find_steam_libraries():
                cand = lib / "steamapps" / "compatdata" / str(appid) / "pfx" / "drive_c" / "users" / "steamuser"
                if cand.exists():
                    prefix_user_dir = cand
                    break

        if not prefix_user_dir:
            return None, False

        # Unterverzeichnis gemäß Kategorie
        if save_category == "Direkte Spielstände":
            target = prefix_user_dir / "Saved Games" / game_title
        elif save_category == "My Games Dokumente":
            target = prefix_user_dir / "Documents" / "My Games" / game_title
        elif save_category == "Lokale AppData":
            target = prefix_user_dir / "AppData" / "Local" / game_title
        elif save_category == "Roaming AppData":
            target = prefix_user_dir / "AppData" / "Roaming" / game_title
        else:
            target = prefix_user_dir / "Documents" / game_title

        return target, True


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
                    if (entry / "AppData").exists() or (entry / "Documents").exists() or (entry / "Saved Games").exists():
                        users_found.append(entry)

        return users_found

    @classmethod
    def scan_savegames(cls, custom_root: Optional[str] = None) -> List[DiscoveredSavegame]:
        """Sucht nach Savegames und verknüpft sie direkt mit Steam Proton Compatdata-Prefixen."""
        profiles = cls.find_windows_users(custom_root)
        installed_apps = SteamProtonManager.get_installed_apps()
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
                            total_bytes = 0
                            try:
                                for f in item.rglob("*"):
                                    if f.is_file():
                                        total_bytes += f.stat().st_size
                            except Exception:
                                pass

                            size_mb = round(total_bytes / (1024 * 1024), 2)
                            if size_mb > 0.01:
                                appid, matched_name = SteamProtonManager.match_savegame_to_steam(item.name, installed_apps)
                                proton_path_str = None
                                is_ready = False

                                if appid:
                                    target_p, is_ready = SteamProtonManager.resolve_proton_target(cat, item.name, appid, installed_apps)
                                    proton_path_str = str(target_p) if target_p else f"compatdata/{appid}/... (Prefix noch nicht gestartet)"

                                saves.append(DiscoveredSavegame(
                                    game_title=item.name,
                                    source_path=str(item),
                                    size_mb=size_mb,
                                    user_name=uname,
                                    category=cat,
                                    matched_appid=appid,
                                    matched_app_name=matched_name,
                                    proton_target_dir=proton_path_str,
                                    is_proton_ready=is_ready
                                ))
                except Exception:
                    continue

        return saves

    @classmethod
    def migrate_savegame_to_proton(cls, save: DiscoveredSavegame) -> Tuple[bool, str]:
        """Kopiert Spielstand direkt in den isolierten Proton compatdata Prefix mit Backup."""
        if not save.proton_target_dir or not save.is_proton_ready:
            return False, f"Kein initialisierter Proton-Prefix für AppID {save.matched_appid} gefunden. Spiel einmalig in Steam starten!"

        src = Path(save.source_path)
        dest = Path(save.proton_target_dir)

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                # Sicherheitsbackup vor dem Überschreiben
                bak = dest.with_name(f"{dest.name}.backup.{int(Path('/tmp').stat().st_mtime)}")
                shutil.copytree(dest, bak)

            shutil.copytree(src, dest, dirs_exist_ok=True)
            return True, f"✔ Spielstand für '{save.game_title}' erfolgreich nach '{dest}' migriert."
        except Exception as e:
            return False, f"Fehler bei Migration: {e}"

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
