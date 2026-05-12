# ISO 10993-5:2022 (Borrador) - Plan de ensayos de biocompatibilidad

## 0) Alcance
Plan para demostrar la biocompatibilidad de los **sensores de polimeros metalicos biocompatibles** para el prototipo Extremadura 2026:
- Matriz: PLA.
- Relleno conductor: nanoparticulas de cobre (orden de 5%).

Este documento define:
- Ensayos requeridos.
- Documentacion a presentar.
- Cronograma (borrador).
- Responsables.

## 1) Referencias normativas (segun alcance del proyecto)
- ISO 10993-5 (citotoxicidad in vitro) - menciones de ensayo segun UNE-EN ISO 10993-5:2009.
- ISO 10993-10 (sensibilizacion cutanea) - UNE-EN ISO 10993-10:2010.
- ISO 10993-11 (irritacion intracutanea) - UNE-EN ISO 10993-11:2009.

> Nota: ajustar nomenclatura exacta y version para el expediente final con el laboratorio/entidad certificadora.

## 2) Ensayos requeridos
2.1 Citotoxicidad in vitro
- Objetivo: demostrar ausencia de citotoxicidad.
- Tipo: ensayo in vitro conforme ISO 10993-5.

2.2 Sensibilizacion cutanea
- Objetivo: evaluar potencial de sensibilizacion.
- Tipo: ensayo conforme ISO 10993-10.

2.3 Irritacion intracutanea
- Objetivo: evaluar irritacion local.
- Tipo: ensayo conforme ISO 10993-11.

## 3) Documentacion a presentar
- Composicion detallada del sensor (PLA + nanoparticulas de cobre).
- Protocolo de fabricacion:
  - Impresion 3D (FDM) por proveedor (p.ej. BioPolymers SL).
  - Parametros de proceso relevantes para reproducibilidad.
- Fichas tecnicas de materiales (PLA y dispersante/si aplica).
- Identificacion de lotes/muestras (metadatos del lote, fecha, responsable).
- Historial de esterilizacion si aplica.
- Procedimiento de preparacion de muestras para ensayo (con criterios de aceptacion).
- Resultados previos (si existen) y cualquier desviacion controlada del proceso.

## 4) Cronograma (borrador)
- Envio de muestras: `15/04/2026`
  - Responsable: Castuo-System
- Ensayos de citotoxicidad (y ensayos asociados del paquete): `30/06/2026`
  - Responsable: CICYTEX
- Informe final: `30/09/2026`
  - Responsable: CICYTEX
- Certificacion: `31/10/2026`
  - Entidad: por definir (p.ej. AENOR u otra entidad aceptada por el expediente)

## 5) Coste (por validar)
- Coste estimado: `8.500 EUR` (por validar)
- Financiacion: proyecto I+D+i con soporte de CICYTEX (por validar)

## 6) Criterios de aceptacion (orientativos)
- Resultados de ensayos dentro de umbrales de seguridad definidos por el protocolo del laboratorio.
- Documentacion completa (composicion + trazabilidad de lotes + protocolos + informe).

## 7) Evidencia y trazabilidad en GaiaChain (integracion)
Para trazabilidad:
- Notarizar en GaiaChain hashes de:
  - informes de ensayo finales,
  - versiones de protocolos,
  - metadata canonica del lote del sensor.

Se recomienda el uso del contrato minimal del repo:
`{ "hash", "coop_id", "ipfs_cid" }`.

