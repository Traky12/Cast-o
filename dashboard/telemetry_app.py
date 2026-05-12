"""
Dashboard de telemetría 7D — Castuo-System AGRI-SENSE-CORE.

Streamlit + Plotly: energía híbrida, panel químico (pH/N/K), estado hídrico y ozono,
mapa térmico subterráneo, auditoría e intervención manual.
Conectado a system_orchestrator.py vía API.
"""
from __future__ import annotations

import os
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import httpx
except ImportError:
    httpx = None

API_BASE = os.getenv("CASTUO_API_BASE", "http://localhost:8000")
STREAMLIT_TITLE = "Castuo-System 5.PRO — Telemetría 7D + Quantum BioGrid"


def _api_get(path: str) -> dict[str, Any] | list[Any]:
    if httpx is None:
        return _stub_data(path)
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{API_BASE.rstrip('/')}{path}")
            r.raise_for_status()
            return r.json()
    except Exception:
        return _stub_data(path)


def _api_post(path: str, json: dict[str, Any]) -> dict[str, Any]:
    if httpx is None:
        return {"audit_id": "AUD-stub", "action": json.get("action", "")}
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.post(f"{API_BASE.rstrip('/')}{path}", json=json)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"error": str(e)}


def _stub_data(path: str) -> dict[str, Any] | list[Any]:
    if "state" in path:
        return {
            "npk_valve_closed": False,
            "heat_pump_flow_factor": 1.0,
            "ozone_injection_enabled": True,
            "cop_geothermal": 4.2,
            "last_ground_temp_c": 17.5,
            "irrigation_demand_factor": 0.9,
            "root_cause_last": "Ciclo de control en espera de sensores.",
            "quantum_confidence_score": 92.5,
            "energy_alloc_ro_kw": 4.2,
            "energy_alloc_geo_kw": 3.8,
            "energy_alloc_o3_kw": 1.5,
            "quantum_backend_last": "classical_enumeration",
        }
    if "audit" in path:
        return [
            {"audit_id": "AUD-demo1", "event": "control_cycle", "severity": "info", "root_cause": "Demo"},
            {"audit_id": "AUD-demo2", "event": "fail_safe_npk_valve_closed", "severity": "critical", "root_cause": "Sensor O3 bajo."},
        ]
    return {}


def _severity_color(severity: str) -> str:
    return {"critical": "#c0392b", "warning": "#f39c12", "info": "#3498db"}.get(severity, "#95a5a6")


st.set_page_config(page_title=STREAMLIT_TITLE, layout="wide")
st.title(STREAMLIT_TITLE)
st.caption("Conectado a system_orchestrator — Bucle de retroalimentación + QAOA BioGrid 5.PRO+")

qconf = float(state.get("quantum_confidence_score") or 0)
col_q, col_q2 = st.columns(2)
with col_q:
    st.metric(
        "Quantum Confidence Score",
        f"{qconf:.1f} %",
        help=">90%: minima entropia operativa; fluctuacion solar >10% dispara recalculo QAOA.",
    )
    if qconf >= 90:
        st.success("Estado de maxima eficiencia (QAOA / enumeracion clasica).")
    elif qconf >= 70:
        st.warning("Revisar irradiancia o pH para subir confianza cuantica.")
    else:
        st.error("Baja confianza: verificar sensores y techo Perovskita+Biogas.")
with col_q2:
    st.write("**Asignacion energia BioGrid (kW)**")
    st.write(
        f"RO {state.get('energy_alloc_ro_kw', 0):.2f} | "
        f"Geo {state.get('energy_alloc_geo_kw', 0):.2f} | "
        f"O3 {state.get('energy_alloc_o3_kw', 0):.2f}"
    )
    st.caption(f"Backend: {state.get('quantum_backend_last', '—')}")

state = _api_get("/api/agri-sense/state")
if not isinstance(state, dict):
    state = {}

col_energy, col_chem, col_water = st.columns(3)

with col_energy:
    st.subheader("Energía híbrida")
    solar_kw = state.get("irrigation_demand_factor", 1.0) * 5.0
    geo_kw = 2.5 if state.get("cop_geothermal") else 0
    ro_kw = 3.0
    fig_energy = go.Figure(
        data=[
            go.Bar(name="Solar (UNE)", x=["Curva"], y=[solar_kw], marker_color="#f1c40f"),
            go.Bar(name="Bomba calor geot.", x=["Curva"], y=[geo_kw], marker_color="#27ae60"),
            go.Bar(name="Ósmosis", x=["Curva"], y=[ro_kw], marker_color="#3498db"),
        ]
    )
    fig_energy.update_layout(barmode="group", height=220, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_energy, use_container_width=True)
    st.metric("COP geotérmico", state.get("cop_geothermal") or "—")

with col_chem:
    st.subheader("Panel químico (UltraPrecision)")
    ph_val = 6.8
    n_ppm = 45
    k_ppm = 120
    fig_ph = go.Figure(go.Indicator(mode="gauge+number", value=ph_val, domain=dict(x=[0, 1], y=[0, 1]),
        title=dict(text="pH"), number=dict(suffix=""),
        gauge=dict(axis=dict(range=[0, 14]), bar=dict(color="#2c3e50"),
            steps=[dict(range=[0, 5.5], color="#e74c3c"), dict(range=[5.5, 7.5], color="#27ae60"), dict(range=[7.5, 14], color="#e74c3c")],
            threshold=dict(line=dict(color="red", width=2), value=7.2))))
    fig_ph.update_layout(height=180, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_ph, use_container_width=True)
    st.metric("Nitrato (N) ppm", n_ppm)
    st.metric("Potasio (K) ppm", k_ppm)

with col_water:
    st.subheader("Estado hídrico y Ozono")
    st.metric("Flujo riego (factor demanda)", f"{state.get('irrigation_demand_factor', 1.0):.2f}")
    st.metric("Válvula NPK", "Cerrada" if state.get("npk_valve_closed") else "Abierta")
    st.metric("Inyección O₃", "ON" if state.get("ozone_injection_enabled") else "OFF")
    st.metric("Factor flujo bomba calor", f"{state.get('heat_pump_flow_factor', 1.0):.2f}")

st.subheader("Mapa de calor subterráneo (T suelo por profundidad)")
depths = [0, 2, 5, 10, 15, 20]
temps = [22.0, 19.0, 17.5, (state.get("last_ground_temp_c") or 16.0), 15.5, 15.0]
df_soil = pd.DataFrame({"profundidad_m": depths, "temperatura_C": temps})
fig_heat = px.line(df_soil, x="temperatura_C", y="profundidad_m",
    title="Temperatura del suelo por profundidad")
fig_heat.update_layout(yaxis=dict(autorange="reversed"), height=280)
st.plotly_chart(fig_heat, use_container_width=True)

st.subheader("Auditoría (últimos 10) — Código de colores por gravedad")
audit_list = _api_get("/api/agri-sense/audit?n=10")
if isinstance(audit_list, list) and audit_list:
    for row in audit_list:
        sid = row.get("audit_id", "")
        sev = row.get("severity", "info")
        rc = row.get("root_cause", "")
        st.markdown(f"<span style='background:{_severity_color(sev)};color:white;padding:2px 8px;border-radius:4px'>{sid}</span> {sev} — {rc[:80]}", unsafe_allow_html=True)
else:
    st.info("Sin eventos de auditoría o API no disponible.")

st.subheader("Intervención manual")
act = st.selectbox("Acción", ["force_ozone_cycle", "set_cop_geothermal", "set_geothermal_setpoint"], key="manual_act")
cop_val = st.number_input("COP (si aplica)", value=4.2, min_value=2.0, max_value=6.0, step=0.1) if act == "set_cop_geothermal" else None
temp_val = st.number_input("Setpoint T °C (si aplica)", value=18.0, min_value=10.0, max_value=25.0, step=0.5) if act == "set_geothermal_setpoint" else None
if st.button("Ejecutar"):
    body = {"action": act}
    if cop_val is not None:
        body["cop"] = cop_val
    if temp_val is not None:
        body["temp_c"] = temp_val
    out = _api_post("/api/agri-sense/manual-intervention", body)
    if "error" in out:
        st.error(out["error"])
    else:
        st.success(f"Audit: {out.get('audit_id', 'OK')}")
