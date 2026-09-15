"""
ui/console.py — Rich CLI Terminal Formatting & Tabellen für Cachy-WinBridge.
"""

from __future__ import annotations
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.drives import PartitionInfo
from core.rosetta import RosettaEntry
from core.apps import AppEquivalent
from core.migrator import DiscoveredSavegame

console = Console(record=True, width=120)

def render_banner() -> None:
    text = Text()
    text.append("🪟 CACHY-WINBRIDGE 🪟\n", style="bold cyan")
    text.append("The Windows-to-Linux Migration, Drive-Automount & Gaming Bridge\n", style="bold white")
    text.append("Tailored for CachyOS / Arch Linux (KDE Plasma 6 Wayland)", style="dim cyan")
    panel = Panel(text, border_style="bright_blue", expand=False)
    console.print(panel)

def render_drives_table(partitions: List[PartitionInfo]) -> None:
    table = Table(title="💾 Festplatten- & Gaming-Partitionen Übersicht", border_style="bright_blue", show_header=True, expand=True)
    table.add_column("Gerät", style="bold cyan", width=10)
    table.add_column("Dateisystem", style="yellow", width=12)
    table.add_column("Größe", justify="right", width=10)
    table.add_column("Label", style="bold white")
    table.add_column("Gemountet?", justify="center", width=18)
    table.add_column("In fstab?", justify="center", width=16)
    table.add_column("Gaming Ready", justify="center", width=16)

    for p in partitions:
        mounted_str = f"[bold green]JA[/] ({p.mountpoint})" if p.is_mounted else "[dim red]NEIN[/]"
        fstab_str = "[bold green]JA (Auto)[/]" if p.is_in_fstab else "[bold yellow]NEIN (Manuell)[/]"
        gaming_str = "[bold green]✔ Optimiert[/]" if p.is_gaming_ready else "[dim]Standard[/]"

        table.add_row(
            p.name,
            p.fstype.upper(),
            p.size_human,
            p.label,
            mounted_str,
            fstab_str,
            gaming_str
        )

    console.print(table)

def render_rosetta_table(entries: List[RosettaEntry], query: str = "") -> None:
    title = f"📖 Windows ➔ Linux Rosetta Stone ({len(entries)} Einträge)"
    if query:
        title += f" [Filter: '{query}']"
    table = Table(title=title, border_style="magenta", show_header=True, expand=True)
    table.add_column("Windows-Begriff / Befehl", style="bold cyan", width=28)
    table.add_column("Linux-Äquivalent", style="bold green", width=28)
    table.add_column("Kategorie", style="yellow", width=14)
    table.add_column("Erklärung & Beispiel", style="white")

    for e in entries:
        desc = f"{e.description}\n[dim cyan]Beispiel: {e.example_usage}[/dim cyan]"
        table.add_row(e.win_term, e.linux_equivalent, e.category, desc)

    console.print(table)

def render_apps_table(apps: List[AppEquivalent]) -> None:
    table = Table(title="🛒 Windows-Software ➔ Native Linux-Äquivalente", border_style="green", show_header=True, expand=True)
    table.add_column("Windows-Programm", style="bold cyan", width=26)
    table.add_column("Linux-Alternative", style="bold green", width=26)
    table.add_column("Status", justify="center", width=14)
    table.add_column("Installations-Befehl (pacman/yay)", style="white")

    for a in apps:
        status_str = "[bold green]✔ Installiert[/]" if a.is_installed else "[bold yellow]Verfügbar[/]"
        table.add_row(a.win_name, a.linux_name, status_str, f"[dim]{a.install_cmd}[/dim]")

    console.print(table)

def render_savegames_table(saves: List[DiscoveredSavegame]) -> None:
    table = Table(title=f"🎮 Gefundene Windows-Spielstände & Steam Proton Status ({len(saves)})", border_style="yellow", show_header=True, expand=True)
    table.add_column("Spiel / Ordner", style="bold cyan", width=22)
    table.add_column("Kategorie", style="magenta", width=18)
    table.add_column("Größe", justify="right", width=10)
    table.add_column("Steam AppID", justify="center", width=16)
    table.add_column("Proton Prefix Status", width=24)
    table.add_column("Zielpfad / Quelle", style="dim white")

    for s in saves:
        if s.matched_appid:
            appid_str = f"[bold cyan]#{s.matched_appid}[/]"
            if s.is_proton_ready:
                proton_status = "[bold green]✔ Prefix bereit[/]"
                target_str = f"[green]{s.proton_target_dir}[/]"
            else:
                proton_status = "[yellow]⏳ Prefix ungenutzt[/]"
                target_str = f"[dim]{s.proton_target_dir}[/dim]"
        else:
            appid_str = "[dim]Nicht erkannt[/dim]"
            proton_status = "[dim]Manuell / DRM-frei[/dim]"
            target_str = s.source_path

        table.add_row(
            s.game_title,
            s.category,
            f"{s.size_mb} MB",
            appid_str,
            proton_status,
            target_str
        )

    console.print(table)

