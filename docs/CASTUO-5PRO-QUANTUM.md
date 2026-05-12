# CASTUO 5.PRO+ — Motor cuántico híbrido (BioGrid 2.0)

## Objetivo

Distribuir energía entre **ósmosis inversa (x_ro)**, **bomba de calor geotérmica (x_geo)** y **ciclo de ozono (x_o3)** bajo el techo:

**x_ro + x_geo + x_o3 ≤ P_perovskita + P_biogás**

(ver `backend/biogrid_5pro.py`: Chlorella PRO, purines → biogás; FV tipo perovskita.)

## Implementación

| Módulo | Rol |
|--------|-----|
| `backend/agri_sense/quantum_optimizer.py` | `CastuoQuantumOptimizer`, `QuadraticProgram` binario, **QAOA** (MinimumEigenOptimizer) si Qiskit está instalado; si no, **enumeración clásica 2³**. |
| `backend/system_orchestrator.py` | Tras **cambio >10% en irradiancia** (o primer ciclo con irradiancia), ejecuta el optimizador en **executor** (no bloquea el event loop). |
| Dashboard 7D | Métrica **Quantum Confidence Score** y kW asignados RO/Geo/O3. |

## Variables de entorno

| Variable | Efecto |
|----------|--------|
| `CASTUO_IBM_QUANTUM=1` | Intenta **IBM Quantum Runtime** (requiere `QISKIT_IBM_TOKEN`). |
| `QISKIT_IBM_TOKEN` | Token IBM Quantum. |

## Dependencias opcionales

```bash
pip install -r requirements-castuo-quantum.txt
```

Sin ellas, el sistema sigue operando con **classical_enumeration** y un **Quantum Confidence Score** coherente con la calidad de la solución factible.

## MRV cuántico / ERC-1155 (hoja de ruta)

Los resultados del optimizador y la causa raíz pueden firmarse en auditoría (`quantum_bio_grid_optimization`) como evidencia de **eficiencia matemática máxima** bajo restricciones reales de finca; la extensión a **ZK-Proof + Smart Contract** es evolución 5.PRO+ documentada en visión de producto.

## Referencias

- `docs/ARQUITECTURA-SISTEMA.md`
- `docs/SOBERANIA-TECNOLOGICA.md`
