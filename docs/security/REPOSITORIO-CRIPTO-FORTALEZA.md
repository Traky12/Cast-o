# Repositorio como Cripto-Fortaleza

**Objetivo:** que, aunque el repositorio sea exfiltrado o clonado por un atacante, los documentos críticos se vean como ruido cifrado fuera del Búnker de Granito, y solo se lean en entornos con llaves físicas autorizadas.

Este diseño se apoya en tres ejes:

1. **Cifrado en reposo** (AES-256-GCM + PQC en la capa de intercambio de claves).  
2. **Firma de identidad fuerte** (“Lacre digital” con hardware FIDO2/YubiKey).  
3. **Ofuscación y destrucción segura de sesión** (anti-forense).

---

## 1) Cifrado en reposo: AES-256-GCM + Kyber (ML-KEM)

### 1.1. Esquema híbrido recomendado

- **Simétrico**: AES-256-GCM para cifrado de contenido de ficheros (`.md`, `.json`, etc.).  
- **Asimétrico PQC**: Kyber (ML-KEM) para encapsular la clave simétrica de sesión.  
- **Soporte operativo**: se implementa a través de herramientas de cifrado de ficheros tipo **SOPS** o **git-crypt**, integradas con llaves en hardware (YubiKey/OpenPGP).

> Referencia de roadmap PQC: ver `docs/security/NIST-PQC-Roadmap.md`.

### 1.2. Archivos críticos a cifrar

Recomendación mínima (lista ampliable):

- `docs/operations/MANUAL-CRISIS-TIERRA-FIRME.md`
- `docs/security/PROTOCOLO-DESPERTAR-V2-HARDENED.md`
- `docs/security/MANIFIESTO_SOBERANIA_README.md` (si incluye claves operativas)
- Cualquier anexo con detalles de **claves físicas**, rutas de backup, o procedimientos internos no públicos.

La selección exacta se controla desde `.sops.yaml` u hoja de configuración equivalente.

### 1.3. Uso operativo con SOPS (ejemplo)

> Este flujo asume que ya existe una llave PGP asociada a una **YubiKey** u otro token hardware, y que en el futuro puede sustituirse o complementarse por un backend Kyber/ML-KEM cuando existan toolchains PQC estables en producción.

1. **Definir reglas en `.sops.yaml`** (ya incluido en raíz del repo; ver fichero para actualizar `KEYID_PLACEHOLDER`).  
2. **Cifrar un archivo crítico**:

   ```bash
   # Linux/macOS
   sops -e -i docs/operations/MANUAL-CRISIS-TIERRA-FIRME.md
   ```

   En Windows PowerShell:

   ```powershell
   sops -e -i "docs/operations/MANUAL-CRISIS-TIERRA-FIRME.md"
   ```

3. **Descifrar localmente (solo con llave hardware presente)**:

   ```bash
   sops -d -i docs/operations/MANUAL-CRISIS-TIERRA-FIRME.md
   ```

Resultado:

- En GitHub / GitLab: el archivo aparece con contenido cifrado (ruido).  
- En el Búnker / entorno autorizado: el archivo se abre en claro solo si la **llave física** está conectada.

---

## 2) Firma de “Lacre Digital” (Identidad fuerte)

### 2.1. Commits firmados por hardware

Requisito recomendado:

- Solo se aceptan commits **firmados** (`gpg --sign` o `ssh+FIDO2`), realizados desde llaves custodiadas por:
  1. Custodio de la Tierra.  
  2. Guardián del Silicio.  
  3. Auditor Ético.

Pasos generales (a completar fuera del repo):

1. Configurar en Git:

   ```bash
   git config --global user.signingkey <KEYID>
   git config --global commit.gpgsign true
   ```

2. Asociar la llave a un **dispositivo FIDO2/YubiKey** siguiendo las guías del proveedor.  
3. Activar en la plataforma remota (GitHub/GitLab):
   - Requisito de **commits firmados** en ramas protegidas (`main`, `release/*`).  
   - Reglas de revisión: al menos 2 de los 3 custodios aprueban cambios en `docs/security/*` y `docs/operations/*`.

### 2.2. Cadena de confianza (Sigstore / gitsign)

Para las versiones de alto impacto (p. ej. cambios en `PROTOCOLO-DESPERTAR-V2-HARDENED.md`):

- Registrar releases con **sigstore/gitsign**, vinculando:
  - Hash del commit.  
  - Identidad del firmante (custodio).  
  - Evidencia de revisión de Sabionda (informe local o referencia en `FINAL_VALIDATION_REPORT.md`).

---

## 3) Ofuscación y destrucción de sesión

### 3.1. Ofuscación de arquitectura (nivel documental)

Principios:

- **Para el atacante**: el repositorio parece colección de documentos técnicos y SOPs rutinarios.  
- **Para Sabionda y los custodios**: ciertos nombres y rutas se reconocen como módulos críticos.

Reglas prácticas:

- No exponer en claro:
  - Listas completas de ubicaciones físicas de backups.  
  - Correlación exacta entre nombres de fichero y dispositivos físicos.  
- Mantener esta lógica documentada solo en:
  - `docs/security/REPOSITORIO-CRIPTO-FORTALEZA.md` (este archivo).  
  - Documentos cifrados vía SOPS (cuando contengan detalles sensibles).

### 3.2. Autodestrucción de sesión (RAM volátil)

Nivel físico / sistema operativo (documentado en otros SOPs):

- Las **llaves simétricas en RAM** deben:
  - Residir en memoria marcada como no-swappable.  
  - Ser sobreescritas con `0x00` / patrones seguros al detectar:
    - Intentos de fuerza bruta sobre el acceso al búnker.  
    - Lecturas anómalas de memoria o manipulación física.

> Ver también:  
> - `docs/security/Quantum-Photonic-Destruction.md`  
> - `docs/security/Quantum-Destruction-Protocols.md`

---

## 4) Procedimiento rápido para administradores

1. **Revisar** este documento y `docs/security/NIST-PQC-Roadmap.md`.  
2. **Configurar llaves** en hardware (YubiKey/FIDO2 + PGP) y registrar IDs de llave en el fichero `.sops.yaml`.  
3. **Cifrar** los documentos marcados como críticos usando `sops -e -i`.  
4. **Habilitar commits firmados** y protección de ramas en la plataforma git remota.  
5. **Registrar** en `docs/ESTADO_INTEGRACION_SEGURIDAD.md` la activación efectiva del cifrado de repositorio y del lacre digital.

Con esto, el repositorio pasa de ser un simple árbol de archivos a un **cofre cifrado**, cuyo contenido completo solo existe, en claro, dentro del perímetro soberano del Castúo-System.

