# CASTUO-SYSTEM™ | Europa: GS1 EPCIS y AI Act

Extensión del sistema para trazabilidad europea (GS1 EPCIS) y cumplimiento del AI Act (UE 2024/1689), manteniendo integración con BioCoin Castúo y Git.

---

## 1. GS1 EPCIS (trazabilidad europea)

### Requisitos

- Identificadores GS1 (GTIN, SSCC) para productos.
- Eventos EPCIS en cada paso (siembra, cosecha, transporte, etc.).
- Integración con BioCoin Castúo (TX hash en la extensión del evento).

### Formato de evento (ejemplo)

Ver **templates/legal/epcis_event.json**: eventTime, eventType (ObjectEvent), action, bizStep, disposition, epcList, extension (txHash, gitCommit, farmId / ipfsHash).

### Script de registro

```bash
pip install requests
python scripts/legal/epcis_event.py
```

En **scripts/legal/epcis_event.py** se envía el evento al API EPCIS (configurar endpoint y auth). Incluir en la extensión: `txHash`, `gitCommit`, `farmId` (y opcionalmente `ipfsHash`).

### Recomendaciones

- GS1 EPCIS como estándar de trazabilidad en cadena de suministro.
- Usar GTIN/SSCC en productos agrovoltaicos.
- Vincular cada documento legal a un TX hash de BioCoin.

---

## 2. AI Act (UE 2024/1689)

### Requisitos

- Transparencia de sistemas de IA (p. ej. modelos predictivos para riego).
- Registro en la base de datos europea de IA cuando aplique (riesgo Alto/Crítico).
- Documentación técnica accesible para autoridades.

### Plantilla de documentación de modelo de IA

Ver **templates/legal/ai_model.md**: nombre, versión, tipo, datos de entrenamiento, precisión, nivel de riesgo (AI Act), TX BioCoin, Git commit, descripción, métricas (precisión, recall, F1), cumplimiento GDPR y AI Act, auditoría.

### Script de generación

```bash
python scripts/legal/generar_ai_doc.py
```

Genera la documentación en Markdown, calcula hash y opcionalmente sube a IPFS; enlaza TX y commit para trazabilidad.

### Registro en base de datos UE de IA

Solo obligatorio para modelos de riesgo **Alto/Crítico**. En **scripts/legal/registrar_ue_ai.py** (skeleton) se prepara el payload (modelName, version, riskLevel, compliance, documentation con ipfsHash/gitCommit/txHash, provider). Endpoint y API key según normativa y portal oficial.

---

## 3. Recomendaciones Europa

- **GS1 EPCIS**: clave para trazabilidad en la cadena de suministro.
- **UE AI Database**: registro solo si los modelos tienen riesgo Alto/Crítico según AI Act.
- **Identificadores GS1**: GTIN, SSCC para productos agrovoltaicos y derivados.
- **BioCoin Castúo**: vincular cada documento y evento EPCIS a un TX hash; smart contracts para transacciones cuando aplique.

---

Para España (BOE, SII Facturae) ver **[LEGAL-SPAIN.md](LEGAL-SPAIN.md)**. Para la visión general de cumplimiento ver **[COMPLIANCE-LEGAL.md](COMPLIANCE-LEGAL.md)**.
