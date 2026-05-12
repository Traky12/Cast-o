"""
Gemelo digital BioCoin Castuo — EvidenceScore, LCA CO2, serie Premium 10k.

Streamlit: tabla de monedas simuladas, mapa de impacto, guía NFC + colorimetría.
"""
from __future__ import annotations

import os
import random

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="BioCoin Castuo — Evidence & LCA", layout="wide")
st.title("BioCoin Castuo — Gemelo digital (Serie Premium)")
st.caption(
    "EvidenceScore (NIR + ALD color) · piezo tamper-evident · LCA cáñamo · capa PVD/ALD protege Chlorella (app móvil)"
)

SERIE = 10_000
random.seed(42)
rows = []
for i in range(1, min(501, SERIE + 1)):
    piezo_ok = random.random() > 0.02
    ald_coh = 0.88 + random.random() * 0.12
    nir_m = 0.82 + random.random() * 0.17
    if not piezo_ok:
        ev_pct = 0.0
    else:
        ev_pct = min(100.0, (0.45 * nir_m + 0.35 * ald_coh + 0.2) * 100)
    lca = -0.8 - random.random() * 1.2
    rows.append(
        {
            "token_id": i,
            "evidence_score_pct": round(ev_pct, 2),
            "piezo_integrity": piezo_ok,
            "ald_coherence_pct": round(ald_coh * 100, 1),
            "lca_co2_kg": round(lca, 3),
            "serie": "GENESIS",
            "tinta_ok": ev_pct > 92,
        }
    )
df = pd.DataFrame(rows)

col1, col2 = st.columns(2)
with col1:
    st.subheader("EvidenceScore por moneda (muestra)")
    sel = st.slider("Umbral verde %", 80, 99, 90)
    df["estado"] = df["evidence_score_pct"].apply(lambda x: "alto" if x >= sel else "revisar")
    tampered = df[~df["piezo_integrity"]]
    if len(tampered) > 0:
        st.error(f"**Tamper piezo-resistivo:** {len(tampered)} moneda(s) con EvidenceScore anulado (posible extracción chip).")
    st.dataframe(df.head(50), use_container_width=True)
with col2:
    fig = go.Figure(go.Indicator(mode="gauge+number", value=float(df["evidence_score_pct"].mean()), domain={"x": [0, 1], "y": [0, 1]}, title={"text": "Media EvidenceScore %"}, gauge={"axis": {"range": [80, 100]}, "bar": {"color": "#1a5f2a"}}))
    fig.update_layout(height=220)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Mapa de impacto CO2 (LCA — semilla cáñamo → entrega)")
df_map = pd.DataFrame(
    {
        "etapa": ["Cultivo GNSS", "Fibra", "Moldeo PHB/PLA", "Logística", "Coleccionista"],
        "co2_kg": [-1.2, -0.3, 0.15, 0.08, 0.0],
    }
)
fig2 = px.bar(df_map, x="etapa", y="co2_kg", color="co2_kg", color_continuous_scale="RdYlGn", title="Huella acumulada (negativo = secuestro)")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("App móvil — flujo de confianza tripartita")
st.markdown(
    """
1. **NFC:** lectura Secure Element → nonce firmado vs `EvidenceHash` en HSM federado.
2. **Óptico:** activar UV/NIR; comparar espectro con firma de serie (tinta criptográfica).
3. **Forense:** slot Jara (ISO 17025) solo en disputa legal.
"""
)

st.markdown(
    """
- **Contrato:** `mintPriceWei=0` + timelock **48h** en precio (`scheduleMintPriceChange`) — anti flash governance.
- **Código:** `security_orchestrator.compute_evidence_hash` (NIR + geo cosecha ± piezo/ALD) · `mint_message.sign_mint_oracle`.
"""
)
st.info("Docs: `docs/biocoin/VINCULO-MATERIAL-DIGITAL.md` · `ORACLE-MINTING-FLOW.md`")
