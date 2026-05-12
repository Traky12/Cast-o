"""
Fachada Sabionda: OmegaCore (estructura + métricas solo vía env) + HolobrainClient (HTTP real).
Tono extremeño en docs/ai/tonos_extremeños.json — sin KPIs hardcodeados.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_HOLO_DIR = Path(__file__).resolve().parent.parent / "holo"
if str(_HOLO_DIR) not in sys.path:
    sys.path.insert(0, str(_HOLO_DIR))

from holobrain_client import HolobrainClient  # noqa: E402
from scripts.omega.omega_core import OmegaCore  # noqa: E402

_TONOS_PATH = _REPO_ROOT / "docs" / "ai" / "tonos_extremeños.json"


def _load_templates() -> dict[str, str]:
    if not _TONOS_PATH.is_file():
        raise FileNotFoundError(
            f"Falta {_TONOS_PATH} (guion de tono documentado, sin métricas fijas)."
        )
    with open(_TONOS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("tonos_extremeños.json debe ser un objeto JSON en la raíz.")
    return {str(k): str(v) for k, v in raw.items()}


def _yield_display(y: str | None) -> str:
    if not y:
        return "sin medición (definir CASTUO_MEASURED_YIELD_PCT o tu API)"
    return y if y.endswith("%") else f"{y}%"


def _delta_display(d: str | None) -> str:
    if not d:
        return "N/D (definir CASTUO_MEASURED_VS_UE_DELTA_PCT si aplica)"
    return d if d.endswith("%") else f"{d}%"


def _carbon_display(c: str | None) -> str:
    if not c:
        return "sin medición (definir CASTUO_MEASURED_CARBON_KG)"
    return f"{c} kg CO₂e"


class SabiondaOmegaFacade:
    def __init__(
        self,
        *,
        core: OmegaCore | None = None,
        holobrain: HolobrainClient | None = None,
        templates: dict[str, str] | None = None,
    ) -> None:
        self.core = core if core is not None else OmegaCore()
        self.holobrain = holobrain if holobrain is not None else HolobrainClient()
        self.templates = templates if templates is not None else _load_templates()

    def greet(self, user_name: str, *, region: str | None = None) -> str:
        import os

        reg = (region or os.environ.get("CASTUO_REGION", "") or "Extremadura").strip()
        st = self.core.get_system_status()
        tpl = self.templates.get("greet", "")
        return tpl.format(
            user=user_name.strip() or "explorador",
            region=reg,
            security=str(st.get("security_barriers", "")),
            sustainability=_carbon_display(st.get("carbon_kg")),
            **{"yield": _yield_display(st.get("yield_pct"))},
        )

    def show_status(
        self,
        *,
        holobrain_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        st = self.core.get_system_status()
        tpl = self.templates.get("status", "")
        message = tpl.format(
            delta=_delta_display(st.get("vs_ue_delta_pct")),
            security=str(st.get("security_barriers", "")),
            sustainability=_carbon_display(st.get("carbon_kg")),
            **{"yield": _yield_display(st.get("yield_pct"))},
        )
        out: dict[str, Any] = {
            "message": message,
            "data": st,
            "holobrain": None,
        }
        if holobrain_metrics is not None:
            out["holobrain"] = self.push_holobrain(holobrain_metrics)
        else:
            out["holobrain"] = {
                "skipped": True,
                "reason": "Pasa holobrain_metrics={plant_status, ph, ec, ...} para POST al webhook n8n.",
            }
        return out

    def push_holobrain(self, metrics: dict[str, Any]) -> dict[str, Any]:
        try:
            r = self.holobrain.send(metrics)
            body: Any
            try:
                body = r.json()
            except json.JSONDecodeError:
                body = r.text[:2000]
            return {
                "ok": r.ok,
                "status_code": r.status_code,
                "webhook_url": self.holobrain.webhook_url(),
                "body": body,
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "webhook_url": self.holobrain.webhook_url()}

    def error_voice(self, user_name: str, error_code: str, tool: str = "logs / n8n / gateway") -> str:
        tpl = self.templates.get("error", "")
        return tpl.format(
            user=user_name.strip() or "explorador",
            error_code=error_code,
            tool=tool,
        )


if __name__ == "__main__":
    def _out(s: str) -> None:
        sys.stdout.buffer.write(s.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")

    f = SabiondaOmegaFacade()
    _out(f.greet("Tester"))
    _out("---")
    _out(json.dumps(f.show_status(), indent=2, ensure_ascii=False))
