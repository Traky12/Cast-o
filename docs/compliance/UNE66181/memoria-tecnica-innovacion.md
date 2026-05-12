# UNE 66181:2022 - Memoria tecnica de I+D+i (Borrador)

## 0) Alcance
Memoria para documentar la innovacion asociada al prototipo Extremadura 2026:
- Validar eficiencia termica del sistema integrado (agrovoltaica + refrigeracion pasiva).
- Optimizar la produccion de microgreens en climas extremos.

Este documento sirve como base para auditoria documental.

## 1) Objetivos
Objetivo 1: Validar refrigeracion pasiva
- Meta: mantener condiciones termicas dentro de rangos objetivo.
- Metodo: medicion con sensores y verificacion mediante gemelos digitales 4D.
- Evidencia: registros de sensores + notarizacion en GaiaChain.

Objetivo 2: Optimizar microgreens en climas extremos
- Meta: mejora de rendimiento frente a referencia operativa.
- Metodo: configuracion de gemelos digitales + ajuste de parametros de cultivo.
- Evidencia: medicion de produccion (diario/cosecha) + trazabilidad.

## 2) Plan de explotacion de resultados (resumen)
- Publicacion de resultados tecnicos: se publicarion solo datos no confidenciales.
- Apertura para cooperativas extremenas: mediante licencias de uso con clausulas de proteccion.
- Integracion con acuerdos B2B: distribucion y compras garantizadas (cuando existan contratos firmados).

## 3) Gestion de Propiedad Intelectual
- Patente conjunta (50% CTAEX, 50% Castuo-System) para el sistema integrado.
- Licencias de uso: libre para cooperativas extremenas en el marco del acuerdo correspondiente.

## 4) Indicadores de innovacion (orientativos)
Indicador: Reduccion de consumo energetico
- Meta: >= 40% vs. invernaderos tradicionales
- Metodo de verificacion: medidores inteligentes + GaiaChain

Indicador: Aumento de rendimiento
- Meta: >= 25% en microgreens
- Metodo de verificacion: balanza certificada + registros de cosecha

Indicador: Huella de carbono
- Meta: <= 0.5 kg CO2/kg producto
- Metodo de verificacion: analisis de ciclo de vida (ACV)

## 5) Cronograma (borrador)
- Presentacion solicitud: `30/04/2026`
  - Responsable: Castuo-System
- Auditoria documental: `30/06/2026`
  - Entidad: por definir (p.ej. AENOR)
- Visita tecnica: `30/09/2026`
  - Entidad: por definir (p.ej. AENOR)
- Emision certificado: `30/11/2026`
  - Entidad: por definir

## 6) Costes (por validar)
- Presupuesto del prototipo: `25.000 EUR` (por validar)
- Ensayos: `10.000 EUR` (por validar)
- Socios: CTAEX (50%), Castuo-System (30%), CICYTEX (20%) - por validar

## 7) Evidencia inmutable recomendada en GaiaChain
Notarizar:
- Memoria tecnica y versiones.
- Versionado de protocolos de ensayos.
- Hash de series temporales de sensores (canones de integridad).

Payload minimal del repo:
`{ "hash", "coop_id", "ipfs_cid" }`

