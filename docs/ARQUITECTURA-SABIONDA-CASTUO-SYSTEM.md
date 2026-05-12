# Arquitectura SABIONDA + CASTUO-SYSTEM v5.0

Diagrama de integración de perfiles, módulos, seguridad y auditoría.

```mermaid
graph TD
    subgraph "1. Usuario Final"
        A1[SABIONDA_MASTER_LANDUM] -->|Gestión total| A2[LANDUM_PRO]
        A1 -->|Crea/gestiona| A3[TECHNICIAN]
        A1 -->|Crea/gestiona| A4[FARMER]
        A1 -->|Crea/gestiona| A5[AUDITOR]
        A1 -->|Crea/gestiona| A6[STUDENT]
        A1 -->|Crea/gestiona| A7[GUEST]
    end

    subgraph "2. Gestión de Perfiles"
        B1[ProfileManager] -->|Carga| B2[ProfileConfig]
        B1 -->|Valida acceso| B3[SessionManager]
        B1 -->|Registra en| B4[GaiaChain]
        B2 -->|Define| B5[Tono de voz]
        B2 -->|Define| B6[Módulos permitidos]
        B2 -->|Define| B7[Restricciones]
    end

    subgraph "3. Módulos Principales"
        C1[Security] -->|Depende de| C2[Blockchain]
        C3[Production] -->|Depende de| C2
        C4[Messaging] -->|Depende de| C1
        C5[Compliance] -->|Depende de| C2
        C6[IoT] -->|Independiente| C0
        C7[Analytics] -->|Depende de| C3
        C7 -->|Depende de| C2
        C8[Academy] -->|Independiente| C0
    end

    subgraph "4. Servicios de Apoyo"
        D1[DependencyManager] -->|Ordena carga| D2[ModuleLoader]
        D2 -->|Carga dinámica| C1
        D2 -->|Carga dinámica| C3
        D2 -->|Carga dinámica| C4
        D3[DataEncryptionService] -->|Usa| D4[HSM FIPS 140-2]
        D3 -->|Registra en| B4
        D5[AdvancedAuth] -->|YubiKey + Biometría| D4
        D5 -->|Registra en| B4
        D6[AuditSystem] -->|Registra todo| B4
    end

    subgraph "5. Infraestructura"
        E1[GaiaChain] -->|Consenso| E2[HoneyBadgerBFT]
        E1 -->|Firmas| E3[Dilithium PQ]
        E4[HSM Thales Luna 7] -->|Almacena claves| E1
        E5[Dedrone Anti-Drones] -->|Protege| E6[Invernaderos]
        E7[SOC 24/7] -->|Monitorea| E1
        E7 -->|Usa| E8[TheHive + Velociraptor]
    end

    subgraph "6. Interfaz de Usuario"
        F1[AdaptiveResponseEngine] -->|Usa| B1
        F1 -->|Genera respuestas| A1
        F1 -->|Genera respuestas| A2
        F2[SabiondaVersionManager] -->|Gestiona versiones| A1
        F2 -->|Crea perfiles| B1
    end

    A1 -->|Usa| B1
    A2 -->|Usa| B1
    B1 -->|Carga módulos| D2
    D6 -->|Audita| B1
    D6 -->|Audita| C1
```

## Resumen ejecutivo

- **Seguridad**: Autenticación multicapa (YubiKey + biometría + HSM + GaiaChain). Cifrado con HSM y auditoría inmutable.
- **Perfiles**: SABIONDA_MASTER_LANDUM con acceso total. Versiones restringidas (LANDUM_PRO, TECHNICIAN, FARMER, etc.) con tonos y funcionalidades adaptadas. Motor de respuestas adaptativas.
- **Arquitectura modular**: Carga dinámica de módulos según permisos (ModuleLoader + DependencyManager). Solo se carga lo necesario.
- **Evolución SABIONDA**: Perfil master con gestión de versiones (SabiondaVersionManager). Creación de perfiles personalizados (ej. LANDUM_PRO_AGRO). Tono profesional o extremeño según contexto.
