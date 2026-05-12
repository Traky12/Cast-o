# EICAR TEST (repo)

## Que es

EICAR es un estandar (fichero de prueba) para validar que una solucion antivirus detecta malware.

## Uso (seguro)

Este repo incluye:
- `scripts/security/test_eicar_injection.sh`

Ejemplo:

```bash
chmod +x scripts/security/test_eicar_injection.sh
EICAR_SCAN_CMD="clamscan" \
./scripts/security/test_eicar_injection.sh
```

El script solo crea un fichero local y, si `EICAR_SCAN_CMD` esta definido, intenta ejecutarlo contra el fichero.

## Integracion con CI/CD

En este repo no encontre un `.gitlab-ci.yml`, asi que la integracion en pipeline queda como `por validar` segun tu infraestructura de despliegue.

