#!/usr/bin/env python3
"""System Log Viewer Module — NetPulse"""

import subprocess
from typing import List


_WIFI_KEYWORDS  = {"wifi", "wlan", "wpa", "networkmanager", "wireless", "802.11"}
_NET_KEYWORDS   = {"eth", "link", "dhcp", "dns", "network", "ip ", "route", "inet"}
_ERROR_KEYWORDS = {"error", "fail", "critical", "panic", "oops"}


class LogViewer:
    """Read and format system log entries relevant to WiFi / networking."""

    # ── public ────────────────────────────────────────────────────

    def get_wifi_logs(self) -> List[str]:
        entries = self._journalctl(
            ["-u", "NetworkManager", "-u", "wpa_supplicant",
             "-n", "300", "--no-pager", "--output", "short-iso"]
        )
        if not entries:
            entries = self._grep_syslog(_WIFI_KEYWORDS)
        if not entries:
            entries = ["[dim]No WiFi logs found. Run as root for full access.[/dim]"]
        return entries

    def get_network_logs(self) -> List[str]:
        entries = self._journalctl(
            ["-u", "networking", "-u", "NetworkManager",
             "-n", "300", "--no-pager", "--output", "short-iso"]
        )
        if not entries:
            entries = self._dmesg(_NET_KEYWORDS)
        if not entries:
            entries = ["[dim]No network logs found.[/dim]"]
        return entries

    def get_error_logs(self) -> List[str]:
        entries = self._journalctl(
            ["-p", "err", "-n", "300", "--no-pager", "--output", "short-iso"]
        )
        if not entries:
            entries = ["[dim]No error logs found.[/dim]"]
        return entries

    # ── private helpers ───────────────────────────────────────────

    def _journalctl(self, args: List[str]) -> List[str]:
        try:
            out = subprocess.run(
                ["journalctl"] + args,
                capture_output=True, text=True, timeout=10,
            )
            if out.returncode != 0:
                return []
            return [self._fmt(line) for line in out.stdout.splitlines() if line.strip()]
        except Exception:
            return []

    def _grep_syslog(self, keywords: set) -> List[str]:
        entries: List[str] = []
        pattern = r"\|".join(keywords)
        for path in ("/var/log/syslog", "/var/log/messages"):
            try:
                out = subprocess.run(
                    ["grep", "-i", pattern, path],
                    capture_output=True, text=True, timeout=10,
                )
                if out.returncode == 0:
                    for line in out.stdout.splitlines()[-300:]:
                        entries.append(self._fmt(line))
                    break
            except Exception:
                continue
        return entries

    def _dmesg(self, keywords: set) -> List[str]:
        entries: List[str] = []
        try:
            out = subprocess.run(
                ["dmesg", "--color=never"],
                capture_output=True, text=True, timeout=10,
            )
            for line in out.stdout.splitlines():
                if any(kw in line.lower() for kw in keywords):
                    entries.append(self._fmt(line))
        except Exception:
            pass
        return entries

    @staticmethod
    def _fmt(line: str) -> str:
        """Colorize a log line based on severity keywords."""
        # Escape Rich markup chars that appear in log text
        safe = line.replace("[", "\\[")

        low = line.lower()
        if any(k in low for k in ("error", "failed", "critical", "panic")):
            return f"[red]{safe}[/red]"
        if any(k in low for k in ("warn", "warning")):
            return f"[yellow]{safe}[/yellow]"
        if any(k in low for k in ("connect", "associated", "acquired", "success", "up")):
            return f"[green]{safe}[/green]"
        return f"[dim]{safe}[/dim]"

