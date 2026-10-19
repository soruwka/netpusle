#!/usr/bin/env python3
"""
 ███╗   ██╗███████╗████████╗██████╗ ██╗   ██╗██╗     ███████╗███████╗
 ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
 ██╔██╗ ██║█████╗     ██║   ██████╔╝██║   ██║██║     ███████╗█████╗
 ██║╚██╗██║██╔══╝     ██║   ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝
 ██║ ╚████║███████╗   ██║   ██║     ╚██████╔╝███████╗███████║███████╗
 ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝
                    WiFi Network Intelligence Suite v1.0
                         github.com/netpulse | @netpulse
"""

import sys
import os
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, TabbedContent, TabPane, Static,
    DataTable, RichLog, Label, Button, Input,
)
from textual.containers import Container, Horizontal, Vertical
from textual import work, on

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.wifi_info import WiFiInfo
from modules.bandwidth import BandwidthMonitor
from modules.network_scanner import NetworkScanner
from modules.packet_capture import PacketCapture
from modules.dns_monitor import DNSMonitor
from modules.log_viewer import LogViewer


LOGO = (
    "[bold cyan] ███╗   ██╗███████╗████████╗██████╗ ██╗   ██╗██╗     ███████╗███████╗\n"
    " ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║   ██║██║     ██╔════╝██╔════╝\n"
    " ██╔██╗ ██║█████╗     ██║   ██████╔╝██║   ██║██║     ███████╗█████╗\n"
    " ██║╚██╗██║██╔══╝     ██║   ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝\n"
    " ██║ ╚████║███████╗   ██║   ██║     ╚██████╔╝███████╗███████║███████╗\n"
    " ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝[/bold cyan]\n"
    "[bold yellow]              ★  WiFi Network Intelligence Suite v1.0  ★[/bold yellow]"
)


class NetPulseApp(App):
    """NetPulse — Professional WiFi Analysis Tool"""

    CSS = """
    Screen { background: #0d1117; color: #c9d1d9; }

    #banner {
        height: 9;
        content-align: center middle;
        background: #0d1117;
        padding: 1;
    }

    TabbedContent { height: 1fr; }

    TabPane { padding: 1 2; background: #0d1117; }

    /* ── stat cards ── */
    .stat-card {
        border: solid #30363d;
        background: #161b22;
        padding: 1;
        margin: 0 1;
        height: 7;
        min-width: 18;
    }
    .card-title {
        color: #58a6ff;
        text-style: bold;
        width: 100%;
        content-align: center top;
    }
    .card-value {
        color: #3fb950;
        text-style: bold;
        width: 100%;
        content-align: center middle;
        height: 3;
    }

    /* ── section headings ── */
    .section-title {
        color: #58a6ff;
        text-style: bold;
        padding: 1 0 0 0;
    }

    /* ── tables ── */
    DataTable {
        height: 1fr;
        border: solid #30363d;
        background: #161b22;
    }
    DataTable > .datatable--header {
        background: #21262d;
        color: #58a6ff;
        text-style: bold;
    }
    DataTable > .datatable--cursor { background: #1f6feb; }

    /* ── rich logs ── */
    RichLog {
        height: 1fr;
        border: solid #30363d;
        background: #0d1117;
        padding: 0 1;
    }

    /* ── buttons ── */
    Button { background: #21262d; border: solid #30363d; margin: 0 1; }
    Button:hover { background: #30363d; }
    Button.-success { background: #1a4731; border: solid #3fb950; color: #3fb950; }
    Button.-error   { background: #4d1a1a; border: solid #f85149; color: #f85149; }
    Button.-warning { background: #3d2c00; border: solid #d29922; color: #d29922; }

    /* ── input ── */
    Input { background: #21262d; border: solid #30363d; margin: 0 1; width: 30; }

    /* ── utility ── */
    .controls   { height: 5; padding: 1 0; }
    .full-height { height: 1fr; }
    .status-good { color: #3fb950; }
    .status-warn { color: #d29922; }
    .status-bad  { color: #f85149; }
    .status-info { color: #58a6ff; }

    #dashboard-cards { height: 9; padding: 1 0; }
    """

    BINDINGS = [
        ("q",      "quit",        "Quit"),
        ("r",      "refresh_all", "Refresh"),
        ("ctrl+c", "quit",        "Exit"),
    ]

    # ──────────────────────────────────────────────────────────────
    def __init__(self):
        super().__init__()
        self.wifi_info      = WiFiInfo()
        self.bw_monitor     = BandwidthMonitor()
        self.scanner        = NetworkScanner()
        self.packet_capture = PacketCapture()
        self.dns_monitor    = DNSMonitor()
        self.log_viewer     = LogViewer()

        self._capture_running = False
        self._dns_running     = False

    # ──────────────────────── compose ────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(LOGO, id="banner")
        with TabbedContent(initial="dashboard"):
            with TabPane("Dashboard",   id="dashboard"):
                yield from self._compose_dashboard()
            with TabPane("WiFi Info",   id="wifi"):
                yield from self._compose_wifi()
            with TabPane("Packets",     id="packets"):
                yield from self._compose_packets()
            with TabPane("DNS Monitor", id="dns"):
                yield from self._compose_dns()
            with TabPane("Bandwidth",   id="bandwidth"):
                yield from self._compose_bandwidth()
            with TabPane("Scanner",     id="scanner"):
                yield from self._compose_scanner()
            with TabPane("Logs",        id="logs"):
                yield from self._compose_logs()
        yield Footer()

    # ─────────────────────── tab layouts ─────────────────────────

    def _compose_dashboard(self):
        with Horizontal(id="dashboard-cards"):
            for card_id, title in [
                ("d-iface",  "Interface"),
                ("d-ssid",   "SSID"),
                ("d-signal", "Signal"),
                ("d-ip",     "IP Address"),
                ("d-up",     "↑ Upload"),
                ("d-down",   "↓ Download"),
            ]:
                with Container(classes="stat-card"):
                    yield Label(title, classes="card-title")
                    yield Label("—", id=card_id, classes="card-value")
        yield Label("Live Activity", classes="section-title")
        yield RichLog(id="dash-log", highlight=True, markup=True)

    def _compose_wifi(self):
        with Horizontal(classes="controls"):
            yield Button("Refresh Info",   id="btn-wifi-refresh")
            yield Button("Scan Networks",  id="btn-wifi-scan")
        yield Label("Current Connection", classes="section-title")
        t = DataTable(id="wifi-conn-table", show_cursor=False)
        t.add_columns("Property", "Value")
        yield t
        yield Label("Nearby Networks", classes="section-title")
        s = DataTable(id="wifi-scan-table")
        s.add_columns("SSID", "BSSID", "Signal", "Quality", "Channel", "Freq", "Security")
        yield s

    def _compose_packets(self):
        with Horizontal(classes="controls"):
            yield Button("▶ Start Capture", id="btn-pkt-start", classes="-success")
            yield Button("⏹ Stop Capture",  id="btn-pkt-stop",  classes="-error")
            yield Label("BPF filter:", classes="status-info")
            yield Input(placeholder="tcp or udp or icmp", id="pkt-filter")
            yield Label("", id="pkt-status", classes="status-warn")
        t = DataTable(id="pkt-table")
        t.add_columns("Time", "Protocol", "Source", "Destination", "Len", "Info")
        yield t

    def _compose_dns(self):
        with Horizontal(classes="controls"):
            yield Button("▶ Start Monitor", id="btn-dns-start", classes="-success")
            yield Button("⏹ Stop Monitor",  id="btn-dns-stop",  classes="-error")
            yield Button("Clear",         id="btn-dns-clear")
            yield Label("", id="dns-status", classes="status-warn")
        yield Label("DNS Query Log  (your machine only)", classes="section-title")
        yield RichLog(id="dns-log", highlight=True, markup=True, classes="full-height")

    def _compose_bandwidth(self):
        with Horizontal(classes="controls"):
            yield Button("Refresh Stats", id="btn-bw-refresh")
        yield Label("Interface Statistics", classes="section-title")
        t = DataTable(id="bw-table", show_cursor=False)
        t.add_columns("Interface", "↑ Sent", "↓ Received", "Pkts Sent", "Pkts Recv", "Errors")
        yield t
        yield Label("Real-time Speeds", classes="section-title")
        yield RichLog(id="bw-log", highlight=True, markup=True)

    def _compose_scanner(self):
        with Horizontal(classes="controls"):
            yield Label("Network range:", classes="status-info")
            yield Input(placeholder="192.168.1.0/24", id="scan-range")
            yield Button("ARP Scan", id="btn-scan-start", classes="-success")
            yield Label("! Requires root (scapy)", classes="status-warn")
        yield Label("Discovered Devices", classes="section-title")
        t = DataTable(id="net-scan-table")
        t.add_columns("IP Address", "MAC Address", "Hostname", "Status")
        yield t

    def _compose_logs(self):
        with Horizontal(classes="controls"):
            yield Button("WiFi Logs",    id="btn-log-wifi")
            yield Button("Network Logs", id="btn-log-net")
            yield Button("Error Logs",   id="btn-log-err")
            yield Button("Clear",         id="btn-log-clear")
        yield RichLog(id="sys-log", highlight=True, markup=True, classes="full-height")

    # ──────────────────────── lifecycle ──────────────────────────

    def on_mount(self) -> None:
        self.title     = "NetPulse"
        self.sub_title = "WiFi Network Intelligence Suite"
        self.set_interval(3, self._tick_dashboard)
        self.set_interval(2, self._tick_bandwidth)
        self.call_after_refresh(self._initial_load)

    def _initial_load(self) -> None:
        self._load_wifi_info()
        self._load_bandwidth()
        self._load_logs("wifi")

    def on_unmount(self) -> None:
        self._capture_running = False
        self._dns_running     = False
        self.packet_capture.stop_capture()
        self.dns_monitor.stop_monitor()

    # ───────────────────────── timers ────────────────────────────

    def _tick_dashboard(self)  -> None: self._update_dashboard()
    def _tick_bandwidth(self)  -> None: self._update_bw_realtime()

    # ─────────────────────── workers ─────────────────────────────

    @work(thread=True)
    def _update_dashboard(self) -> None:
        try:
            info   = self.wifi_info.get_connected_info()
            speeds = self.bw_monitor.get_realtime_speeds()
            self.app.call_from_thread(self._apply_dashboard, info, speeds)
        except Exception as e:
            self.app.call_from_thread(self._dash_log, f"[red]Error: {e}[/red]")

    def _apply_dashboard(self, info: dict, speeds: dict) -> None:
        def _set(widget_id, text):
            try:
                self.query_one(f"#{widget_id}", Label).update(str(text))
            except Exception:
                pass

        _set("d-iface",  info.get("interface", "—"))
        _set("d-ssid",   info.get("ssid",      "—"))
        _set("d-signal", info.get("signal",    "—"))
        _set("d-ip",     info.get("ip",        "—"))
        _set("d-up",     speeds.get("upload",   "—"))
        _set("d-down",   speeds.get("download", "—"))

        ts = datetime.now().strftime("%H:%M:%S")
        ssid = info.get("ssid", "N/A")
        ip   = info.get("ip",   "N/A")
        self._dash_log(
            f"[dim]{ts}[/dim]  [cyan]Connected:[/cyan] [bold green]{ssid}[/bold green]"
            f"   [cyan]IP:[/cyan] [yellow]{ip}[/yellow]"
            f"   [green]↑ {speeds.get('upload','?')}[/green]"
            f"   [cyan]↓ {speeds.get('download','?')}[/cyan]"
        )

    # ── wifi ──

    @work(thread=True)
    def _load_wifi_info(self) -> None:
        try:
            info = self.wifi_info.get_connected_info()
            self.app.call_from_thread(self._apply_wifi_conn, info)
        except Exception as e:
            self._dash_log(f"[red]WiFi info error: {e}[/red]")

    def _apply_wifi_conn(self, info: dict) -> None:
        try:
            t = self.query_one("#wifi-conn-table", DataTable)
            t.clear()
            for key, label in [
                ("interface", "Interface"),
                ("ssid",      "SSID"),
                ("bssid",     "AP MAC (BSSID)"),
                ("ip",        "IP Address"),
                ("gateway",   "Gateway"),
                ("dns",       "DNS Servers"),
                ("signal",    "Signal Level"),
                ("quality",   "Signal Quality"),
                ("frequency", "Frequency"),
                ("channel",   "Channel"),
                ("security",  "Security"),
                ("mode",      "Mode"),
                ("speed",     "Link Speed"),
            ]:
                t.add_row(label, info.get(key, "N/A"))
        except Exception:
            pass

    @work(thread=True)
    def _scan_wifi_networks(self) -> None:
        try:
            self._dash_log("[yellow]Scanning for nearby networks…[/yellow]")
            nets = self.wifi_info.scan_nearby()
            self.app.call_from_thread(self._apply_wifi_scan, nets)
        except Exception as e:
            self._dash_log(f"[red]Scan error: {e}[/red]")

    def _apply_wifi_scan(self, networks: list) -> None:
        try:
            t = self.query_one("#wifi-scan-table", DataTable)
            t.clear()
            for n in networks:
                t.add_row(
                    n.get("ssid",      "Hidden"),
                    n.get("bssid",     "N/A"),
                    n.get("signal",    "N/A"),
                    n.get("quality",   "N/A"),
                    n.get("channel",   "N/A"),
                    n.get("frequency", "N/A"),
                    n.get("security",  "Open"),
                )
            self._dash_log(f"[green]Found {len(networks)} network(s)[/green]")
        except Exception:
            pass

    # ── packets ──

    @work(thread=True)
    def _start_packet_capture(self) -> None:
        try:
            bpf = self.query_one("#pkt-filter", Input).value.strip()
        except Exception:
            bpf = ""

        self._capture_running = True
        self.app.call_from_thread(self._set_label, "pkt-status", "[green]● Capturing…[/green]")

        def cb(pkt_info: dict) -> None:
            if not self._capture_running:
                return
            self.app.call_from_thread(self._add_packet_row, pkt_info)

        self.packet_capture.start_capture(callback=cb, bpf_filter=bpf)

    def _add_packet_row(self, pkt_info: dict) -> None:
        try:
            t = self.query_one("#pkt-table", DataTable)
            if t.row_count > 800:
                t.clear()
            t.add_row(
                pkt_info.get("time",     ""),
                pkt_info.get("protocol", ""),
                pkt_info.get("src",      ""),
                pkt_info.get("dst",      ""),
                str(pkt_info.get("length", "")),
                pkt_info.get("info",     ""),
            )
        except Exception:
            pass

    # ── dns ──

    @work(thread=True)
    def _start_dns_monitor(self) -> None:
        self._dns_running = True
        self.app.call_from_thread(self._set_label, "dns-status", "[green]● Monitoring…[/green]")

        def cb(entry: dict) -> None:
            if not self._dns_running:
                return
            self.app.call_from_thread(self._add_dns_entry, entry)

        self.dns_monitor.start_monitor(callback=cb)

    def _add_dns_entry(self, entry: dict) -> None:
        try:
            log = self.query_one("#dns-log", RichLog)
            ts     = entry.get("time",     "")
            domain = entry.get("domain",   "")
            qtype  = entry.get("type",     "")
            src    = entry.get("src",      "")
            log.write(
                f"[dim]{ts}[/dim]  [cyan]{qtype:<6}[/cyan]  "
                f"[bold green]{domain:<50}[/bold green]  [dim]{src}[/dim]"
            )
        except Exception:
            pass

    # ── bandwidth ──

    @work(thread=True)
    def _load_bandwidth(self) -> None:
        try:
            stats = self.bw_monitor.get_all_interfaces()
            self.app.call_from_thread(self._apply_bw_table, stats)
        except Exception:
            pass

    def _apply_bw_table(self, stats: dict) -> None:
        try:
            t = self.query_one("#bw-table", DataTable)
            t.clear()
            for iface, d in stats.items():
                t.add_row(
                    iface,
                    d.get("bytes_sent_hr", "N/A"),
                    d.get("bytes_recv_hr", "N/A"),
                    str(d.get("packets_sent", 0)),
                    str(d.get("packets_recv", 0)),
                    str(d.get("errin", 0) + d.get("errout", 0)),
                )
        except Exception:
            pass

    @work(thread=True)
    def _update_bw_realtime(self) -> None:
        try:
            speeds = self.bw_monitor.get_realtime_speeds()
            self.app.call_from_thread(self._apply_bw_realtime, speeds)
        except Exception:
            pass

    def _apply_bw_realtime(self, speeds: dict) -> None:
        try:
            log   = self.query_one("#bw-log", RichLog)
            ts    = datetime.now().strftime("%H:%M:%S")
            up    = speeds.get("upload",    "0 B/s")
            dn    = speeds.get("download",  "0 B/s")
            iface = speeds.get("interface", "?")
            log.write(
                f"[dim]{ts}[/dim]  [{iface}]  "
                f"[green]↑ {up:>12}[/green]   [cyan]↓ {dn:>12}[/cyan]"
            )
        except Exception:
            pass

    # ── scanner ──

    @work(thread=True)
    def _scan_network(self) -> None:
        try:
            net_range = self.query_one("#scan-range", Input).value.strip()
            if not net_range:
                self._dash_log("[yellow]Enter a network range first (e.g. 192.168.1.0/24)[/yellow]")
                return
            self._dash_log(f"[yellow]ARP scanning {net_range}…[/yellow]")
            devices = self.scanner.arp_scan(net_range)
            self.app.call_from_thread(self._apply_net_scan, devices, net_range)
        except Exception as e:
            self._dash_log(f"[red]Scanner error: {e}[/red]")

    def _apply_net_scan(self, devices: list, net_range: str) -> None:
        try:
            t = self.query_one("#net-scan-table", DataTable)
            t.clear()
            for d in devices:
                t.add_row(
                    d.get("ip",       "N/A"),
                    d.get("mac",      "N/A"),
                    d.get("hostname", "Unknown"),
                    "[bold green]● Online[/bold green]",
                )
            self._dash_log(f"[green]Scanner: {len(devices)} device(s) on {net_range}[/green]")
        except Exception:
            pass

    # ── logs ──

    @work(thread=True)
    def _load_logs(self, log_type: str = "wifi") -> None:
        try:
            if log_type == "wifi":
                entries = self.log_viewer.get_wifi_logs()
            elif log_type == "network":
                entries = self.log_viewer.get_network_logs()
            else:
                entries = self.log_viewer.get_error_logs()
            self.app.call_from_thread(self._apply_logs, entries)
        except Exception:
            pass

    def _apply_logs(self, entries: list) -> None:
        try:
            log = self.query_one("#sys-log", RichLog)
            log.clear()
            for line in entries[-300:]:
                log.write(line)
        except Exception:
            pass

    # ─────────────────────── helpers ─────────────────────────────

    def _dash_log(self, message: str) -> None:
        try:
            self.query_one("#dash-log", RichLog).write(message)
        except Exception:
            pass

    def _set_label(self, widget_id: str, markup: str) -> None:
        try:
            self.query_one(f"#{widget_id}", Label).update(markup)
        except Exception:
            pass

    # ──────────────────── button handlers ────────────────────────

    @on(Button.Pressed, "#btn-wifi-refresh")
    def _h_wifi_refresh(self)  -> None: self._load_wifi_info()

    @on(Button.Pressed, "#btn-wifi-scan")
    def _h_wifi_scan(self)     -> None: self._scan_wifi_networks()

    @on(Button.Pressed, "#btn-pkt-start")
    def _h_pkt_start(self) -> None:
        if not self._capture_running:
            self._start_packet_capture()

    @on(Button.Pressed, "#btn-pkt-stop")
    def _h_pkt_stop(self) -> None:
        self._capture_running = False
        self.packet_capture.stop_capture()
        self._set_label("pkt-status", "[dim]● Stopped[/dim]")

    @on(Button.Pressed, "#btn-dns-start")
    def _h_dns_start(self) -> None:
        if not self._dns_running:
            self._start_dns_monitor()

    @on(Button.Pressed, "#btn-dns-stop")
    def _h_dns_stop(self) -> None:
        self._dns_running = False
        self.dns_monitor.stop_monitor()
        self._set_label("dns-status", "[dim]● Stopped[/dim]")

    @on(Button.Pressed, "#btn-dns-clear")
    def _h_dns_clear(self) -> None:
        try: self.query_one("#dns-log", RichLog).clear()
        except Exception: pass

    @on(Button.Pressed, "#btn-bw-refresh")
    def _h_bw_refresh(self)    -> None: self._load_bandwidth()

    @on(Button.Pressed, "#btn-scan-start")
    def _h_scan_start(self)    -> None: self._scan_network()

    @on(Button.Pressed, "#btn-log-wifi")
    def _h_log_wifi(self)      -> None: self._load_logs("wifi")

    @on(Button.Pressed, "#btn-log-net")
    def _h_log_net(self)       -> None: self._load_logs("network")

    @on(Button.Pressed, "#btn-log-err")
    def _h_log_err(self)       -> None: self._load_logs("error")

    @on(Button.Pressed, "#btn-log-clear")
    def _h_log_clear(self) -> None:
        try: self.query_one("#sys-log", RichLog).clear()
        except Exception: pass

    def action_refresh_all(self) -> None:
        self._load_wifi_info()
        self._load_bandwidth()


# ─────────────────────────────────────────────────────────────────────────────

def check_privileges() -> None:
    if os.geteuid() != 0:
        print("\n\033[33m⚠  Warning: not running as root.\033[0m")
        print("   Packet capture, DNS monitor & network scanner require root.")
        print("   Re-run with:  sudo python3 main.py\n")


def main() -> None:
    check_privileges()
    app = NetPulseApp()
    app.run()


if __name__ == "__main__":
    main()

