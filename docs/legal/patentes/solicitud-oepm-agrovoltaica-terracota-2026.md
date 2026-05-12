# Solicitud de Patente Conjunta (OEPM)

## Titulo provisional
"Sistema integrado de agrovoltaica con refrigeracion pasiva mediante terracota, geotermia somera y sensores de polimeros metalicos biocompatibles para cultivos hidroponicos de alta eficiencia"

## 0) Datos de contexto (piloto Extremadura)
Este documento forma parte de la documentacion del prototipo Extremadura 2026 y se complementa con:
- `docs/ops/pilotos/extremadura-agrovoltaica-terracota-2026.md`
- `docs/ops/pilotos/ctaex-acuerdo-prototipo-agrovoltaica-terracota.md`

## 1. Campo de la invencion
La presente invencion pertenece al ambito de la agrovoltaica avanzada, combinando:

- Refrigeracion pasiva mediante modulos de terracota.
- Geotermia somera (aprox. 1.5 a 2.0 m de profundidad) para estabilidad termica.
- Sensores de polimeros metalicos biocompatibles, caracterizados por ensayos de biocompatibilidad (ISO 10993-5).
- Gemelos digitales 4D para optimizacion en tiempo real (simulacion temporal + ajuste).
- Trazabilidad en blockchain (GaiaChain) para cumplimiento regulatorio y auditoria.

## 2. Antecedentes de la tecnica
2.1 Agrovoltaica clasica
La agrovoltaica clasica integra paneles solares sobre cultivos con el objetivo de reducir estres termico y aumentar eficiencia energetica.

2.2 Refrigeracion pasiva
Existen soluciones basadas en materiales ceramicos con capacidad termica para amortiguar variaciones, si bien suelen carecer de integracion con un sistema termico completo (terracota + geotermia) y con trazabilidad inmutable.

2.3 Sensores conductivos y biocompatibilidad
Los sensores conductivos y metodos de medicion pueden incorporar materiales con riesgo de toxicidad si no se dispone de ensayos de biocompatibilidad. La invencion se dirige a sensores con matriz polimerica PLA y relleno conductor biocompatible, respaldado por ensayos ISO 10993-5.

2.4 Gemelos digitales
Los gemelos digitales se aplican en agricultura, incluyendo simulacion para prediccion y optimizacion. La invencion integra el componente temporal (4D) y vincula decisiones/estados con evidencia inmutable.

## 3. Descripcion detallada
3.1 Modulos de terracota
- Composicion: arcilla extremena.
- Geometria: modulos de 80 x 40 x 10 cm, con configuracion interna orientada a flujo de aire (refrigeracion pasiva).
- Propiedades termicas: conductividad y capacidad calorifica ajustadas para amortiguacion.
- Fabricacion: moldeado por extrusion.

3.2 Sistema geotermico somero
- Profundidad: aprox. 1.8 m (ajustable dentro del rango 1.5 a 2.0 m segun emplazamiento).
- Intervencion termica: estabilidad termica mediante intercambio cerrado con bomba de calor de referencia.
- Fluido caloportador: mezcla de agua con glicol (porcentaje ajustable).
- Resultado: temperatura estable para disminuir picos termicos del interior.

3.3 Polimeros metalicos biocompatibles para sensores
- Matriz polimerica: PLA.
- Relleno conductor: nanoparticulas de cobre (porcentaje en el orden de 5%).
- Conductividad objetivo: en el intervalo referido por el proyecto.
- Ensayos de biocompatibilidad: ISO 10993-5 (citotoxicidad), y soporte documental de fabricacion (impresion 3D por proveedor).

3.4 Gemelos digitales 4D
El sistema incluye un gemelo digital con:
- Modulo termico (simulacion y/o estimacion CFD simplificada como scaffold, con integracion posterior a CFD real).
- Modulo estructural (estimacion FEA/scaffold, con integracion posterior).
- Modulo temporal: serie historica de estados.
- Modulo de decisiones: optimizacion mediante IA local.

Flujo de integracion:
- Datos de sensores (temperatura, humedad, radiacion, flujo termico, etc.) -> gemelo digital -> estimacion/optimizacion -> ajustes -> actuadores -> nueva trazabilidad.

3.5 Trazabilidad con GaiaChain
La invencion incluye un mecanismo de evidencia inmutable:
- Cada registro relevante (por ejemplo, mediciones, estados y versiones de modelos) se convierte en un hash.
- El hash se notariza en GaiaChain mediante payload minimal:
  `{"hash", "coop_id", "ipfs_cid"}`

### Contrato (ejemplo de modelo de referencia)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PrototypeTraceability {
    struct Measurement {
        string sensorId;
        string parameter; // "temperature", "humidity", etc.
        float value;
        uint256 timestamp;
        string ipfsCid; // Optional for large data
    }

    event MeasurementRecorded(
        string indexed coopId,
        string indexed sensorId,
        string parameter,
        float value,
        uint256 timestamp,
        string ipfsCid
    );

    function recordMeasurement(
        string memory coopId,
        string memory sensorId,
        string memory parameter,
        float value,
        uint256 timestamp,
        string memory ipfsCid
    ) public {
        emit MeasurementRecorded(
            coopId,
            sensorId,
            parameter,
            value,
            timestamp,
            ipfsCid
        );
    }
}
```

## 4. Reivindicaciones (borrador)
4.1 Un sistema integrado de agrovoltaica que comprende:
- Paneles solares bifaciales.
- Modulos de terracota configurados para refrigeracion pasiva.
- Geotermia somera para estabilidad termica.
- Sensores de polimeros metalicos biocompatibles con matriz PLA y relleno conductor de nanoparticulas de cobre.

4.2 El sistema de la reivindicacion 4.1, donde:
- Los modulos de terracota presentan configuracion interna orientada a flujo de aire para amortiguacion de picos termicos.

4.3 El sistema de la reivindicacion 4.1, donde:
- Los sensores cumplen ensayos de biocompatibilidad (ISO 10993-5) para citotoxicidad y presentan documentacion de fabricacion.

4.4 El sistema de la reivindicacion 4.1, donde:
- Los gemelos digitales 4D emplean un modulo termico, un modulo estructural y un componente temporal para optimizacion en tiempo real.

4.5 El sistema de la reivindicacion 4.1, donde:
- La trazabilidad de mediciones/estados/decisiones se registra mediante GaiaChain usando un payload minimal `{"hash","coop_id","ipfs_cid"}`.

## 5. Dibujos (referencia a figuras)
Figura 1: Vista explodida del sistema integrado.  
Figura 2: Diagrama de flujo del gemelo digital 4D.  
Figura 3: Detalle del modulo de terracota (seccion transversal).  
Figura 4: Esquema del sensor de polimero metalico.  

## 6. Resumen
La invencion representa un salto cualitativo en agrovoltaica avanzada al combinar:

- Refrigeracion pasiva (terracota + geotermia somera).
- Sensores biocompatibles basados en polimeros metalicos (PLA + nanoparticulas de cobre).
- Optimizacion mediante gemelos digitales 4D con IA local.
- Trazabilidad inmutable en GaiaChain para cumplimiento y auditoria.

## 7. Solicitantes (borrador)
- CTAEX (50%).
- Castuo-System (50%).

