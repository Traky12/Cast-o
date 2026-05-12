# Programa de Certificación en Seguridad para CASTUO 5.0

**Duración**: 40 horas (5 días intensivos)  
**Modalidad**: Presencial + Virtual (laboratorios prácticos)  
**Certificación**: *Especialista en Seguridad Ciberfísica para Agroindustria 4.0* (avalado por UEx y CTAEX)

---

## Módulo 1: Seguridad Física Avanzada (8 h)

### Temas
1. **Protocolos de Acceso Biométrico**
   - Configuración de YubiKey + Huella Dactilar + PIN.
   - Integración con GaiaChain para logs inmutables.
   - *Laboratorio*: Configurar MFA en Raspberry Pi (`security/physical_mfa.py`).

2. **Sistemas de Detección de Intrusiones Físicas**
   - Sensores sísmicos y de vibración (`security/seismic_sensor.py`).
   - Cámaras con IA (detección de armas/comportamiento).
   - *Laboratorio*: Simular intrusión y analizar alertas.

3. **Protección de Invernaderos**
   - Puertas blindadas clase 6 (EN 1627).
   - Sistemas anti-sabotaje para paneles solares.

---

## Módulo 2: Seguridad de Red y Ciberfísica (10 h)

1. **Arquitectura de Red Segura**
   - Firewalls (default-deny), segmentación con Cilium + eBPF (`security/iot_network_policy.yaml`).
   - *Laboratorio*: Políticas de red para IoT agrícola.

2. **Detección de APTs**
   - Velociraptor, TheHive; análisis para agroindustria (`security/apt_detection.py`).
   - *Laboratorio*: Simular ataque APT y respuesta.

3. **Seguridad Post-Cuántica**
   - CRYSTALS-Kyber, Dilithium (`security/post_quantum.py`, `security/post_quantum_signatures.py`).
   - *Laboratorio*: Cifrado/descifrado con liboqs.

---

## Módulo 3: Protección de Datos y Blockchain (8 h)

1. **Cifrado Homomórfico**
   - Microsoft SEAL para análisis sin descifrar (`security/homomorphic_encryption.py`).
   - *Laboratorio*: Procesar datos de producción cifrados.

2. **Tokenización (GDPR)**
   - Tokenización con auditoría en GaiaChain (`security/data_tokenization.py`).
   - *Laboratorio*: Tokenizar documento con PII.

3. **GaiaChain y ZKP**
   - Consenso PBFT, pruebas de conocimiento cero.
   - *Laboratorio*: Registrar lote de cáñamo en GaiaChain.

---

## Módulo 4: Respuesta a Incidentes (6 h)

1. **Protocolos de Respuesta**
   - Playbooks para ransomware, DDoS, intrusiones físicas.
2. **Forense Digital**
   - Velociraptor, Autopsy.
3. **Recuperación de Desastres**
   - Backups inmutables (WORM), planes de contingencia.

---

## Módulo 5: Cumplimiento Legal y Auditorías (8 h)

1. **Normativas**
   - GDPR, AI Act, RD 903/2025 (cannabis), eIDAS.
2. **Auditorías**
   - ISO 27001, ISO 27035.
3. **Gestión de Riesgos**
   - Matriz de riesgos y planes de mitigación.

---

## Evaluación Final

- **Examen teórico**: 30 %
- **Proyecto práctico**: 50 %
- **Simulación de incidente**: 20 %

**Requisitos**: Asistencia 90 % + aprobación de evaluaciones.  
**Vigencia**: 2 años (recertificación anual recomendada).
