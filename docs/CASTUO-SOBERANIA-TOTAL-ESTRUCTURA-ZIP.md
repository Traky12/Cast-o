# Estructura ZIP «Soberanía Total» v5.PRO+ — Mapa al repositorio CASTUO

El paquete **CASTUO_Soberania_Total_v5_PRO.zip** (visión de entrega industrial) se **mapea** al código y documentación **abiertos** de este repositorio. No se incluyen binarios pesados (LoRA, CAD, PDFs propietarios) en Git; sí la **ruta lógica** y el **ADN digital** documentado.

```
CASTUO_Soberania_Total_v5_PRO.zip
├── README_MAESTRO.md              → docs/README_MAESTRO.md (este repo)
├── 01_Hardware_Soberano_RISCV/
│   ├── Agent5PRO_Carcasa_L7.stp   → [entrega CAD / CERN-OHL fuera de Git]
│   ├── Dron_Hibrido_Jara.stp
│   ├── BOM_Hardware_Abierto.xlsx
│   └── Licencia_CERN_OHL_S.txt
├── 02_Inteligencia_IA_Soberana/
│   ├── Mistral8x7B_Rural_LoRA.bin → [artefacto entrenamiento / no en repo]
│   ├── Agente_AutoGen_Orquestador.py → backend/routers/orchestrator.py + agents/
│   └── VectorDB_Normativas_UE.json   → docs/ + RAG (extensible)
├── 03_Optimizador_Cuantico_QAOA/
│   ├── qaoa_optimizer_v5.py       → backend/agri_sense/quantum_optimizer.py
│   ├── Castuo_Quadratic_Program.lp→ [export LP opcional desde QuadraticProgram]
│   └── IBMQ_Premium_Connector.pem → [credenciales locales, nunca en Git]
├── 04_Blockchain_BioCoin_ERC1400/
│   ├── BioCoinCastuo.sol          → [contrato / repositorio smart-contracts aparte]
│   ├── Chaincode_PBFT_Soberano.go
│   └── Kyber1024_HSM_Integrator.js → backend/security/pq_crypto.py (referencia PQC)
├── 05_Gemelo_Digital_3D/
│   ├── DigitalTwin_Orchestrator.unity → [Unity / fuera de core backend]
│   ├── Material_Degradation_Model.py    → [extensión futura; ver CATALOGO aleaciones]
│   └── AnexoC_JaraPlot.yaml           → docs/fiware/AnexoC_JaraPlot.yaml
├── 06_BioGrid_Energia_Autonoma/
│   ├── Perovskita_Panel_Specs.pdf  → docs (especificaciones adjuntas fuera de Git)
│   └── Grafeno_Battery_Management.py → sinergia con system_orchestrator + quantum
└── 07_Certificaciones_y_Legal/
    ├── Certificado_UNE_216701_Stub.pdf → plantillas docs/
    ├── Sello_Soberania_Tecnologica_5PRO.png
    └── Cumplimiento_RGPD_MiCA.pdf      → docs/SOBERANIA-TECNOLOGICA.md
```

## Estado de viabilidad

| Pilar | Estado en repo |
|-------|----------------|
| Hardware abierto | Documentado; CAD/BOM en canal de hardware CERN-OHL |
| IA soberana | Orquestador Mistral + rutas Castuo |
| QAOA BioGrid | Implementado híbrido + `biogrid_5pro` |
| Blockchain / MiCA | Documentación; contratos en capa aparte |
| Gemelo / FIWARE | YAML NGSI-LD parcela Jara |
| Certificación UNE / legal | `ACUERDO-COOPERACION-CTAEX-CASTUO.md`, UNE en federated |

---

*CASTUO 5.PRO: ADN digital de la bioeconomía soberana — listo para despliegue europeo.*
