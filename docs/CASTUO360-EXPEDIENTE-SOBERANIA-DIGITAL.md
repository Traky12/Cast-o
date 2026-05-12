# CASTUO360 — Expediente legal integral en Ecosystem 6.X

Blindaje PI + **trust layer** ejecutable: hash como nexo código–hardware–tribunal/inversor.

## 1. Legal-layer (blockchain)

- **Timestamping:** hash **SHA-256** del ZIP expediente (planos CAD, sensores piezo, algoritmos airbag) anclado **GaiaChain** → fecha cierta / prioridad invención.
- **Smart-NDA:** acceso repo firmware airbag condicionado a firma digital vigente; revoca al expirar contrato.

## 2. Caja negra evidence-ready

- Telemetría IMU / airbags empaquetada y **firmada** → prueba cumplimiento reivindicaciones (ej. 1.c activación preventiva).
- Impacto / flotación / airbag → **certificado digital** a aseguradora o autoridad aviación.

## 3. V2X / alerta urbana

- Nodo seguridad ciudadana; protocolo cifrado **BLE/UWB** documentado como secreto industrial / patente.

## 4. Activos protegidos (resumen)

| Módulo | Protección | Ecosystem 6.X |
|--------|------------|---------------|
| Anillo modular | Modelo utilidad / diseño | Telemetría integridad estructural |
| Airbags inteligentes | Patente invención | Agent5 + logs firmados |
| SimRing-Airbag | Software / PI | Gemelo formación |
| Beacon post-impacto | Secreto industrial | IPFS + hash |

## Herramienta hash expediente

```bash
python scripts/hash_expediente_zip.py ruta/EXPEDIENTE_CASTUO360.zip
```

## Confianza dinámica

| Nivel | Implementación |
|-------|----------------|
| Anclaje | Hash maestro ZIP on-chain |
| Acceso | Smart-NDA |
| Pericial | Logs firmados continuos |

*OEPM / PCT: asesorar con agente de patentes antes de publicación pública del ZIP sin reserva.*

## Ejecución del blindaje (flujos reales)

Ancla GaiaChain, ciclo de vida PI por componente, Smart-NDA y checklists OEPM/PCT: [CASTUO360-BLINDAJE-EJECUCION-6X.md](CASTUO360-BLINDAJE-EJECUCION-6X.md).
