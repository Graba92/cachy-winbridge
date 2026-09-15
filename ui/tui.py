"""
ui/tui.py — Interaktives Textual TUI-Dashboard für Cachy-WinBridge.
Bietet 4 Tabs: Laufwerke & Gaming-Mounts, Rosetta Stone, Software-Katalog und Savegame-Migrator.
"""

from __future__ import annotations
from typing import List, Optional
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
)

from core.drives import DriveManager, PartitionInfo
from core.rosetta import RosettaEngine, RosettaEntry
from core.apps import AppDirectory, AppEquivalent
from core.migrator import WindowsMigrator, DiscoveredSavegame


class WinBridgeApp(App):
    """Hauptanwendung für das Cachy-WinBridge Textual TUI Dashboard."""

    TITLE = "Cachy-WinBridge Dashboard"
    SUB_TITLE = "Windows-to-Linux Migration & Gaming Mount Suite"
    CSS = """
    Screen {
        background: #121820;
        color: #e2e8f0;
    }

    Header {
        background: #1a2332;
        color: #38bdf8;
    }

    Footer {
        background: #1a2332;
        color: #94a3b8;
    }

    TabbedContent {
        height: 1fr;
    }

    TabPane {
        padding: 1;
    }

    DataTable {
        height: 1fr;
        border: solid #0284c7;
        background: #0f172a;
    }

    #button_bar {
        height: 3;
        margin-top: 1;
        align: center middle;
    }

    Button {
        margin-right: 2;
        min-width: 20;
    }

    .info-panel {
        height: 5;
        border: solid #334155;
        background: #1e293b;
        padding: 1;
        margin-top: 1;
        color: #f8fafc;
    }

    Input {
        margin-bottom: 1;
        border: solid #0284c7;
        background: #0f172a;
    }

    .section-title {
        text-style: bold;
        color: #38bdf8;
        margin-bottom: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.partitions: List[PartitionInfo] = []
        self.rosetta_entries: List[RosettaEntry] = []
        self.software_catalog: List[AppEquivalent] = []
        self.savegames: List[DiscoveredSavegame] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="tab_drives"):
            # Tab 1: Drives & Automount
            with TabPane("💾 Laufwerke & Automount", id="tab_drives"):
                yield Label("Erkannte Partitionen & Gaming-Konfiguration:", classes="section-title")
                yield DataTable(id="drives_table", cursor_type="row")
                yield Static(
                    "Wähle eine Partition aus, um Aktionen durchzuführen oder die fstab-Konfiguration anzuzeigen.",
                    id="drives_info",
                    classes="info-panel"
                )
                with Horizontal(id="button_bar"):
                    yield Button("Laufwerke aktualisieren", id="btn_refresh_drives", variant="primary")
                    yield Button("Ausgewähltes einbinden", id="btn_mount_selected", variant="success")
                    yield Button("fstab Zeile anzeigen", id="btn_show_fstab", variant="default")

            # Tab 2: Rosetta Stone
            with TabPane("📖 Rosetta Stone", id="tab_rosetta"):
                yield Label("Windows-Befehle ➔ CachyOS / Linux Äquivalente:", classes="section-title")
                yield Input(placeholder="Suchbegriff eingeben (z.B. taskmgr, services, regedit, dir, dxdiag)...", id="rosetta_search")
                yield DataTable(id="rosetta_table", cursor_type="row")

            # Tab 3: Software-Katalog
            with TabPane("🛒 Software-Katalog", id="tab_apps"):
                yield Label("Windows-Tools ➔ Native Linux-Alternativen mit Installationsbefehl:", classes="section-title")
                yield DataTable(id="apps_table", cursor_type="row")
                yield Static(
                    "Drücke im Terminal 'q' zum Beenden oder nutze die CLI für direkte Installationen.",
                    classes="info-panel"
                )

            # Tab 4: Savegame-Migrator
            with TabPane("🎮 Savegame-Migrator", id="tab_saves"):
                yield Label("Windows-Spielstände und AppData auf gemounteten Laufwerken:", classes="section-title")
                yield DataTable(id="saves_table", cursor_type="row")
                with Horizontal(id="button_bar"):
                    yield Button("Windows-Laufwerke scannen", id="btn_scan_saves", variant="primary")
                    yield Button("In ~/Gefundene_Savegames kopieren", id="btn_copy_save", variant="warning")
                yield Static(
                    "Klicke auf 'Windows-Laufwerke scannen', um bestehende Windows-Profile nach Spielständen zu durchsuchen.",
                    id="saves_info",
                    classes="info-panel"
                )

        yield Footer()

    def on_mount(self) -> None:
        self.init_drives_table()
        self.init_rosetta_table()
        self.init_apps_table()
        self.init_saves_table()

        self.refresh_drives()
        self.refresh_rosetta("")
        self.refresh_apps()

    # --- DRIVES TAB LOGIC ---
    def init_drives_table(self) -> None:
        dt = self.query_one("#drives_table", DataTable)
        dt.add_columns("Gerät", "Dateisystem", "Größe", "Label", "Gemountet", "fstab Auto", "Gaming-Ready")

    def refresh_drives(self) -> None:
        dt = self.query_one("#drives_table", DataTable)
        dt.clear()
        self.partitions = DriveManager.scan_partitions()
        for i, p in enumerate(self.partitions):
            dt.add_row(
                p.name,
                p.fstype.upper(),
                p.size_human,
                p.label,
                "✔ " + (p.mountpoint or "") if p.is_mounted else "❌ Nein",
                "✔ Ja" if p.is_in_fstab else "❌ Nein",
                "✔ Bereit" if p.is_gaming_ready else "Standard",
                key=str(i)
            )
        info = self.query_one("#drives_info", Static)
        info.update(f"{len(self.partitions)} Partition(en) erkannt. Bereit für Automounting & Gaming-Konfiguration.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn_refresh_drives":
            self.refresh_drives()
        elif btn_id == "btn_mount_selected":
            self.mount_selected_partition()
        elif btn_id == "btn_show_fstab":
            self.show_fstab_line()
        elif btn_id == "btn_scan_saves":
            self.scan_savegames()
        elif btn_id == "btn_copy_save":
            self.copy_selected_save()

    def get_selected_partition(self) -> Optional[PartitionInfo]:
        dt = self.query_one("#drives_table", DataTable)
        if dt.cursor_row is not None and 0 <= dt.cursor_row < len(self.partitions):
            return self.partitions[dt.cursor_row]
        return None

    def mount_selected_partition(self) -> None:
        p = self.get_selected_partition()
        info = self.query_one("#drives_info", Static)
        if not p:
            info.update("[bold red]Keine Partition ausgewählt![/]")
            return
        if p.is_mounted:
            info.update(f"[bold yellow]{p.name} ist bereits gemountet unter: {p.mountpoint}[/]")
            return

        ok, msg = DriveManager.mount_partition_user(p.device_path)
        if ok:
            info.update(f"[bold green]Erfolgreich gemountet: {msg}[/]")
            self.refresh_drives()
        else:
            info.update(f"[bold red]Mount fehlgeschlagen: {msg}[/]")

    def show_fstab_line(self) -> None:
        p = self.get_selected_partition()
        info = self.query_one("#drives_info", Static)
        if not p:
            info.update("[bold red]Keine Partition ausgewählt![/]")
            return
        info.update(f"[bold cyan]Empfohlene /etc/fstab Zeile für {p.name}:[/]\n{p.recommended_fstab_line}")

    # --- ROSETTA TAB LOGIC ---
    def init_rosetta_table(self) -> None:
        dt = self.query_one("#rosetta_table", DataTable)
        dt.add_columns("Windows-Begriff", "Linux-Äquivalent", "Kategorie", "Beschreibung & Beispiel")

    def refresh_rosetta(self, query: str) -> None:
        dt = self.query_one("#rosetta_table", DataTable)
        dt.clear()
        self.rosetta_entries = RosettaEngine.search(query)
        for e in self.rosetta_entries:
            dt.add_row(
                e.win_term,
                e.linux_equivalent,
                e.category,
                f"{e.description} | {e.example_usage}"
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "rosetta_search":
            self.refresh_rosetta(event.value)

    # --- APPS TAB LOGIC ---
    def init_apps_table(self) -> None:
        dt = self.query_one("#apps_table", DataTable)
        dt.add_columns("Windows-Programm", "Linux-Alternative", "Kategorie", "Status", "Installations-Befehl")

    def refresh_apps(self) -> None:
        dt = self.query_one("#apps_table", DataTable)
        dt.clear()
        self.software_catalog = AppDirectory.get_catalog()
        for a in self.software_catalog:
            dt.add_row(
                a.win_name,
                a.linux_name,
                a.category,
                "✔ Installiert" if a.is_installed else "Verfügbar",
                a.install_cmd
            )

    # --- SAVES TAB LOGIC ---
    def init_saves_table(self) -> None:
        dt = self.query_one("#saves_table", DataTable)
        dt.add_columns("Spiel / Ordner", "Kategorie", "Größe", "Steam AppID", "Proton Zielpfad / Quelle")

    def scan_savegames(self) -> None:
        info = self.query_one("#saves_info", Static)
        info.update("Scanne gemountete Windows-Laufwerke und Steam Proton Compatdata-Prefixe...")
        self.savegames = WindowsMigrator.scan_savegames()
        dt = self.query_one("#saves_table", DataTable)
        dt.clear()
        for s in self.savegames:
            appid_col = f"#{s.matched_appid}" if s.matched_appid else "—"
            target_col = s.proton_target_dir if s.proton_target_dir else s.source_path
            dt.add_row(
                s.game_title,
                s.category,
                f"{s.size_mb} MB",
                appid_col,
                target_col
            )
        info.update(f"Scan abgeschlossen: {len(self.savegames)} Spielstände erkannt. Proton-kompatible Saves werden direkt in den Compatdata-Prefix übertragen.")

    def copy_selected_save(self) -> None:
        dt = self.query_one("#saves_table", DataTable)
        info = self.query_one("#saves_info", Static)
        if dt.cursor_row is None or not (0 <= dt.cursor_row < len(self.savegames)):
            info.update("[bold red]Kein Spielstand ausgewählt![/]")
            return

        save = self.savegames[dt.cursor_row]
        if save.is_proton_ready:
            ok, msg = WindowsMigrator.migrate_savegame_to_proton(save)
            if ok:
                info.update(f"[bold green]✔ Direkt in Steam Proton übertragen: {save.game_title}[/]")
            else:
                info.update(f"[bold red]{msg}[/]")
        else:
            dest_dir = Path.home() / "Gefundene_Savegames"
            ok = WindowsMigrator.copy_savegame(save.source_path, str(dest_dir))
            if ok:
                info.update(f"[bold yellow]Kopiert nach {dest_dir / save.game_title} (Kein aktiver Proton-Prefix für #{save.matched_appid})[/]")
            else:
                info.update(f"[bold red]Fehler beim Kopieren von {save.game_title}![/]")


def start_tui() -> None:
    """Startet das interaktive TUI-Dashboard."""
    app = WinBridgeApp()
    app.run()


if __name__ == "__main__":
    start_tui()
