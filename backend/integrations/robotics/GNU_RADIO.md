# GNU Radio y captura RF (fuera del wheelhouse del repo)

**Objetivo territorial:** captura legal y técnicamente autorizada en bandas permitidas; el código Python del monolito **no** arranca bloques GNU Radio sin que el operador tenga licencias, filtros y antenas acordes.

## Requisitos típicos (Linux)

- Paquetes de sistema: `gnuradio`, `gr-osmosdr` (o driver del SDR concreto).
- Flujo: `osmosdr.source` → cadena de demodulación → `file_sink` o socket a un servicio que publique **solo digest + metadatos** hacia Castúo.

## Contrato con Castúo

1. Los IQ completos **no** se suben al backend por defecto: solo hashes, contadores y métricas agregadas (alineado con PEI-002 / minimización).
2. Cifrado en tránsito: TLS 1.3 hacia API interna; opcional sellado con `RobotSecurityLayer` para comandos cortos.

## Ejemplo de esqueleto (referencia, no ejecutable aquí)

```python
# Ejecutar solo en máquina con GNU Radio y permisos RF correctos.
# from gnuradio import gr, blocks, analog  # noqa: E800
```

Documentar en DPIA si se correlacionan señales con personas u operadores (p. ej. voz, biometría).
