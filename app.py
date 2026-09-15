#!/usr/bin/env python3
"""
cachy-winbridge — The Windows-to-Linux Migration, Drive-Automount & Gaming Bridge
Designed for CachyOS / Arch Linux (KDE Plasma 6 Wayland).
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

from core.drives import DriveManager
from core.rosetta import RosettaEngine
from core.apps import AppDirectory
from core.wine_runner import WineRunner
from core.migrator import WindowsMigrator
from ui.console import (
    render_banner,
    render_drives_table,
    render_rosetta_table,
    render_apps_table,
    render_savegames_table,
    console,
)


def cmd_status(args: argparse.Namespace) -> None:
    render_banner()
    partitions = DriveManager.scan_partitions()
    render_drives_table(partitions)

    apps = AppDirectory.get_catalog()
    installed_count = sum(1 for a in apps if a.is_installed)
    console.print(f"\n[bold cyan]📦 Software-Status:[/] {installed_count}/{len(apps)} empfohlene Linux-Alternativen installiert.")
    console.print("[dim]Tipp: Starte 'python app.py tui' für das vollständige interaktive Dashboard.[/dim]\n")


def cmd_drives(args: argparse.Namespace) -> None:
    render_banner()
    partitions = DriveManager.scan_partitions()
    render_drives_table(partitions)

    if args.generate_fstab:
        console.print("\n[bold green]Empfohlene /etc/fstab Einträge für dauerhaftes Gaming-Automounting:[/]")
        console.print("[dim]Kopiere diese Zeilen in /etc/fstab oder nutze das automatische Backup.[/dim]\n")
        lines_to_add = []
        for p in partitions:
            if not p.is_in_fstab:
                console.print(f"[bold cyan]# {p.label} ({p.name}, {p.fstype})[/]")
                console.print(f"{p.recommended_fstab_line}\n")
                lines_to_add.append(p.recommended_fstab_line)

        if lines_to_add:
            valid, verify_msg = DriveManager.validate_fstab_addition(lines_to_add)
            if valid:
                console.print(f"[bold green]🛡️ Pre-Flight Sicherheitscheck bestanden (findmnt --verify):[/]\n{verify_msg}\n")
            else:
                console.print(f"[bold yellow]🛡️ Pre-Flight Sicherheitsanalyse (findmnt --verify):[/]\n{verify_msg}")
                missing_dirs = [p.recommended_mount_dir for p in partitions if not p.is_in_fstab and not Path(p.recommended_mount_dir).exists()]
                if missing_dirs:
                    mkdir_cmd = "sudo mkdir -p " + " ".join(missing_dirs)
                    console.print(f"[bold cyan]👉 Vorab Mount-Verzeichnisse erstellen:[/] [white]{mkdir_cmd}[/]\n")


def cmd_fstab_verify(args: argparse.Namespace) -> None:
    render_banner()
    console.print("[bold cyan]Führe Pre-Flight Syntax-Check der /etc/fstab via findmnt durch...[/]")
    ok, msg = DriveManager.verify_fstab_syntax()
    if ok:
        console.print(f"[bold green]✔ {msg}[/]")
    else:
        console.print(f"[bold red]❌ {msg}[/]")


def cmd_mount_all(args: argparse.Namespace) -> None:
    render_banner()
    partitions = DriveManager.scan_partitions()
    console.print("[bold yellow]Versuche ungemountete Partitionen einzubinden...[/]\n")
    for p in partitions:
        if not p.is_mounted:
            ok, msg = DriveManager.mount_partition_user(p.device_path)
            if ok:
                console.print(f"[bold green]✔ {p.name} ({p.label}): {msg}[/]")
            else:
                console.print(f"[bold red]❌ {p.name} ({p.label}): {msg}[/]")
        else:
            console.print(f"[dim]• {p.name} ist bereits eingehängt unter: {p.mountpoint}[/dim]")


def cmd_rosetta(args: argparse.Namespace) -> None:
    render_banner()
    query = args.query or ""
    entries = RosettaEngine.search(query)
    render_rosetta_table(entries, query=query)


def cmd_apps(args: argparse.Namespace) -> None:
    render_banner()
    apps = AppDirectory.get_catalog()
    render_apps_table(apps)


def cmd_migrator(args: argparse.Namespace) -> None:
    render_banner()
    console.print("[bold cyan]Scanne gemountete Datenträger nach Windows-Profilen und Steam Proton Spielständen...[/]")
    saves = WindowsMigrator.scan_savegames(custom_root=args.path)
    if not saves:
        console.print("[bold yellow]Keine Windows-Profile oder Spielstände in Standard-Mountpunkten (/mnt, /run/media) gefunden.[/]")
        console.print("[dim]Hinweis: Stelle sicher, dass deine Windows-Partitionen gemountet sind (z.B. mit 'cachy-winbridge mount-all').[/dim]")
    else:
        render_savegames_table(saves)
        if args.migrate_proton:
            console.print("\n[bold green]Starte automatische Migration in Steam Proton Compatdata-Prefixe...[/]")
            migrated = 0
            for s in saves:
                if s.is_proton_ready:
                    ok, msg = WindowsMigrator.migrate_savegame_to_proton(s)
                    if ok:
                        console.print(f"[bold green]✔ {s.game_title}: {msg}[/]")
                        migrated += 1
                    else:
                        console.print(f"[bold red]❌ {s.game_title}: {msg}[/]")
                else:
                    console.print(f"[dim]• {s.game_title}: Übersprungen (Kein aktiver Proton-Prefix für AppID #{s.matched_appid})[/dim]")
            console.print(f"\n[bold cyan]Migration beendet:[/] {migrated} Spielstände erfolgreich übertragen.")


def cmd_run_exe(args: argparse.Namespace) -> None:
    render_banner()
    exe_file = args.file
    console.print(f"[bold cyan]Starte '{exe_file}' im isolierten Micro-Prefix...[/]")
    ok, msg = WineRunner.run_executable(exe_file, isolated=not args.shared)
    if ok:
        console.print(f"[bold green]✔ {msg}[/]")
    else:
        console.print(f"[bold red]❌ {msg}[/]")


def cmd_tui(args: argparse.Namespace) -> None:
    from ui.tui import start_tui
    start_tui()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cachy-winbridge",
        description="🪟 Cachy-WinBridge — Windows-to-Linux Migration, Drive-Automount & Gaming Bridge"
    )
    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Befehle")

    # status
    p_status = subparsers.add_parser("status", help="Übersicht über Laufwerke, Gaming-Mounts und Software")
    p_status.set_defaults(func=cmd_status)

    # drives
    p_drives = subparsers.add_parser("drives", help="Erkennt Blockgeräte und zeigt Proton-sichere Mount-Optionen")
    p_drives.add_argument("--generate-fstab", action="store_true", help="Gibt optimierte /etc/fstab Zeilen inkl. findmnt-Sicherheitscheck aus")
    p_drives.set_defaults(func=cmd_drives)

    # fstab-verify
    p_fstab = subparsers.add_parser("fstab-verify", help="Führt einen Pre-Flight Syntax- & Konsistenz-Check der /etc/fstab durch")
    p_fstab.set_defaults(func=cmd_fstab_verify)

    # mount-all
    p_mount = subparsers.add_parser("mount-all", help="Hängt ungemountete Partitionen via udisksctl ein (inkl. Fast-Startup Diagnose)")
    p_mount.set_defaults(func=cmd_mount_all)

    # rosetta
    p_rosetta = subparsers.add_parser("rosetta", help="Windows-Befehle und Konzepte in Linux-Äquivalente übersetzen")
    p_rosetta.add_argument("query", nargs="?", default="", help="Suchbegriff (z.B. taskmgr, services, regedit)")
    p_rosetta.set_defaults(func=cmd_rosetta)

    # apps
    p_apps = subparsers.add_parser("apps", help="Windows-Tools durch native Linux-Alternativen ersetzen")
    p_apps.set_defaults(func=cmd_apps)

    # migrator
    p_migrator = subparsers.add_parser("migrator", help="Sucht nach alten Windows-Spielständen und verknüpft Steam Proton Prefixe")
    p_migrator.add_argument("--path", type=str, default=None, help="Benutzerdefinierter Suchpfad")
    p_migrator.add_argument("--migrate-proton", action="store_true", help="Kopiert erkannte Spielstände direkt in den isolierten Steam Proton compatdata Prefix")
    p_migrator.set_defaults(func=cmd_migrator)

    # run-exe
    p_exe = subparsers.add_parser("run-exe", help="Startet .exe/.msi Dateien in einem isolierten Wine-Prefix")
    p_exe.add_argument("file", help="Pfad zur .exe oder .msi Datei")
    p_exe.add_argument("--shared", action="store_true", help="Nutzt den gemeinsamen Standard-Prefix statt isoliertem Ordner")
    p_exe.set_defaults(func=cmd_run_exe)

    # tui
    p_tui = subparsers.add_parser("tui", help="Startet das interaktive TUI-Dashboard")
    p_tui.set_defaults(func=cmd_tui)

    args = parser.parse_args()

    if not args.command:
        # Standardmäßig Status anzeigen
        cmd_status(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
