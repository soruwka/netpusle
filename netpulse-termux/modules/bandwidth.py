#!/usr/bin/env python3
"""Bandwidth Monitor Module — NetPulse"""

import time
from typing import Dict

import psutil


def _bytes_to_human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _speed_to_human(n: float) -> str:
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB/s"


class BandwidthMonitor:
    def __init__(self):
        self._prev_stats: Dict = {}
        self._prev_time: float = time.time()
        self._init_stats()

    def _init_stats(self) -> None:
        try:
            self._prev_stats = psutil.net_io_counters(pernic=True)
            self._prev_time  = time.time()
        except Exception:
            pass

    # ── all interfaces ────────────────────────────────────────────

    def get_all_interfaces(self) -> Dict[str, Dict]:
        result = {}
        try:
            stats = psutil.net_io_counters(pernic=True)
            for iface, d in stats.items():
                result[iface] = {
                    "bytes_sent":    d.bytes_sent,
                    "bytes_recv":    d.bytes_recv,
                    "bytes_sent_hr": _bytes_to_human(d.bytes_sent),
                    "bytes_recv_hr": _bytes_to_human(d.bytes_recv),
                    "packets_sent":  d.packets_sent,
                    "packets_recv":  d.packets_recv,
                    "errin":         d.errin,
                    "errout":        d.errout,
                    "dropin":        getattr(d, "dropin",  0),
                    "dropout":       getattr(d, "dropout", 0),
                }
        except Exception:
            pass
        return result

    # ── real-time speeds ─────────────────────────────────────────

    def get_realtime_speeds(self) -> Dict[str, str]:
        result = {"upload": "0 B/s", "download": "0 B/s", "interface": "N/A"}
        try:
            current = psutil.net_io_counters(pernic=True)
            now     = time.time()
            elapsed = now - self._prev_time

            if elapsed > 0 and self._prev_stats:
                best_iface  = None
                best_bytes  = -1

                for iface, d in current.items():
                    if iface not in self._prev_stats:
                        continue
                    prev  = self._prev_stats[iface]
                    delta = (d.bytes_sent - prev.bytes_sent +
                             d.bytes_recv - prev.bytes_recv)
                    if delta > best_bytes:
                        best_bytes = delta
                        best_iface = iface

                if best_iface:
                    prev = self._prev_stats[best_iface]
                    curr = current[best_iface]
                    up   = max(0, (curr.bytes_sent - prev.bytes_sent) / elapsed)
                    dn   = max(0, (curr.bytes_recv - prev.bytes_recv) / elapsed)
                    result = {
                        "upload":    _speed_to_human(up),
                        "download":  _speed_to_human(dn),
                        "interface": best_iface,
                    }

            self._prev_stats = current
            self._prev_time  = now
        except Exception:
            pass
        return result
