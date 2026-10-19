#!/usr/bin/env python3
"""WiFi Information Module — NetPulse"""

import os
import re
import socket
import subprocess
from typing import Dict, List


class WiFiInfo:
    """Gather WiFi info using Linux system commands (iwconfig, nmcli, ip)."""

    # ── interfaces ───────────────────────────────────────────────

    def get_wireless_interfaces(self) -> List[str]:
        ifaces = []

        # Method 1: iwconfig stdout
        try:
            out = subprocess.run(
                ["iwconfig"], capture_output=True, text=True, timeout=5
            ).stdout
            for line in out.splitlines():
                if line and not line.startswith(" "):
                    iface = line.split()[0]
                    if "IEEE 802.11" in line or "ESSID" in line:
                        if iface not in ifaces:
                            ifaces.append(iface)
        except Exception:
            pass

        # Method 2: /sys/class/net/<iface>/wireless
        try:
            for iface in os.listdir("/sys/class/net"):
                if os.path.isdir(f"/sys/class/net/{iface}/wireless"):
                    if iface not in ifaces:
                        ifaces.append(iface)
        except Exception:
            pass

        return ifaces or ["wlan0"]

    # ── current connection ────────────────────────────────────────

    def get_connected_info(self) -> Dict:
        info: Dict = {
            "interface": "N/A", "ssid": "Not Connected", "bssid": "N/A",
            "ip": "N/A", "gateway": "N/A", "dns": "N/A",
            "signal": "N/A", "quality": "N/A", "frequency": "N/A",
            "channel": "N/A", "security": "N/A", "mode": "N/A", "speed": "N/A",
        }

        ifaces = self.get_wireless_interfaces()

        # ── iwconfig ──
        for iface in ifaces:
            try:
                out = subprocess.run(
                    ["iwconfig", iface], capture_output=True, text=True, timeout=5
                ).stdout

                if "ESSID:" not in out:
                    continue

                info["interface"] = iface

                m = re.search(r'ESSID:"([^"]*)"', out)
                if m:
                    info["ssid"] = m.group(1) or "Hidden"

                m = re.search(r"Access Point: ([0-9A-Fa-f:]{17})", out)
                if m:
                    info["bssid"] = m.group(1)

                m = re.search(r"Signal level=(-?\d+) dBm", out)
                if m:
                    dbm = int(m.group(1))
                    info["signal"] = f"{dbm} dBm"
                    q = max(0, min(100, 2 * (dbm + 100)))
                    info["quality"] = f"{q}%"

                m = re.search(r"Frequency:(\d+\.\d+) GHz.*?Channel (\d+)", out)
                if m:
                    info["frequency"] = f"{m.group(1)} GHz"
                    info["channel"] = m.group(2)

                m = re.search(r"Mode:(\S+)", out)
                if m:
                    info["mode"] = m.group(1)

                m = re.search(r"Bit Rate=(\S+ \S+)", out)
                if m:
                    info["speed"] = m.group(1)

                break
            except Exception:
                continue

        iface = info["interface"] if info["interface"] != "N/A" else ifaces[0]

        # ── IP address ──
        try:
            out = subprocess.run(
                ["ip", "addr", "show", iface], capture_output=True, text=True, timeout=5
            ).stdout
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", out)
            if m:
                info["ip"] = m.group(1)
        except Exception:
            pass

        # ── default gateway ──
        try:
            out = subprocess.run(
                ["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5
            ).stdout
            m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", out)
            if m:
                info["gateway"] = m.group(1)
        except Exception:
            pass

        # ── DNS servers ──
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

        # ── security type via nmcli ──
        try:
            out = subprocess.run(
                ["nmcli", "-t", "-f", "802-11-wireless-security.key-mgmt",
                 "connection", "show", info["ssid"]],
                capture_output=True, text=True, timeout=5,
            ).stdout.lower()
            if "wpa-psk" in out:
                info["security"] = "WPA2-PSK"
            elif "wpa-eap" in out:
                info["security"] = "WPA2-EAP"
            elif "sae" in out:
                info["security"] = "WPA3-SAE"
            elif "none" in out:
                info["security"] = "Open"
        except Exception:
            pass

        return info

    # ── nearby scan ───────────────────────────────────────────────

    def scan_nearby(self) -> List[Dict]:
        networks = []
        iface = self.get_wireless_interfaces()[0]

        # ── iwlist scan ──
        try:
            out = subprocess.run(
                ["sudo", "iwlist", iface, "scan"],
                capture_output=True, text=True, timeout=20,
            ).stdout

            for cell in out.split("Cell ")[1:]:
                n: Dict = {
                    "ssid": "Hidden", "bssid": "N/A",
                    "signal": "N/A",  "quality": "N/A",
                    "frequency": "N/A", "channel": "N/A",
                    "security": "Open",
                }

                m = re.search(r"Address: ([0-9A-Fa-f:]{17})", cell)
                if m:
                    n["bssid"] = m.group(1)

                m = re.search(r'ESSID:"([^"]*)"', cell)
                if m:
                    n["ssid"] = m.group(1) or "Hidden"

                m = re.search(r"Signal level=(-?\d+) dBm", cell)
                if m:
                    dbm = int(m.group(1))
                    n["signal"] = f"{dbm} dBm"
                    n["quality"] = f"{max(0, min(100, 2*(dbm+100)))}%"

                m = re.search(r"Quality=(\d+)/(\d+)", cell)
                if m and n["quality"] == "N/A":
                    n["quality"] = f"{int(int(m.group(1))/int(m.group(2))*100)}%"

                m = re.search(r"Frequency:(\d+\.\d+) GHz.*?Channel (\d+)", cell)
                if m:
                    n["frequency"] = f"{m.group(1)} GHz"
                    n["channel"] = m.group(2)

                if "WPA2" in cell:
                    n["security"] = "WPA2"
                elif "WPA" in cell:
                    n["security"] = "WPA"
                elif "WEP" in cell:
                    n["security"] = "WEP"

                if n["bssid"] != "N/A":
                    networks.append(n)

            return networks
        except Exception:
            pass

        # ── nmcli fallback ──
        try:
            out = subprocess.run(
                ["nmcli", "--terse", "-f", "SSID,BSSID,SIGNAL,CHAN,FREQ,SECURITY",
                 "dev", "wifi", "list"],
                capture_output=True, text=True, timeout=15,
            ).stdout

            for line in out.strip().splitlines():
                parts = line.split(":")
                if len(parts) < 5:
                    continue
                ssid     = parts[0]
                bssid    = ":".join(parts[1:7])
                signal   = parts[7]  if len(parts) > 7  else "N/A"
                channel  = parts[8]  if len(parts) > 8  else "N/A"
                freq     = parts[9]  if len(parts) > 9  else "N/A"
                security = parts[10] if len(parts) > 10 else "Open"

                networks.append({
                    "ssid": ssid or "Hidden",
                    "bssid": bssid,
                    "signal": f"{signal} dBm",
                    "quality": f"{signal}%",
                    "channel": channel,
                    "frequency": freq,
                    "security": security or "Open",
                })
        except Exception:
            pass

        return networks
