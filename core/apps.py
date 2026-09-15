"""
core/apps.py — Windows-zu-Linux Software-Äquivalente & 1-Klick Installer.
Zeigt Umsteigern die perfekten Linux-Alternativen zu ihren vertrauten Windows-Programmen.
"""

from __future__ import annotations
import shutil
from dataclasses import dataclass
from typing import List

@dataclass
class AppEquivalent:
    win_name: str
    linux_name: str
    category: str
    description: str
    install_cmd: str
    check_binary: str
    is_installed: bool = False

APP_CATALOG: List[AppEquivalent] = [
    # Gaming & Tuning
    AppEquivalent(
        win_name="MSI Afterburner & RivaTuner",
        linux_name="MangoHud + Goverlay",
        category="Gaming",
        description="FPS-Overlay, Frame-Time-Graphen, GPU/CPU-Temperaturanzeige direkt im Spiel.",
        install_cmd="sudo pacman -S --needed mangohud goverlay",
        check_binary="mangohud"
    ),
    AppEquivalent(
        win_name="CPU-Z & HWMonitor",
        linux_name="CPU-X & Btop",
        category="Hardware",
        description="Detaillierte Hardware-Spezifikationen, Taktraten, Spannungen und Auslastung.",
        install_cmd="sudo pacman -S --needed cpu-x btop",
        check_binary="cpu-x"
    ),
    AppEquivalent(
        win_name="Epic Games Launcher & GOG Galaxy",
        linux_name="Heroic Games Launcher",
        category="Gaming",
        description="Nativer, blitzschneller Open-Source-Launcher für Epic Games, GOG und Amazon Games.",
        install_cmd="sudo pacman -S --needed heroic-games-launcher-bin || yay -S heroic-games-launcher",
        check_binary="heroic"
    ),
    AppEquivalent(
        win_name="Equalizer APO & Realtek Audio Control",
        linux_name="EasyEffects (PipeWire)",
        category="Audio",
        description="Systemweiter Equalizer, Bass-Boost, Kompressor und Mikrofon-Rauschfilter für PipeWire.",
        install_cmd="sudo pacman -S --needed easyeffects",
        check_binary="easyeffects"
    ),

    # Produktivität & Editoren
    AppEquivalent(
        win_name="Notepad++",
        linux_name="Kate / Notepadqq",
        category="Produktivität",
        description="Mächtiger Code- und Texteditor mit Syntax-Highlighting, Tabs und Plugins.",
        install_cmd="sudo pacman -S --needed kate",
        check_binary="kate"
    ),
    AppEquivalent(
        win_name="7-Zip & WinRAR",
        linux_name="PeaZip / Ark",
        category="Tools",
        description="Modernes Archivierungswerkzeug mit voller 7z-, RAR-, ZIP- und Zstandard-Unterstützung.",
        install_cmd="sudo pacman -S --needed ark  # oder yay -S peazip-qt6",
        check_binary="ark"
    ),
    AppEquivalent(
        win_name="Rufus & UNetbootin",
        linux_name="Ventoy / Impression",
        category="Tools",
        description="Bootfähige USB-Sticks erstellen (Ventoy erlaubt einfaches ISO-Drag-and-Drop).",
        install_cmd="sudo pacman -S --needed ventoy",
        check_binary="ventoy"
    ),
    AppEquivalent(
        win_name="Paint.NET / Photoshop Basics",
        linux_name="Pinta / Krita / GIMP",
        category="Grafik",
        description="Ebenenbasierte Bildbearbeitung, Retusche und digitales Zeichnen.",
        install_cmd="sudo pacman -S --needed krita gimp pinta",
        check_binary="krita"
    ),
    AppEquivalent(
        win_name="Discord",
        linux_name="Discord / Vesktop",
        category="Kommunikation",
        description="Voice- und Textchat (Vesktop bietet native Wayland-Screensharing-Unterstützung).",
        install_cmd="sudo pacman -S --needed discord || yay -S vesktop",
        check_binary="discord"
    ),
    AppEquivalent(
        win_name="OBS Studio",
        linux_name="OBS Studio (Native Wayland)",
        category="Streaming",
        description="Live-Streaming und Bildschirmaufnahmen mit nativer PipeWire- und NVENC/VAAPI-Hardwarebeschleunigung.",
        install_cmd="sudo pacman -S --needed obs-studio",
        check_binary="obs"
    )
]

class AppDirectory:
    """Verwaltet den Katalog und prüft den Installationsstatus im System."""

    @classmethod
    def get_catalog(cls) -> List[AppEquivalent]:
        apps = []
        for app in APP_CATALOG:
            installed = bool(shutil.which(app.check_binary))
            apps.append(AppEquivalent(
                win_name=app.win_name,
                linux_name=app.linux_name,
                category=app.category,
                description=app.description,
                install_cmd=app.install_cmd,
                check_binary=app.check_binary,
                is_installed=installed
            ))
        return apps
