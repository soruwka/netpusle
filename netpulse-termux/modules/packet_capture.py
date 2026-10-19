#!/usr/bin/env python3
"""Packet Capture Module — NetPulse (your own traffic only)"""

import threading
from datetime import datetime
from typing import Callable, Dict, Optional

try:
    from scapy.all import sniff, IP, IPv6, TCP, UDP, ICMP, ARP, DNS
    SCAPY_OK = True
except ImportError:
    SCAPY_OK = False

# Known port → protocol name
_PORT_MAP: Dict[int, str] = {
    20: "FTP-data", 21: "FTP", 22: "SSH", 23: "Telnet",
    25: "SMTP", 53: "DNS", 67: "DHCP", 68: "DHCP",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    465: "SMTPS", 587: "SMTP-TLS", 993: "IMAPS", 995: "POP3S",
    3306: "MySQL", 3389: "RDP", 5432: "Postgres",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt",
}


class PacketCapture:
    def __init__(self):
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start_capture(
        self,
        callback: Callable[[Dict], None],
        bpf_filter: str = "",
        interface: Optional[str] = None,
    ) -> None:
        if not SCAPY_OK:
            callback({
                "time": datetime.now().strftime("%H:%M:%S"),
                "protocol": "ERROR",
                "src": "—", "dst": "—", "length": 0,
                "info": "scapy not installed  (pip install scapy)",
            })
            return

        self._stop.clear()

        def _run() -> None:
            def _handler(pkt) -> None:
                if self._stop.is_set():
                    return
                parsed = self._parse(pkt)
                if parsed:
                    callback(parsed)

            try:
                sniff(
                    filter=bpf_filter or None,
                    iface=interface,
                    prn=_handler,
                    store=False,
                    stop_filter=lambda _: self._stop.is_set(),
                )
            except Exception:
                pass

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop_capture(self) -> None:
        self._stop.set()

    # ── packet parser ─────────────────────────────────────────────

    def _parse(self, pkt) -> Optional[Dict]:
        try:
            base = {
                "time":     datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "protocol": "Other",
                "src":      "?",
                "dst":      "?",
                "length":   len(pkt),
                "info":     "",
            }

            # ── ARP ──
            if ARP in pkt:
                base.update(
                    protocol="ARP",
                    src=pkt[ARP].psrc,
                    dst=pkt[ARP].pdst,
                    info="ARP Request" if pkt[ARP].op == 1 else "ARP Reply",
                )
                return base

            # ── IPv4 ──
            if IP in pkt:
                base["src"] = pkt[IP].src
                base["dst"] = pkt[IP].dst

                if TCP in pkt:
                    sp, dp = pkt[TCP].sport, pkt[TCP].dport
                    flags = str(pkt[TCP].flags)
                    proto = _PORT_MAP.get(dp) or _PORT_MAP.get(sp) or "TCP"
                    base.update(
                        protocol=proto,
                        info=f"{sp} → {dp}  flags=[{flags}]",
                    )

                elif UDP in pkt:
                    sp, dp = pkt[UDP].sport, pkt[UDP].dport

                    if DNS in pkt and pkt[DNS].qr == 0:
                        try:
                            qname = pkt[DNS].qd.qname.decode("utf-8", "replace").rstrip(".")
                        except Exception:
                            qname = "?"
                        base.update(protocol="DNS", info=f"Query: {qname}")
                    else:
                        proto = _PORT_MAP.get(dp) or _PORT_MAP.get(sp) or "UDP"
                        base.update(protocol=proto, info=f"{sp} → {dp}")

                elif ICMP in pkt:
                    icmp_names = {
                        0: "Echo Reply", 3: "Dest Unreachable",
                        8: "Echo Request", 11: "TTL Exceeded",
                    }
                    base.update(
                        protocol="ICMP",
                        info=icmp_names.get(pkt[ICMP].type, f"Type {pkt[ICMP].type}"),
                    )

                return base

            return None  # skip non-IP, non-ARP
        except Exception:
            return None
