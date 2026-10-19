#!/usr/bin/env python3
"""WiFi Information Module — NetPulse (Termux/Android edition)

Uses termux-api commands instead of iwconfig/nmcli.
Install: pkg install termux-api  +  Termux:API app from F-Droid.
"""

import json
import re
import subprocess
from typing import Dict, List


def _run(cmd: List[str], timeout: int = 8) -> str:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        ).stdout.strip()
    except Exception:
        return ""


class WiFiInfo:
    """Gather WiFi info via termux-api on Android."""

    # ── interfaces ────────────────────────────────────────────────

    def get_wireless_interfaces(self) -> List[str]:
        ifaces = []
        try:
            import os
            for iface in os.listdir("/sys/class/net"):
                if os.path.isdir(f"/sys/class/net/{iface}/wireless"):
                    ifaces.append(iface)
        except Exception:
            pass

        if not ifaces:
            out = _run(["ip", "link"])
            for line in out.splitlines():
                m = re.match(r"\d+: (\w+):", line)
                if m and m.group(1) not in ("lo", "dummy0"):
                    ifaces.append(m.group(1))

        return ifaces or ["wlan0"]

    # ── current connection ────────────────────────────────────────

    def get_connected_info(self) -> Dict:
        info: Dict = {
            "interface": "wlan0",
            "ssid":      "Not Connected",
            "bssid":     "N/A",
            "ip":        "N/A",
            "gateway":   "N/A",
            "dns":       "N/A",
            "signal":    "N/A",
            "quality":   "N/A",
            "frequency": "N/A",
            "channel":   "N/A",
            "security":  "N/A",
            "mode":      "Managed",
            "speed":     "N/A",
        }

        raw = _run(["termux-wifi-connectioninfo"])
        if raw:
            try:
                d = json.loads(raw)
                info["ssid"]      = d.get("ssid", "N/A").strip('"')
                info["bssid"]     = d.get("bssid", "N/A")
                info["ip"]        = d.get("ip", "N/A")
                info["frequency"] = f"{d.get('frequency_mhz', '?')} MHz"

                freq_mhz = d.get("frequency_mhz", 0)
                if freq_mhz:
                    info["channel"] = str(self._freq_to_channel(freq_mhz))

                rssi = d.get("rssi", None)
                if rssi is not None:
                    info["signal"]  = f"{rssi} dBm"
                    info["quality"] = f"{max(0, min(100, 2*(rssi+100)))}%"

                speed = d.get("link_speed_mbps", None)
                if speed is not None:
                    info["speed"] = f"{speed} Mb/s"

                if d.get("network_id") is not None:
                    info["security"] = "WPA2"
            except (json.JSONDecodeError, KeyError):
                pass

        # ── gateway ──
        out = _run(["ip", "route", "show", "default"])
        m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", out)
        if m:
            info["gateway"] = m.group(1)

        # ── DNS ──
        try:
            servers = []
            with open("/etc/resolv.conf") as f:
                for line in f:
                    if line.startswith("nameserver"):
                        servers.append(line.split()[1])
            if servers:
                info["dns"] = ", ".join(servers[:3])
        except Exception:
            pass

        return info

    # ── nearby scan ───────────────────────────────────────────────

    def scan_nearby(self) -> List[Dict]:
        raw = _run(["termux-wifi-scaninfo"], timeout=15)
        if not raw:
            return [{
                "ssid": "termux-api not installed / no permission",
                "bssid": "N/A", "signal": "N/A", "quality": "N/A",
                "channel": "N/A", "frequency": "N/A", "security": "N/A",
            }]

        networks: List[Dict] = []
        try:
            aps = json.loads(raw)
            for ap in aps:
                ssid  = ap.get("ssid", "Hidden").strip('"') or "Hidden"
                bssid = ap.get("bssid", "N/A")
                rssi  = ap.get("rssi", None)
                freq  = ap.get("frequency_mhz", 0)
                caps  = ap.get("capabilities", "")

                signal  = f"{rssi} dBm" if rssi is not None else "N/A"
                quality = f"{max(0, min(100, 2*(rssi+100)))}%" if rssi is not None else "N/A"

                security = "Open"
                if "WPA2" in caps:
                    security = "WPA2"
                elif "WPA" in caps:
                    security = "WPA"
                elif "WEP" in caps:
                    security = "WEP"

                networks.append({
                    "ssid":      ssid,
                    "bssid":     bssid,
                    "signal":    signal,
                    "quality":   quality,
                    "channel":   str(self._freq_to_channel(freq)) if freq else "N/A",
                    "frequency": f"{freq} MHz" if freq else "N/A",
                    "security":  security,
                })

            networks.sort(
                key=lambda n: int(n["signal"].split()[0]) if "dBm" in n["signal"] else -999,
                reverse=True,
            )
        except (json.JSONDecodeError, KeyError):
            pass

        return networks

    # ── helpers ───────────────────────────────────────────────────

    @staticmethod
    def _freq_to_channel(freq_mhz: int) -> int:
        if freq_mhz == 2484:
            return 14
        if 2412 <= freq_mhz <= 2472:
            return (freq_mhz - 2407) // 5
        if 5170 <= freq_mhz <= 5825:
            return (freq_mhz - 5000) // 5
        if 6000 <= freq_mhz <= 7125:
            return (freq_mhz - 5950) // 5
        return 0

