# Cumplimiento regulatorio — BioCoin Castuo (UE)

## REACH / ISO 10993 (biocompatibilidad)

- **REACH:** inventario de sustancias por capa (PHB, PLA, fibra cáñamo, SiO₂ encapsulante, nanocerámica PVD); SDS y registro/pre-registro según tonelaje anual.
- **ISO 10993 (screening):** contacto prolongado limitado (objeto manipulable, no implante); serie de citotoxicidad/irritación según uso previsto “coleccionable / keycard”.
- **Documentación:** Dossier técnico por lote (Lote 0000–9999) enlazado al **Manifest Canonical** on-chain.

## MiCA (Mercados de Criptoactivos UE)

- Clasificación orientativa: **activo referenciado** o **utilidad** según derechos reales del token (acceso TPV, eventos, no promesa de rendimiento).
- **Whitepaper / información mínima:** descripción del proyecto, riesgos, tecnología NFC/HSM, gobernanza DAO para cláusula de expansión.
- **Reservas y buyback:** el **Bio-Reserve Fund** (`bioReserveFund`, típ. **10 %** de `reserveRateBps`) acumula liquidez on-chain para **retirada/recompra** cuando el **EvidenceScore** cae bajo umbral (degradación física, piezo roto, incoherencia NIR). Debe documentarse como mecanismo de **circularidad y disciplina de mercado**, no como promesa de valor.

## Soberanía de evidencias

- **IPFS + WORM en soberanía ES/PT (UE):** anclajes de `Manifest Canonical` y `EvidenceHash` en nodos y almacenamiento **WORM** bajo jurisdicción ibérica/UE; evita dependencia operativa de infra fuera de marco europeo de datos y prueba.
- **HSM federado:** firmas de oráculo alineadas con política de custodia **Shamir 3/5** (tres de cinco fragmentos para operación crítica).

## Forense ISO 17025

- **Slot Jara:** procedimiento de cadena de custodia para extracción de taggant en disputa; laboratorio acreditado emite informe vinculado al `Serial_ID`.

---

*No constituye asesoramiento legal; revisión por abogado MiCA/REACH obligatoria antes de emisión.*
