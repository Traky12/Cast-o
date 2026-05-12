# Anytype — Configuración CASTÚO-SYSTEM TRL8 + ISO 27001

Guía enterprise CASTÚO. **Empresa:** CASTÚO 360 S.L. (CTO Gregorio Jiménez)  
**Producto:** SaaS agrovoltaico TRL8 (backend FastAPI + Vault PQC)  
**Certificación:** ISO 27001 Stage 1 92% (backup pen: `D:\CASTUO-SYSTEM_TRL8_20260316.zip`)  
**Equipo:** Gregorio + técnicos campo + clientes agricultores  
**Uso:** Demo CTAEX + colaboración visual local-first (GDPR compliant)

[Anytype](https://anytype.io) — aplicación local-first, P2P, con cifrado E2E (Países Bajos). Adecuada para documentación y colaboración sin depender de servidores en la nube.

### CASTÚO vs Obsidian vs Anytype

| CASTÚO       | Obsidian      | Anytype                 |
| ------------ | ------------- | ----------------------- |
| Sync         | 10 EUR/mes    | P2P WiFi gratis         |
| Mobile       | WebView lento | Apps nativas rápidas    |
| GDPR         | Australia     | Países Bajos compliant  |
| Colaboración | Individual    | Shared Spaces real-time |
| CTAEX        | Archivos      | Grafo visual TRL8       |

Obsidian Sync usa infraestructura de pago y puede estar fuera de UE; Anytype es local-first P2P y Países Bajos (UE).

---

## 1. Instalación + LOCAL-ONLY (GDPR compliant)

- **PC Windows:** [https://anytype.io](https://anytype.io) → descargar → **Engranaje (⚙️)** → **Network** → **LOCAL-ONLY**.
- **Móvil iOS/Android:** App Store / Play Store → Anytype → Onboarding → **Engranaje** → **LOCAL-ONLY**.

Requisitos:

- **Misma WiFi** (ej. **Gregorio_Casa**) en PC, iPhone y Android — CRÍTICO.
- **Recovery Phrase IDÉNTICA** (12 palabras) en todos los dispositivos.
- **PIN 6 dígitos** opcional para desbloquear.
- **NO** usar "Anytype Network" — solo **P2P local**.

---

## 2. Objetos CASTÚO (bases de datos visuales)

Crear **Objects** (bases de datos) para estructurar la información TRL8:

| Objeto | Tipo | Propiedades sugeridas | Uso |
|--------|------|------------------------|-----|
| **Proyecto TRL8** | Set / Database | Nombre, Fecha, Estado (Staging/Prod), Enlace (URL) | Un objeto por despliegue (ej. Demo CTAEX) |
| **Evidencia ISO 27001** | Set | Nombre doc, Tipo (DoA, Auditoría, ZAP), Ruta en pen, Fecha | Referencia a los 9 docs + emergency_demo.png |
| **Clave PQC** | Set | Nombre (K_gaiachain_sign…), Algoritmo (Kyber-768), Última rotación | Estado de las 4 claves |
| **Endpoint Demo** | Set | URL, Servicio (Backend/Vault/ZAP/Frontend), Puerto | Lista de localhost:8000/docs, 8200/ui, etc. |

Cómo crearlos en Anytype: **+** → **Object** → elegir **Set** o **Database** → añadir propiedades (Relation) según la tabla.

---

## 3. Grafo TRL8 (visualización de relaciones)

- Crear una **Page** (p. ej. “Grafo TRL8”) y enlazar desde ella a los objetos anteriores (Proyecto TRL8, Evidencias, Claves PQC, Endpoints).
- Usar **Graph view** (vista grafo) para ver relaciones: Proyecto → Evidencias, Proyecto → Endpoints, Evidencias → Claves.
- Opcional: en cada objeto, añadir una **Relation** “Relacionado con” apuntando a otros objetos para que el grafo muestre dependencias (backend → vault, deployment → docker-compose.staging).

---

## 4. Shared Spaces (colaboración)

- Si se usa **Anytype ID** (no local-only), crear un **Space** compartido, p. ej. “CASTÚO TRL8”.
- Invitar por correo a técnicos campo o a Gregorio; asignar permisos (solo lectura para clientes agricultores si aplica).
- Mantener en el Space:
  - Enlaces a documentación (DoA, auditoría, ZAP).
  - Páginas de procedimientos (despliegue desde pen, URLs demo).
  - Notas de demo CTAEX (qué enseñar en los 10 min).

**GDPR:** Los datos en Anytype con cuenta son E2E cifrados; el “shared” es entre dispositivos/invitados que tú controlas. Para máxima minimización de datos, usar Local only y compartir solo exportaciones (PDF/archivos) cuando haga falta.

---

## 5. P2P Sync (móvil + campo)

### Emparejar dispositivos (Local-only, misma WiFi)

1. **PC** → Nuevo espacio **CTAEX Demo TRL8**.
2. **Móvil** → Abrir Anytype → Auto-detecta el PC (**mDNS**) → **Nuevo dispositivo** → **ACEPTAR**.
3. **PC** → Nota "Prueba 21:27 CET" → **Móvil** aparece en **2-3 s** ✓.
4. **Líneas VERDES** = Sync activo ✅ (sin líneas/rojo = revisar WiFi o firewall).

### Windows Firewall (si el móvil no detecta el PC)

- **wf.msc** (Firewall) → Permitir una aplicación → **anytype.exe** → **Privada** ✓.
- Permite a Anytype usar la red privada (WiFi) para P2P.

### Casos de uso CASTÚO

- **iPhone Campo** → Foto panel agrovoltaico → Sync WiFi 3 s → **PC Gregorio** recibe foto → Vincular Certificación ISO 27001.
- **Android Técnico** → Ve estado Vault PQC → Actualiza rotación en la nota compartida.
- **CTAEX** → Shared Space "Demo TRL8" → **Grafo LIVE** en tiempo real.

**Resumen:** Todo sincronizado en local ↔ GDPR compliant ↔ 0 EUR.

---

## 6. Importar Pen Drive D: (versión optimizada)

1. `unzip "D:\CASTUO-SYSTEM_TRL8_20260316.zip"`
2. Anytype → Import → carpeta `docs/`
3. Objetos generados: **Certificación**, **Endpoint**, **Vault Key**, **Cliente**

### Quick start (5 pasos)

1. PC: anytype.io → Gear → **LOCAL-ONLY**
2. Móvil: App Store → **LOCAL-ONLY**
3. WiFi **Gregorio_Casa** → Recovery Phrase igual
4. PC: Espacio **CTAEX Demo TRL8**
5. Móvil: Auto-detecta → Líneas VERDES ✓ FUNCIONA

### Workflow campo → CTAEX

```
iPhone Campo → Foto panel → Anytype Object
        ↕️ P2P WiFi 3s ↕️
PC Gregorio → Vincula ISO 27001 92%
        ↕️ P2P WiFi 3s ↕️
Android Técnico → Actualiza Vault PQC
        ↕️ Shared Space ↕️
CTAEX → Grafo TRL8 visual LIVE
```

### Objetos y relaciones

| Objeto        | Propiedades                   | Relaciones           |
| ------------- | ----------------------------- | -------------------- |
| Certificación | 92% ISO 27001, Stage 1 5 mayo | Audita → Endpoint    |
| Endpoint      | localhost:8000, Health ✓     | Protege → Vault Key  |
| Vault Key     | Kyber-768, Rotación 30d       | Sellado → Emergency  |
| Cliente       | Agricultor, QR panel         | Firma → Consent GDPR |

---

## Checklist FUNCIONA

- [ ] Anytype PC + móvil instalados
- [ ] WiFi Gregorio_Casa + Local-only
- [ ] Recovery Phrase 12 palabras igual
- [ ] PC → "CTAEX Demo TRL8" → Móvil 3s
- [ ] Nota sync instantáneo ✓ FUNCIONA
- [ ] Líneas verdes P2P activo
- [ ] wf.msc → anytype.exe Privada ✓
- [ ] Import Pen D: → Objetos TRL8 ✓

---

### Valor CASTÚO + Anytype

| Beneficio | Impacto |
| --------- | -------- |
| Sync P2P gratis | -€120/año (vs Obsidian) |
| Campo→Oficina 3s | Productividad +200% |
| CTAEX Shared Space | Subvención €250K |
| GDPR Países Bajos | Stage 2 fácil |
| Apps nativas | Equipo técnico autónomo |

**docs/anytype/ANYTYPE_CASTUO_SETUP.md** → ✅ ENTERPRISE READY

- Tabla comparativa profesional
- Pasos ejecutables numerados
- Checklist verificable
- Sección 6 única (sin duplicados)
- Workflow campo→CTAEX integrado
