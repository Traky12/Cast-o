# Cumplimiento normativo

## Cumplimiento automático con normativas globales

El adapter aplica y documenta cumplimiento según la región configurada.

El adapter aplica y documenta cumplimiento según la región configurada (`ES`, `EU`, `GLOBAL` u otras).

### Normativas soportadas

| Región | Normativas |
|--------|------------|
| **UE** | GDPR, AI Act 2024, PAC 2040 |
| **USA** | CCPA, Farm Bill 2028 (configurable) |
| **LATAM** | LGPD (Brasil), Lei Agro 2026 (configurable) |
| **Asia** | PIPL (China), AgriTech 2030 (configurable) |

### Cómo se aplica el cumplimiento

1. **Validación de datasets**  
   En regiones con GDPR se comprueban columnas que puedan contener datos personales (email, DNI, teléfono). Se registra un aviso si no están anonimizadas (p. ej. sin prefijo `ANON_`). En producción se debe anonimizar o restringir el uso.

2. **Logging en GaiaChain 2.0**  
   Cada llamada a Mistral API genera un hash (SHA-256) de la petición y la respuesta, registrable en GaiaChain para auditoría y trazabilidad.

3. **Cifrado y autenticación**  
   Las API keys pueden almacenarse cifradas (Fernet). El ecosistema CASTÚO permite además AES-256-GCM y autenticación con YubiKey 5Ci para operaciones sensibles.

4. **Adaptación por región**  
   La configuración de cumplimiento (`compliance`) se elige según la región del adapter (ES, EU, GLOBAL), permitiendo extender a SM4 u otras normativas por zona (p. ej. China).
