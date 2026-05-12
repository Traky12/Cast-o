# Demo en Vivo + Vídeo Tutorial (5 minutos)

Guión técnico para grabar un vídeo demostrativo del dashboard ForestOwnershipToken, incluyendo el proceso de derecho al olvido. Incluye script para la demo en vivo y storyboard para el vídeo tutorial.

**Versión:** 1.0 · **Fecha:** 15/04/2026  
**Audiencia:** Propietarios forestales, técnicos de la Junta de Extremadura, público general.

---

## 1. Guión para el Vídeo Tutorial (5 minutos)

**Título:** *ForestOwnershipToken: Tokenización de Propiedades Forestales en Extremadura*

**Duración:** 5:00 minutos  

**Formato:** Captura de pantalla + voz en off (o locutor en imagen).

**Herramientas recomendadas:**

| Uso | Herramienta |
|-----|-------------|
| Grabación | OBS Studio (gratis) o Camtasia |
| Edición | OpenShot o Adobe Premiere |
| Voz en off | Audacity (grabar) o ElevenLabs (IA) |

### 1.1. Storyboard (minuto a minuto)

| Tiempo | Escena | Acción | Texto (voz en off) |
|--------|--------|--------|--------------------|
| 0:00–0:15 | Portada | Logo Junta de Extremadura + CASTÚO-SYSTEM™. | "Bienvenidos a la demo del sistema ForestOwnershipToken, desarrollado para la Junta de Extremadura." |
| 0:15–0:45 | Introducción | Dashboard principal con mapa de Extremadura y lista de parcelas. | "Este sistema permite tokenizar propiedades forestales con certificaciones PEFC/FSC, calcular subvenciones automáticas y vincularse a mercados de carbono." |
| 0:45–1:30 | Mintado de una parcela | 1. Seleccionar "Tokenizar Parcela". 2. Rellenar formulario (parcela XT-12345-001). 3. Confirmar transacción en MetaMask. | "Vamos a tokenizar una parcela de 1 hectárea en Cáceres con certificaciones PEFC y FSC. El sistema valida los datos con SIGPAC y registra la propiedad en GaiaChain." |
| 1:30–2:15 | Verificación de subvenciones | 1. Seleccionar token recién creado. 2. Clic en "Calcular Subvenciones". 3. Mostrar resultado (€650/ha/año). | "El sistema calcula automáticamente las subvenciones aplicables: €200 de PAC 2040, €150 por PEFC, y €300 por Red Natura 2000, totalizando €650 por hectárea y año." |
| 2:15–3:00 | Vinculación a mercados de carbono | 1. Seleccionar "Mintar Créditos de Carbono". 2. Confirmar transacción. 3. Mostrar créditos generados (5 toneladas CO₂). | "Cada hectárea secuestra 5 toneladas de CO₂ al año. El sistema genera créditos verificables que pueden venderse en mercados como Verra o Gold Standard." |
| 3:00–4:00 | Ejercicio del derecho al olvido | 1. Acceder al módulo de privacidad. 2. Seleccionar token y "Ejercer Derecho al Olvido". 3. Confirmar con OTP. | "El sistema cumple con el GDPR: permite borrar datos personales manteniendo la información catastral obligatoria. Genera un certificado de borrado para el propietario." |
| 4:00–4:45 | Descarga del certificado | 1. Mostrar email recibido con enlace. 2. Descargar PDF del certificado. 3. Mostrar contenido del PDF. | "El propietario recibe un certificado digital que prueba el ejercicio de su derecho al olvido, con el hash de la transacción en GaiaChain para auditoría." |
| 4:45–5:00 | Cierre | Logo Junta + CASTÚO. Texto: "¿Preguntas? Contacte con soporte@castuo-system.com". | "ForestOwnershipToken está listo para implementarse en Extremadura. Para más información, visite nuestra documentación técnica o contacte con nuestro equipo." |

---

## 2. Script para Demo en Vivo

Comandos y pasos para realizar una demo en tiempo real durante una reunión con la Junta.

### 2.1. Preparación del entorno

**Requisitos:**

| Elemento | Detalle |
|----------|---------|
| Dashboard | https://dashboard-test.castuo-system.com (credenciales de prueba) |
| MetaMask | Red GaiaChain Testnet (RPC: https://testnet.gaiachain.castuo-system.com) |
| Cuenta de prueba | 0xTecnicoDemo (1 ETH de prueba para gas) |
| Parcela de prueba | XT-DEMO-001 (pre-cargada con PEFC/FSC) |

**Comandos previos:**

```bash
# 1. Desplegar dashboard local (opcional para demo offline)
cd frontend/extremadura-dashboard
npm run dev

# 2. Asegurar que el backend está operativo (FastAPI)
cd api && uvicorn main:app --reload

# 3. Pre-cargar datos de prueba (opcional)
python3 backend/scripts/load_test_data.py --demo
```

### 2.2. Guión paso a paso

**Paso 1: Introducción (2 min)**  
Mostrar el dashboard principal. Explicar los 4 módulos: Tokenización de parcelas, Cálculo de subvenciones, Mercado de carbono, Privacidad (derecho al olvido).

**Paso 2: Tokenizar una parcela (5 min)**

Comando equivalente (para mostrar en terminal si es demo técnica):

```bash
python3 backend/scripts/mint_certified_forest_property.py \
  0xTecnicoDemo XT-DEMO-001 \
  --coordinates "39.4769°N, 6.3706°W" \
  --area 10000 \
  --species "Quercus ilex,Pinus pinea" \
  --carbon 5000 \
  --certifications PEFC FSC "Red Natura 2000" \
  --upload-ipfs
```

Acciones en el dashboard: seleccionar "Tokenizar Parcela", rellenar formulario (XT-DEMO-001, 1 ha, PEFC/FSC), confirmar en MetaMask. Mostrar Token ID generado y enlace a GaiaChain Explorer.

**Paso 3: Calcular subvenciones (3 min)**  
Ir a "Subvenciones", seleccionar el token recién creado, clic en "Calcular Subvenciones". Mostrar: PAC 2040 €200/ha, PEFC/FSC +€150/ha, Red Natura 2000 +€300/ha, **Total €650/ha/año**.

**Paso 4: Mintar créditos de carbono (3 min)**  
Ir a "Mercado de Carbono", seleccionar token 1, "Mintar Créditos", confirmar en MetaMask. Mostrar: 5 toneladas CO₂/ha (estimado €250/ha/año a €50/tonelada).

**Paso 5: Ejercer derecho al olvido (5 min)**  
Ir al módulo "Privacidad" (`#/privacidad`). Seleccionar token 1, "Ejercer Derecho al Olvido", confirmar con OTP. Mostrar certificado: campos borrados (Propietario, DNI, Email) y mantenidos (parcelaId, coordinates, certifications). Descargar PDF.

**Paso 6: Cierre (2 min)**  
Resumen: legal (GDPR, Ley 3/2023, Decreto 45/2020), económico (€650–€800/ha/año), técnico (trazabilidad GaiaChain). Próximos pasos: acuerdo SIGPAC, despliegue piloto 100 ha.

---

## 3. Storyboard actualizado (incluye móvil)

**Vídeo tutorial:** *ForestOwnershipToken: Tokenización y Reclamación de Subvenciones*  
**Duración:** 5:00 · **Estilo:** Demo práctica + voz en off (tonalidad cercana pero técnica).

| Tiempo | Escena | Acción | Voz en off / texto en pantalla | Recursos visuales |
|--------|--------|--------|--------------------------------|-------------------|
| 0:00–0:15 | Portada | Logo Junta + CASTÚO + título. | "ForestOwnershipToken: Cómo tokenizar tu propiedad forestal y reclamar subvenciones desde cualquier dispositivo." | Fondo: dehesa extremeña + logo. |
| 0:15–0:45 | Introducción | Mapas de Extremadura con parcelas (PEFC/FSC). | "Te mostramos cómo tokenizar tu parcela, calcular subvenciones automáticas y reclamarlas desde tu móvil en solo 3 pasos." | Zoom a parcela XT-DEMO-001 (Cáceres). |
| 0:45–1:30 | Tokenización (PC) | Dashboard: "Tokenizar Parcela", formulario XT-DEMO-001, confirmar MetaMask. | "Tokenizamos la parcela desde el dashboard. Introducimos los datos y confirmamos en MetaMask. En segundos queda registrada en GaiaChain." | Captura formulario + MetaMask. |
| 1:30–2:15 | Cálculo subvenciones (PC) | Seleccionar token, "Calcular Subvenciones", resultado €650/ha. | "€200 PAC 2040, €150 PEFC/FSC, €300 Red Natura 2000. Total: €650 por hectárea y año." | Gráfico de barras. |
| 2:15–3:00 | Reclamación desde móvil | MetaMask en móvil → dashboard → "Reclamar Subvención" → confirmar. | "Desde el móvil: abre MetaMask, entra al dashboard, selecciona tu parcela y 'Reclamar Subvención'. Confirma y los fondos llegan a tu wallet en minutos." | Capturas: MetaMask, dashboard móvil, botón, confirmación. |
| 3:00–3:45 | Mercado de carbono (PC) | "Mintar Créditos de Carbono", confirmar, mostrar 5 t CO₂. | "Tu parcela genera 5 toneladas de CO₂/año. Se tokenizan como créditos que puedes vender en Verra o Gold Standard." | Gráfico créditos + enlace Verra. |
| 3:45–4:30 | Derecho al olvido (PC) | Módulo "Privacidad", token, "Ejercer Derecho al Olvido", OTP. | "Puedes borrar tus datos personales con un clic, generando un certificado de borrado." | Módulo privacidad + PDF certificado. |
| 4:30–5:00 | Cierre | Logo Junta + CASTÚO. "¿Preguntas? soporte@castuo-system.com". | "ForestOwnershipToken está disponible para propietarios forestales de Extremadura. Más información en nuestra web o equipo." | Fondo: bosque + logos. |

### 3.1. Ejemplo de reclamación desde móvil (detalle técnico)

| Elemento | Detalle |
|----------|---------|
| Dispositivo | Android/iOS con MetaMask instalada |
| Navegador | Chrome o Safari actualizado |
| Wallet | MetaMask, red GaiaChain Testnet |
| Cuenta de prueba | 0xTecnicoMovil (1 ETH prueba) |
| Token de prueba | XT-DEMO-001 (PEFC/FSC) |

**Pasos para grabar la secuencia:**  
1. Abrir MetaMask en móvil (GaiaChain Testnet, 1 ETH).  
2. Acceder a https://dashboard-test.juntaextremadura.es desde el navegador.  
3. Conectar wallet, seleccionar parcela XT-DEMO-001 (1 ha, PEFC/FSC, €650/ha).  
4. Clic en "Reclamar Subvención", confirmar en MetaMask (~0.01 ETH gas).  
5. Mostrar transacción exitosa y saldo en SubsidyToken.

**Capturas para el vídeo (esquema):**

```
+-------------------------------------+  +-------------------------------------+
|  📱 Pantalla 1: MetaMask             |  |  🌐 Pantalla 2: Dashboard móvil     |
|  Red: GaiaChain Testnet             |  |  Token: XT-DEMO-001                 |
|  Saldo: 1 ETH                       |  |  Subvención: €650/ha                |
|  Cuenta: 0xTecnicoMovil             |  |  Botón: "Reclamar Subvención"       |
+-------------------------------------+  +-------------------------------------+

+-------------------------------------+  +-------------------------------------+
|  📱 Pantalla 3: Confirmación        |  |  ✅ Pantalla 4: Transacción OK       |
|  MetaMask: Confirmar transacción    |  |  Tx: 0x123...abc                    |
|  Gas: 0.01 ETH                     |  |  Estado: "Éxito"                    |
+-------------------------------------+  +-------------------------------------+
```

**Comandos para simular entorno móvil:**

```bash
# Frontend accesible desde la red local (móvil en la misma WiFi)
cd frontend/extremadura-dashboard && npm run start -- --host
# Acceder desde móvil: http://<IP_LOCAL>:3000

# Cargar datos de prueba para demo móvil
python3 backend/scripts/load_test_data.py --demo --mobile
```

**Simulación de reclamación (backend):**

```bash
curl -X POST http://localhost:8000/api/subsidies/claim \
  -H "Content-Type: application/json" \
  -d '{"tokenId": 1, "walletAddress": "0xTecnicoMovil"}'
```

*(Nota: el endpoint `/api/subsidies/claim` debe estar implementado en la API; ver documentación técnica.)*

---

## 4. Grabación del vídeo tutorial

### 4.1. Configuración recomendada

| Elemento | Recomendación |
|----------|----------------|
| Resolución | 1920×1080 (Full HD) |
| FPS | 30 |
| Micrófono | Blue Yeti o equivalente (voz en off) |
| Software | OBS Studio (grabación) + OpenShot (edición) |
| Fondo | Logo Junta + CASTÚO-SYSTEM™ (plantilla adjunta) |

### 4.2. Script de voz en off (texto completo)

> "Bienvenidos a la demostración del sistema ForestOwnershipToken, desarrollado por CASTÚO-SYSTEM™ en colaboración con la Junta de Extremadura.
>
> En este vídeo mostraremos cómo tokenizar una propiedad forestal con certificaciones PEFC y FSC, calcular subvenciones automáticas y ejercer el derecho al olvido según el GDPR.
>
> **Paso 1: Tokenización.** Accedemos al dashboard en dashboard-test.castuo-system.com. Seleccionamos 'Tokenizar Parcela' y rellenamos: Parcela ID XT-DEMO-001, certificaciones PEFC, FSC y Red Natura 2000. El sistema valida con SIGPAC y registra la propiedad en GaiaChain.
>
> **Paso 2: Subvenciones.** Para esta parcela de 1 hectárea: 200 euros del PAC 2040, 150 por PEFC y FSC, 300 por Red Natura 2000. Total: 650 euros por hectárea y año, vinculados al token.
>
> **Paso 3: Carbono.** La parcela secuestra 5 toneladas de CO₂ al año. El sistema genera créditos verificables para mercados como Verra o Gold Standard, unos 250 euros más por hectárea.
>
> **Paso 4: Derecho al olvido.** El propietario puede ejercerlo con un clic. Se borran datos personales y se mantiene la información catastral obligatoria, generando certificado de borrado para auditoría.
>
> ForestOwnershipToken está listo para Extremadura: trazabilidad, cumplimiento normativo y nuevos ingresos para propietarios forestales. Para más información: documentación técnica o soporte@castuo-system.com."

### 4.3. Edición

- Introducción 0:00–0:15: logo + voz.  
- Demo 0:15–4:00: capturas con explicaciones.  
- Cierre 4:00–5:00: logo + contacto.  
- Transiciones: fundido entre escenas.  
- Texto en pantalla: destacar €650/ha y 5 t CO₂.  
- Música: libre de derechos (ej. YouTube Audio Library).

---

## 5. Documentación legal y técnica para grabación

Cumplimiento con **GDPR**, **Ley 34/2002 (LSSI)** y **Ley 7/2010 (Comunicación Audiovisual)**.

### 5.1. Protocolo legal de grabación

**Consentimientos obligatorios:**

- **Consentimiento de imagen y voz** (locutores/actores): uso exclusivo para formación ForestOwnershipToken; duración 5 años (renovable); derecho a revocación (Art. 7 GDPR). Plantilla: [docs/junta-extremadura/legal/consentimiento_imagen_voz.md](legal/consentimiento_imagen_voz.md).

**Registro de grabación (auditoría):**

```markdown
**REGISTRO DE GRABACIÓN Nº: GRAB-2026-04-15-001**
- **Fecha:** 15/04/2026
- **Hora inicio:** 10:00 · **Hora fin:** 11:30
- **Ubicación:** Oficina CASTÚO-SYSTEM™ (Cáceres)
- **Equipo presente:** Gregorio Jiménez Bodes (Responsable), María López (Técnica), Juan Pérez (Locutor)
- **Material:** Vídeo tutorial 5 min, tomas alternativas 10 min
- **Almacenamiento:** Servidor local (cifrado AES-256), copia en IPFS (hash: QmXoypiz...)
- **Firma del responsable:** ________________________
```

**LSSI (Ley 34/2002):** Identificación clara de Junta de Extremadura y CASTÚO-SYSTEM™; información sobre cookies si hay tracking; derecho de oposición (politica-privacidad@juntaex.es). Texto legal en vídeo (0:00–0:05):

> "Este vídeo ha sido producido por la Junta de Extremadura y CASTÚO-SYSTEM™ con fines formativos. Para más información sobre protección de datos: juntaex.es/privacidad."

### 5.2. Guion simplificado para propietarios forestales

Versión sin tecnicismos, beneficios prácticos.

| Tiempo | Escena | Voz en off (lenguaje sencillo) | Visual |
|--------|--------|--------------------------------|--------|
| 0:00–0:15 | Portada | "Hola, soy [Nombre]. Hoy te muestro cómo recibir tus ayudas forestales de forma rápida y segura desde tu móvil." | Logo Junta + CASTÚO + dehesa. |
| 0:15–0:45 | Introducción | "Si tienes una finca forestal en Extremadura, este sistema te permite cobrar subvenciones sin papeleos, con el móvil." | Mapa Extremadura + iconos árboles y euros. |
| 0:45–1:30 | Tokenización (PC) | "Primero registramos tu finca: número de parcela y certificados (PEFC o FSC)." | Formulario: parcela, certificados, hectáreas. |
| 1:30–2:15 | Subvenciones (PC) | "El sistema calcula cuánto te corresponde. Con PEFC y Red Natura puedes recibir hasta 650 euros por hectárea al año." | Barras: PAC 200€, PEFC +150€, Red Natura +300€. |
| 2:15–3:00 | Reclamación móvil | "Para cobrar: abre MetaMask, entra al dashboard de la Junta, selecciona tu parcela y 'Cobrar ayuda'. En segundos el dinero llega a tu wallet." | Secuencia: MetaMask → dashboard → "Cobrar ayuda" → confirmación. |
| 3:00–3:45 | Carbono (PC) | "Tu finca genera créditos de carbono que también puedes vender: 5 toneladas de CO₂ por hectárea, unos 250 euros más." | Árboles + CO₂ + icono euros. |
| 3:45–4:30 | Derecho al olvido (PC) | "Si quieres que borremos tus datos personales, un clic. El sistema genera un certificado de borrado." | Botón "Borrar mis datos" + PDF certificado. |
| 4:30–5:00 | Cierre | "Cobrar tus ayudas es fácil, rápido y seguro. Dudas: oficina comarcal de la Junta." | Logo Junta + teléfono 927 00 00 00. |

**Diálogo clave (reclamación desde móvil, 2:15–3:00):**

> "Vamos a cobrar tus ayudas desde el móvil, paso a paso. Abre la app MetaMask. Entra al dashboard de la Junta, dashboard.juntaextremadura.es. Selecciona tu parcela; verás tu ayuda calculada, por ejemplo 650 euros por hectárea. Pulsa 'Cobrar ayuda' y confirma en MetaMask. En segundos el dinero está en tu wallet. Sin papeleos, sin esperas."

### 5.3. Configuración técnica con cumplimiento legal

| Elemento | Requisito legal | Implementación |
|----------|----------------|----------------|
| Consentimiento grabado | LSSI y GDPR Art. 7 | Audio al inicio: "Consiento la grabación de este vídeo para fines formativos." |
| Almacenamiento | GDPR Art. 32 | Vídeos cifrados (AES-256); copia en IPFS (hash en registro). |
| Registro de acceso | Ley 7/2010 | Log de accesos (IP, fecha, usuario). |
| Derecho de oposición | GDPR Art. 21 | En vídeo: "Para ejercer sus derechos: dpo@juntaex.es". |

### 5.4. Comandos para grabación (cumplimiento legal)

```bash
# 1. Iniciar grabación con marca de agua (LSSI)
# En OBS: añadir fuente de texto "Junta de Extremadura - Uso formativo"

# 2. Metadatos legales en el archivo (ffmpeg)
ffmpeg -i video_20260415.mp4 \
  -metadata title="ForestOwnershipToken - Demo para propietarios forestales" \
  -metadata copyright="Junta de Extremadura 2026" \
  -metadata comment="Grabado bajo consentimiento GDPR-2026-04-15" \
  -c:v libx264 -c:a aac \
  video_final.mp4

# 3. Subir a IPFS para registro inmutable
ipfs add video_final.mp4
# Ejemplo: QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco
```

### 5.5. Plantilla de registro de grabación (JSON)

Archivo: `docs/junta-extremadura/legal/registro_grabacion_20260415.json` (ver [legal/registro_grabacion_20260415.json](legal/registro_grabacion_20260415.json)).

---

## 6. Cumplimiento legal para publicación en YouTube

### 6.1. Checklist previo a la subida

| Requisito | Acción | Responsable | Estado |
|-----------|--------|-------------|--------|
| Consentimientos firmados | Archivar en docs/legal/consentimientos/ | Gregorio | ☐ |
| Registro de grabación | Guardar JSON; opcional IPFS | María López | ☐ |
| Marca de agua | "Junta de Extremadura - Uso formativo" | Equipo técnico | ☐ |
| Metadatos en vídeo | ffmpeg (copyright, uso permitido) | Gregorio | ☐ |
| Política de privacidad | Enlace en descripción: juntaex.es/privacidad | Junta | ☐ |
| Privacidad del vídeo | Privado (solo con enlace) | Gregorio | ☐ |
| Registro de acceso | Logs en YouTube Studio | Junta | ☐ |

### 6.2. Texto legal para la descripción de YouTube

(Copiar/pegar en la descripción del vídeo.)

```text
📌 ForestOwnershipToken: Tutorial para Propietarios Forestales
Este vídeo ha sido producido por la Junta de Extremadura y CASTÚO-SYSTEM™ con fines exclusivamente formativos.

🔹 Derechos de uso: Formación para propietarios forestales de Extremadura. Prohibida su reproducción o distribución sin autorización.

🔹 Protección de datos: Para ejercer sus derechos (acceso, rectificación, olvido), contacte con: dpo@juntaex.es. Más información: juntaex.es/privacidad

🔹 Contacto: Soporte técnico soporte@castuo-system.com · Junta de Extremadura 927 00 00 00

© Junta de Extremadura, 2026. Todos los derechos reservados.
```

---

## 7. Materiales adjuntos

| Material | Ubicación / descripción |
|----------|-------------------------|
| Plantilla portadas | Canva: logo Junta + CASTÚO |
| Datos de prueba | Parcela XT-DEMO-001 (1 ha, PEFC/FSC, €650/ha); créditos 5 t CO₂/año |
| Script carga datos | [backend/scripts/load_test_data.py](../../backend/scripts/load_test_data.py) `--demo` |
| Script demo móvil | [backend/scripts/load_demo_data.py](../../backend/scripts/load_demo_data.py) `--mobile` |
| Consentimiento imagen/voz | [legal/consentimiento_imagen_voz.md](legal/consentimiento_imagen_voz.md) |
| Registro de grabación | [legal/registro_grabacion_20260415.json](legal/registro_grabacion_20260415.json) |
| Guion simplificado PDF | Exportar §5.2 con Pandoc a guion_simplificado_propietarios.pdf |

---

## 8. Checklist final para demo/vídeo

| Item | Responsable | Estado | Notas |
|------|-------------|--------|-------|
| Dashboard desplegado en testnet | Equipo técnico | ☐ | URL: https://dashboard-test... |
| Cuenta MetaMask configurada | Gregorio | ☐ | 0xTecnicoMovil (1 ETH) |
| Datos de prueba cargados | Equipo técnico | ☐ | Parcela XT-DEMO-001 |
| Script de demo probado | Gregorio | ☐ | Comandos §2.1 y §2.2 |
| Equipos de grabación listos | Junta | ☐ | Cámaras + micrófonos |
| Conexión a internet estable | Junta | ☐ | Mín. 50 Mbps |
| Guion impreso para locutor | Gregorio | ☐ | Versión final adjunta |
| Copia de seguridad del dashboard | Equipo técnico | ☐ | Backup en IPFS |

---

## 9. Resumen ejecutivo para la Junta

**Documentos listos para enviar:**

- **Vídeo tutorial (5 min):** Enlace privado YouTube (sustituir por el real); hash IPFS para auditoría.
- **Documentación legal:** Consentimientos, registro de grabación, informe cumplimiento LSSI/GDPR.
- **Guion simplificado:** PDF para propietarios forestales.
- **Checklist de publicación** en YouTube.

**Próximos pasos:**

1. Revisión legal por Asesoría Jurídica de la Junta (plazo: 5 días).  
2. Aprobación final del vídeo (firma digital del DPO).  
3. Publicación en YouTube (privado) y envío del enlace a propietarios piloto.

---

[← Documentación final de envío](DOCUMENTACION_FINAL_ENVIO_JUNTA.md) · [Plan de formación técnicos](PLAN_FORMACION_TECNICOS.md)
