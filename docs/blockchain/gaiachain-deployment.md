# GaiaChain 3.0 (Template, soberania)

## Objetivo
Desplegar una blockchain operativa para notarizar eventos criticos (commits, auditorias, evidencias) con trazabilidad verificable.

## Requisitos de infraestructura (placeholders)
- 3 nodos: 1 validador + 2 respaldo
- CPU/RAM/SSD por nodo: [AJUSTAR]
- Red: [VPC o red privada]
- Puertos: [AJUSTAR]

## Despliegue (docker-compose template)
Ver archivo:
- `docker-compose.gaiachain.yml`

## Variables requeridas (placeholders)
- `NODE_KEY_<N>`: claves de nodo (no incluir en el repo)
- `BOOTNODES`: lista de bootnodes (formato enode://...)

## Integracion con Castuo-System
Tu backend registra evidencia inmutable mediante:
- `POST /api/v1/witness` (GaiaChain)
- contrato minimal del repo: `{"hash","coop_id","ipfs_cid"}`

## Verificacion
- Confirmar que el endpoint witness responde 2xx
- Confirmar que los TX hashes retornan y pueden verificarse
- Registrar un evento de prueba con `scripts/Register-SecurityEvent.ps1`

