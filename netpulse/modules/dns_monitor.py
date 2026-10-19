#!/usr/bin/env python3
"""DNS Monitor Module — NetPulse (your machine's queries only)"""

import threading
from datetime import datetime
from typing import Callable, Dict, Optional

try:
    from scapy.all import sniff, DNS, DNSQR, IP
    SCAPY_OK = True
except ImportError:
    SCAPY_OK = False

_QTYPES: Dict[int, str] = {
    1: "A", 2: "NS", 5: "CNAME", 6: "SOA", 12: "PTR",
    15: "MX", 16: "TXT", 28: "AAAA", 33: "SRV", 255: "ANY",
}


class DNSMonitor:
    def __init__(self):
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start_monitor(
        self,
        callback: Callable[[Dict], None],
        interface: Optional[str] = None,
    ) -> None:
        if not SCAPY_OK:
            callback({
                "time": datetime.now().strftime("%H:%M:%S"),
                "domain": "scapy not installed — pip install scapy",
                "type": "ERR",
                "src": "—",
            })
            return

        self._stop.clear()

        def _run() -> None:
            def _handler(pkt) -> None:
                if self._stop.is_set():
                    return
                entry = self._parse_dns(pkt)
                if entry:
                    callback(entry)

            try:
                sniff(
                    filter="udp port 53 or tcp port 53",
                    iface=interface,
                    prn=_handler,
                    store=False,
                    stop_filter=lambda _: self._stop.is_set(),
                )
            except Exception:
                pass

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop_monitor(self) -> None:
        self._stop.set()

    def _parse_dns(self, pkt) -> Optional[Dict]:
        try:
            if DNS not in pkt:
                return None

            dns = pkt[DNS]

            # Only outgoing queries (qr == 0)
            if dns.qr != 0 or dns.qd is None:
                return None

            qname = dns.qd.qname.decode("utf-8", "replace").rstrip(".")
            qtype = _QTYPES.get(dns.qd.qtype, str(dns.qd.qtype))
            src   = pkt[IP].src if IP in pkt else "?"

            return {
                "time":   datetime.now().strftime("%H:%M:%S"),
                "domain": qname,
                "type":   qtype,
                "src":    src,
            }
        except Exception:
            return None

