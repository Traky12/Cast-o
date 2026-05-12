# -*- coding: utf-8 -*-
"""Lectura centralizada de variables OT para edge, métricas y documentación."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List, Optional, Tuple


def _truthy(v: str) -> bool:
    return v.strip().lower() in {"1", "true", "yes", "on"}


def remote_energize_allowed() -> bool:
    raw = os.getenv("OT_REMOTE_ACTUATOR_WRITES", "")
    if raw.strip() == "":
        return True
    return _truthy(raw)


def killswitch_energize_blocked() -> bool:
    return _truthy(os.getenv("OT_ACTUATOR_KILLSWITCH", ""))


def parse_safe_windows_utc() -> List[Tuple[int, int]]:
    """
    Ventanas de mantenimiento en hora UTC [start, end) para energizar actuadores críticos.
    Formatos: "0-2,10-12" o "0 2,10 12" (coma separa ventanas).
    Vacío → sin restricción horaria adicional (solo roles / kill-switch).
    """
    raw = os.getenv("OT_SAFE_MODE_WINDOWS", "").strip()
    if not raw:
        return []
    out: List[Tuple[int, int]] = []
    for seg in raw.split(","):
        seg = seg.strip()
        if not seg:
            continue
        if "-" in seg and seg.count("-") == 1:
            a, b = seg.split("-", 1)
            out.append((int(a.strip()), int(b.strip())))
            continue
        parts = seg.split()
        if len(parts) >= 2:
            out.append((int(parts[0]), int(parts[1])))
    return out


def safe_mode_allows_critical_energize(now: Optional[datetime] = None) -> bool:
    windows = parse_safe_windows_utc()
    if not windows:
        return True
    if now is None:
        now = datetime.now(timezone.utc)
    h = now.astimezone(timezone.utc).hour
    for start, end in windows:
        if start <= h < end:
            return True
    return False
