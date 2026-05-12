# Trazabilidad y cumplimiento (AEMPS - RD 903/2025) - Borrador

## 0) Alcance
Este documento define un esquema de trazabilidad y buenas practicas orientado a:
- Trazabilidad de lotes y condiciones ambientales.
- Registro de instalaciones y evidencia inmutable mediante GaiaChain.
- Vinculacion de registros a QR en bandejas de cultivo.

El objetivo es apoyar auditorias y preparar documentacion para expedientes.

> Nota: validar el ajuste final con normativa y con el expediente tecnico del sistema.

## 1) Trazabilidad en GaiaChain
Se registran, mediante hashes, los elementos relevantes:
- Lotes de semillas.
- Nutrientes utilizados.
- Condiciones ambientales (temperatura, humedad, pH).
- Eventos criticos (p.ej. cambios de protocolo, incidencias y correcciones).

### 1.1 Contrato minimal (repo)
Se utiliza el payload minimal ya implementado en el repo:
`{ "hash", "coop_id", "ipfs_cid" }`

## 2) QR en bandejas (vinculacion)
Cada bandeja incluye:
- Un QR con prefijo del proyecto (ej: `EXT-2026-`).
- Contenido del QR: id de lote y referencia a evidencia notarizada (p.ej. mediante hash).

## 3) Buenas practicas de cultivo (BPC) - resumen
Protocolos:
- Limpieza de modulos de terracota: cada 3 ciclos.
- Esterilizacion de sustrato: peroxido de hidrogeno 3% (ajustar a protocolo final).
- Monitoreo de pH/CE: cada 2 horas.

## 4) Documentacion sugerida para AEMPS (plantilla JSON)
Ejemplo de registro de instalaciones:

```json
{
  "installation_id": "CASTUO-EXT-01",
  "location": "Valdefermos, Caceres",
  "crops": ["microgreens", "fresas"],
  "hydroponic_system": {
    "type": "NFT (Nutrient Film Technique)",
    "nutrients": ["Osmocote", "Masterblend"],
    "pH_range": [5.5, 6.5],
    "EC_range": [1.5, 2.5]
  },
  "traceability": {
    "blockchain": "GaiaChain",
    "qr_code_prefix": "EXT-2026-"
  }
}
```

## 5) Control de plagas (resumen)
Metodos fisicos:
- Trampas cromaticas.

Metodos biologicos:
- Amblyseius swirskii (ajustar a plan final).

Metodos quimicos:
- Solo permitidos por AEMPS (ej. piretrinas naturales), previa autorizacion/ajuste.

## 6) Auditorias
Frecuencia sugerida:
- Trimestral (primera: `30/06/2026`)

Ente auditor:
- Entidad colaboradora por definir (p.ej. AENOR u otra aceptada por el expediente).

## 7) Evidencia inmutable recomendada
Notarizar:
- Versiones de protocolos HACCP y BPC.
- Hashes de series temporales canonicas de sensores.
- Hashes de informes de ensayos relacionados.

