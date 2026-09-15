"""
core/drives.py — Drive Scanner, NTFS/Btrfs Automount Wizard & /etc/fstab Generator.
Löst das #1 Problem von Windows-Umsteigern: Nicht gemountete oder schreibgeschützte Gaming-Platten.
"""

from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FSTAB_PATH = Path("/etc/fstab")

@dataclass
class PartitionInfo:
    name: str
    device_path: str
    fstype: str
    size_human: str
    label: str
    uuid: str
    mountpoint: Optional[str]
    is_mounted: bool
    is_in_fstab: bool
    is_gaming_ready: bool
    recommended_mount_dir: str
    recommended_fstab_line: str

class DriveManager:
    """Verwaltet Festplatten, Partitionen und sicheres Automounting."""

    @classmethod
    def get_fstab_uuids(cls) -> Dict[str, str]:
        """Liest alle in /etc/fstab registrierten UUIDs und deren Zeilen ein."""
        registered = {}
        if not FSTAB_PATH.exists():
            return registered
        try:
            with open(FSTAB_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    parts = stripped.split()
                    if parts and parts[0].startswith("UUID="):
                        uuid = parts[0].split("=", 1)[1].strip()
                        registered[uuid] = stripped
        except Exception:
            pass
        return registered

    @classmethod
    def scan_partitions(cls) -> List[PartitionInfo]:
        """Scannt alle Blockgeräte und filtert nutzbare Daten- & Gaming-Partitionen."""
        fstab_entries = cls.get_fstab_uuids()
        partitions: List[PartitionInfo] = []

        try:
            res = subprocess.run(
                ["lsblk", "-J", "-b", "-o", "NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL,UUID,TYPE"],
                capture_output=True,
                text=True,
                timeout=5
            )
            data = json.loads(res.stdout)
        except Exception:
            return partitions

        def parse_device(dev: dict):
            children = dev.get("children", [])
            for child in children:
                parse_device(child)

            dev_type = dev.get("type", "")
            fstype = dev.get("fstype") or ""
            uuid = dev.get("uuid") or ""
            size_bytes = int(dev.get("size") or 0)

            # Nur echte Partitionen mit Dateisystem und UUID
            if dev_type == "part" and fstype and uuid and fstype != "swap":
                name = dev.get("name", "")
                label = dev.get("label") or ""
                mountpoint = dev.get("mountpoint")
                is_mounted = bool(mountpoint)
                is_in_fstab = uuid in fstab_entries

                # Lesbare Größe berechnen
                gb = size_bytes / (1024 ** 3)
                size_str = f"{gb:.1f} GB" if gb < 1024 else f"{gb/1024:.2f} TB"

                # Empfohlenen Mountpoint bestimmen (z.B. /mnt/Games_SSD oder /mnt/sda1)
                safe_label = re.sub(r'[^a-zA-Z0-9_-]', '_', label).strip('_')
                folder_name = safe_label if safe_label else name
                recommended_dir = f"/mnt/{folder_name}"

                # Optimierte Fstab-Optionen für Gaming & Proton
                # NTFS benötigt zwingend uid/gid=1000 und windows_names, damit Proton nicht crasht
                uid = os.getuid()
                gid = os.getgid()
                if fstype in ["ntfs", "ntfs3"]:
                    opt = f"uid={uid},gid={gid},windows_names,nofail,x-gvfs-show,auto"
                    fs_driver = "ntfs3"
                    gaming_ready = True
                elif fstype == "btrfs":
                    opt = "defaults,noatime,compress=zstd,nofail,x-gvfs-show,auto"
                    fs_driver = "btrfs"
                    gaming_ready = True
                elif fstype == "ext4":
                    opt = "defaults,noatime,nofail,x-gvfs-show,auto"
                    fs_driver = "ext4"
                    gaming_ready = True
                else:
                    opt = "defaults,nofail,x-gvfs-show,auto"
                    fs_driver = fstype
                    gaming_ready = False

                fstab_line = f"UUID={uuid}  {recommended_dir}  {fs_driver}  {opt}  0  0"

                partitions.append(PartitionInfo(
                    name=name,
                    device_path=f"/dev/{name}",
                    fstype=fstype,
                    size_human=size_str,
                    label=label if label else f"[Kein Label] ({name})",
                    uuid=uuid,
                    mountpoint=mountpoint,
                    is_mounted=is_mounted,
                    is_in_fstab=is_in_fstab,
                    is_gaming_ready=gaming_ready,
                    recommended_mount_dir=recommended_dir,
                    recommended_fstab_line=fstab_line
                ))

        for root_dev in data.get("blockdevices", []):
            parse_device(root_dev)

        return partitions

    @classmethod
    def check_ntfs_issue_in_error(cls, err: str) -> Optional[str]:
        """Erkennt Windows Fast-Startup / Hibernation / Dirty-Bit Muster in Fehlermeldungen."""
        lower_err = err.lower()
        if any(keyword in lower_err for keyword in ["hibernat", "unclean", "dirty", "metadata kept in windows cache", "refused to mount"]):
            return (
                "⚠️ Windows Fast-Startup / Ruhezustand ist aktiv! Das NTFS-Dateisystem ist gesperrt.\n"
                "👉 Lösung: Einmal Windows starten und mit gedrückter Shift-Taste auf 'Herunterfahren' klicken,\n"
                "   oder in Windows als Administrator ausführen: 'powercfg /h off'."
            )
        if "notauthorized" in lower_err:
            return "Hinweis: Einhängen dieser internen Festplatte erfordert Systemrechte (Polkit/Sudo oder /etc/fstab)."
        return None

    @classmethod
    def mount_partition_user(cls, device_path: str) -> Tuple[bool, str]:
        """Mounted eine Partition unprivilegiert via udisksctl mit Fast-Startup Diagnose."""
        if not shutil.which("udisksctl"):
            return False, "udisksctl ist nicht installiert."
        try:
            res = subprocess.run(
                ["udisksctl", "mount", "-b", device_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0:
                return True, res.stdout.strip()
            
            raw_err = res.stderr.strip()
            special_advice = cls.check_ntfs_issue_in_error(raw_err)
            if special_advice:
                return False, f"{raw_err}\n{special_advice}"
            return False, raw_err
        except Exception as e:
            return False, str(e)

    @classmethod
    def generate_fstab_backup(cls) -> Path:
        """Erstellt ein sicheres Backup der aktuellen /etc/fstab mit Zeitstempel."""
        ts = int(time.time())
        bak_dir = Path.home() / ".config" / "cachy-winbridge" / "backups"
        bak_dir.mkdir(parents=True, exist_ok=True)
        bak_path = bak_dir / f"fstab.bak.{ts}"
        if FSTAB_PATH.exists():
            shutil.copy2(FSTAB_PATH, bak_path)
        return bak_path

    @classmethod
    def verify_fstab_syntax(cls, tab_file: Optional[Path] = None) -> Tuple[bool, str]:
        """Führt einen Pre-Flight Syntax-Check via findmnt --verify durch."""
        target = tab_file or FSTAB_PATH
        if not target.exists():
            return False, f"Datei {target} existiert nicht."

        if not shutil.which("findmnt"):
            return True, "findmnt nicht gefunden (Syntax-Prüfung übersprungen)."

        try:
            res = subprocess.run(
                ["findmnt", "--verify", "--tab-file", str(target)],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = (res.stdout.strip() + "\n" + res.stderr.strip()).strip()
            if res.returncode == 0:
                return True, output or "✔ Keine Fehler oder Syntax-Konflikte erkannt."
            return False, output or "Unbekannter Syntax-Fehler in fstab-Tabelle."
        except Exception as e:
            return False, f"Fehler bei findmnt Überprüfung: {e}"

    @classmethod
    def validate_fstab_addition(cls, new_entries: List[str]) -> Tuple[bool, str]:
        """Erstellt eine Test-fstab in /tmp und validiert sie vorab risikofrei."""
        current_content = FSTAB_PATH.read_text(encoding="utf-8") if FSTAB_PATH.exists() else ""
        test_file = Path(f"/tmp/fstab.verify.{os.getpid()}")
        try:
            combined = current_content + "\n# --- Cachy-WinBridge Safe Addition ---\n" + "\n".join(new_entries) + "\n"
            test_file.write_text(combined, encoding="utf-8")
            ok, msg = cls.verify_fstab_syntax(tab_file=test_file)
            return ok, msg
        finally:
            if test_file.exists():
                try:
                    test_file.unlink()
                except Exception:
                    pass
