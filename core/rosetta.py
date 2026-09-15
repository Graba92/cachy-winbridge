"""
core/rosetta.py — Windows-to-Linux Rosetta Stone & Befehls-Übersetzer.
Übersetzt Windows-Befehle, Tastenkürzel und Dateisystem-Konzepte in die Linux/CachyOS-Welt.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class RosettaEntry:
    win_term: str
    linux_equivalent: str
    category: str
    description: str
    example_usage: str

ROSETTA_DICTIONARY: List[RosettaEntry] = [
    # Systemverwaltung & Diagnose
    RosettaEntry(
        win_term="taskmgr (Task-Manager / Strg+Shift+Esc)",
        linux_equivalent="btop / plasma-systemmonitor",
        category="System",
        description="Zeigt laufende Prozesse, CPU-, RAM-, GPU-Auslastung und beendet Hänger.",
        example_usage="btop"
    ),
    RosettaEntry(
        win_term="services.msc (Dienste-Verwaltung)",
        linux_equivalent="systemctl",
        category="System",
        description="Hintergrunddienste verwalten, starten, stoppen und Autostart festlegen.",
        example_usage="systemctl status bluetooth  |  sudo systemctl restart NetworkManager"
    ),
    RosettaEntry(
        win_term="devmgmt.msc (Geräte-Manager)",
        linux_equivalent="lspci -k / lsusb / lshw",
        category="Hardware",
        description="Listet Hardware, Grafikkarten, Audiochips und aktive Kernel-Treiber auf.",
        example_usage="lspci -k | grep -A 3 -E 'VGA|3D'  |  lsusb"
    ),
    RosettaEntry(
        win_term="dxdiag (DirectX Diagnose)",
        linux_equivalent="vulkaninfo --summary / fastfetch",
        category="Gaming & Grafik",
        description="Zeigt Vulkan-, OpenGL-, GPU- und Treiberspezifikationen an.",
        example_usage="vulkaninfo --summary  |  fastfetch"
    ),
    RosettaEntry(
        win_term="eventvwr.msc (Ereignisanzeige)",
        linux_equivalent="journalctl -xe / dmesg",
        category="Diagnose",
        description="Zentrales System- und Kernel-Logbuch für Fehler und Boot-Meldungen.",
        example_usage="journalctl -xe -p err..alert  |  dmesg -T --level=err"
    ),
    RosettaEntry(
        win_term="sfc /scannow (Systemdatei-Prüfung)",
        linux_equivalent="pacman -Qk",
        category="Wartung",
        description="Prüft alle installierten Pakete auf veränderte oder fehlende Binärdateien.",
        example_usage="pacman -Qk  |  sudo pacman -S --needed $(pacman -Qknq)"
    ),
    RosettaEntry(
        win_term="winget / choco / Systemsteuerung (Programme)",
        linux_equivalent="pacman / yay / flatpak",
        category="Software",
        description="Paketmanager zur Installation, Aktualisierung und Deinstallation von Apps.",
        example_usage="sudo pacman -S steam  |  yay -S discord  |  sudo pacman -Rns paket"
    ),
    RosettaEntry(
        win_term="regedit (Windows Registry)",
        linux_equivalent="~/.config/ & ~/.local/share/",
        category="Dateisystem",
        description="Keine kryptische Binärdatenbank! Einstellungen liegen als lesbare Textdateien im Home-Ordner.",
        example_usage="nano ~/.config/MangoHud/MangoHud.conf"
    ),

    # Netzwerk
    RosettaEntry(
        win_term="ipconfig / ipconfig /all",
        linux_equivalent="ip addr / networkctl",
        category="Netzwerk",
        description="Zeigt Netzwerk-Adapter, lokale IP-Adressen und MAC-Adressen an.",
        example_usage="ip -c addr  |  networkctl status"
    ),
    RosettaEntry(
        win_term="ping -t (Dauer-Ping)",
        linux_equivalent="ping",
        category="Netzwerk",
        description="Unter Linux läuft ping standardmäßig endlos bis Strg+C gedrückt wird.",
        example_usage="ping 1.1.1.1  |  ping -c 4 google.com (nur 4 Pings)"
    ),
    RosettaEntry(
        win_term="tracert (Trace Route)",
        linux_equivalent="traceroute / mtr",
        category="Netzwerk",
        description="Verfolgt den Weg von Netzwerkpaketen über Router-Hops.",
        example_usage="traceroute archlinux.org  |  mtr 8.8.8.8"
    ),

    # Terminal-Befehle
    RosettaEntry(
        win_term="cls (Clear Screen)",
        linux_equivalent="clear (oder Strg+L)",
        category="Terminal",
        description="Leert die aktuelle Terminal-Ausgabe.",
        example_usage="clear"
    ),
    RosettaEntry(
        win_term="dir",
        linux_equivalent="ls -lah",
        category="Terminal",
        description="Zeigt Dateien und versteckte Verzeichnisse mit Rechten und Größe an.",
        example_usage="ls -lah"
    ),
    RosettaEntry(
        win_term="copy / xcopy / robocopy",
        linux_equivalent="cp -r / rsync -avP",
        category="Terminal",
        description="Kopiert Dateien oder ganze Verzeichnisse mit Fortschrittsanzeige.",
        example_usage="cp -r /quelle /ziel  |  rsync -avP /quelle/ /ziel/"
    ),
    RosettaEntry(
        win_term="move",
        linux_equivalent="mv",
        category="Terminal",
        description="Verschiebt oder benennt Dateien und Ordner um.",
        example_usage="mv alter_name.txt neuer_name.txt"
    ),
    RosettaEntry(
        win_term="del / rmdir /s /q",
        linux_equivalent="rm -rf",
        category="Terminal",
        description="Löscht Dateien oder Verzeichnisse unwiderruflich.",
        example_usage="rm datei.txt  |  rm -rf ordner/"
    ),
    RosettaEntry(
        win_term="diskpart / Datenträgerverwaltung",
        linux_equivalent="cfdisk / lsblk / gparted",
        category="Laufwerke",
        description="Partitionierungswerkzeuge für SSDs, HDDs und USB-Sticks.",
        example_usage="lsblk  |  sudo cfdisk /dev/nvme0n1"
    )
]

class RosettaEngine:
    """Sucht und filtert Übersetzungen zwischen Windows und Linux."""

    @classmethod
    def search(cls, query: str) -> List[RosettaEntry]:
        q = query.strip().lower()
        if not q:
            return ROSETTA_DICTIONARY
        matches = []
        for e in ROSETTA_DICTIONARY:
            if (q in e.win_term.lower() or 
                q in e.linux_equivalent.lower() or 
                q in e.category.lower() or 
                q in e.description.lower()):
                matches.append(e)
        return matches
