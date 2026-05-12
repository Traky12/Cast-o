# Parámetros clave de seguridad avanzada

| Categoría    | Parámetro                    | Valor recomendado              | Normativa              |
|-------------|------------------------------|---------------------------------|------------------------|
| Cifrado     | Algoritmo                    | RSA4096_AES256_GCM_Kyber1024_SECURE | NIST SP 800-56C, FIPS 140-2 L3 |
|             | Poly modulus degree          | 16384                           | NIST SP 800-56C        |
|             | Coeff mod bit sizes          | [60, 40, 40, 60, 60]            | NIST SP 800-56C        |
|             | Security level               | 192-bit post-quantum           | NIST SP 800-131A       |
|             | Rotación de claves           | 90 días                         | ISO 27001:A.10.1.1     |
| Detección   | Umbral red (low)             | 0.001 (0.1%)                    | ISO 27001:A.12.4.1     |
|             | Umbral comportamiento (low)  | 0.0005 (0.05%)                  | GDPR:Art.32            |
|             | Retención evidencias         | 90 días                         | GDPR:Art.30            |
|             | Modo cumplimiento             | strict                          | ISO 27001:A.18.1.4     |
| Defensa     | Política por defecto         | default                         | ISO 27001:A.16.1.1     |
|             | Tiempo objetivo respuesta    | 100 ms                          | NIST SP 800-61         |
|             | Falsos positivos objetivo    | 0.001 (0.1%)                    | ISO 27001:A.12.6.1     |
|             | Ruta de escalado             | security → devops → legal → executive | ISO 27001:A.16.1.4 |
| Trazabilidad| Algoritmo hash               | BLAKE3                          | eIDAS:Art.3            |
|             | Algoritmo firma              | Dilithium5                      | NIST SP 800-208        |
|             | Tamaño máximo bloque         | 1 MB                            | ISO 27001:A.12.4.3     |
|             | Retención                    | 365 días                        | GDPR:Art.30            |
| GaiaChain   | Retención evidencias         | 10 años                         | eIDAS:Art.4            |
|             | Retención informes legales   | 30 años                         | GDPR:Art.30            |
|             | Cifrado evidencias           | AES-256-GCM+Kyber1024           | NIST SP 800-131A       |
| Monitoreo   | Intervalo                    | 15 s                            | ISO 27001:A.12.4.1     |
|             | Evaluación alertas           | 30 s                            | ISO 27001:A.16.1.1     |
|             | Retención métricas           | 90 días                         | ISO 27001:A.12.4.3     |

## Activación

```bash
./scripts/configure_security.sh
./scripts/deploy_defense_system.sh
```

## Respuesta a incidentes

```bash
./scripts/incident_response.sh critical "Descripción del incidente"
```
