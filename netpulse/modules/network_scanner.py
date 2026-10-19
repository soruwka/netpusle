#!/usr/bin/env python3
"""Network Scanner Module — NetPulse (ARP scan on your own LAN)"""

import re
import socket
import subprocess
from typing import Dict, List

try:
    from scapy.all import ARP, Ether, srp
    SCAPY_OK = True
except ImportError:
    SCAPY_OK = False


class NetworkScanner:
    """ARP-based LAN host discovery (requires root)."""

    def arp_scan(self, network: str) -> List[Dict]:
        """
        Send ARP requests to every host in `network` (e.g. 192.168.1.0/24)
        and return a list of responding devices.
        """
        devices: List[Dict] = []

        # ── scapy ARP scan ──
        if SCAPY_OK:
            try:
                pkt    = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
                result = srp(pkt, timeout=2, verbose=False)[0]
                for _, received in result:
                    ip  = received.psrc
                    mac = received.hwsrc
                    devices.append({
                        "ip":       ip,
                        "mac":      mac,
                        "hostname": self._resolve(ip),
                    })
                devices.sort(key=lambda x: list(map(int, x["ip"].split("."))))
                return devices
            except Exception:
                pass

        # ── nmap fallback ──
        try:
            out = subprocess.run(
                ["nmap", "-sn", network, "-oG", "-"],
                capture_output=True, text=True, timeout=30,
            ).stdout
            for line in out.splitlines():
                if "Host:" in line and "Status: Up" in line:
                    ip_m   = re.search(r"Host: (\d+\.\d+\.\d+\.\d+)", line)
                    name_m = re.search(r"\(([^)]+)\)", line)
                    if ip_m:
                        ip = ip_m.group(1)
                        devices.append({
                            "ip":       ip,
                            "mac":      "N/A",
                            "hostname": name_m.group(1) if name_m else self._resolve(ip),
                        })
        except Exception:
            pass

        return devices

    @staticmethod
    def _resolve(ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return "Unknown"

