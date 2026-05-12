# Guía de Ejecución para Windows (CASTÚO-SYSTEM)

**Versión:** 1.2.1  
**Fecha:** 16/03/2026  
**Objetivo:** Ejecutar scripts PowerShell sin fricciones en entornos Windows.

**Referencia cruzada:** Alineado con el **Prontuario Maestro v1.2.1** — [`docs/PRONTUARIO_MAESTRO_ESCALADO_TRL9_TRL13.md`](../../PRONTUARIO_MAESTRO_ESCALADO_TRL9_TRL13.md) (§14.2 Runbook Express, §17.2 despliegue seguro, §17.3 conectividad UE).

**Resumen operativo:** entorno Windows → estructura + **PDFs legales** → token Hetzner en variable de entorno → **`deploy_hetzner.ps1`** (`docker compose` V2) → comprobación HTTP; incidencias: *Runbook* (~15 min) y [emergencia](#procedimiento-de-emergencia-si-todo-falla) si el fallo persiste.

### Índice

| Área | Enlace |
|------|--------|
| Requisitos y ejecución base | [Requisitos previos](#requisitos-previos) · [Instrucciones de ejecución](#instrucciones-de-ejecución) |
| Mapa v1.2.1 | [Estado final del repositorio](#estado-final-del-repositorio-v121) |
| Docker / emergencia | [Ajustes técnicos: Docker y emergencia](#ajustes-técnicos-aplicados-docker-y-emergencia) |
| CTAEX y 7 días | [Flujo de trabajo depurado](#flujo-de-trabajo-depurado-próximos-7-días) |
| Incidencias | [Runbook (15 min)](#runbook-express--runbook-de-incidencias-15-minutos) · [Emergencia](#procedimiento-de-emergencia-si-todo-falla) |
| Cumplimiento | [Marco legal y técnico](#cumplimiento-legal-y-técnico-marco-verificable) |

### Reglas de seguridad (aplicación continua)

- **Secretos:** `HETZNER_API_TOKEN` y claves **solo** en sesión actual, perfil cifrado o **GitHub Secrets**; nunca en commits, issues ni capturas. Los scripts evitan volcar el token; no añadas `Write-Host $env:HETZNER_API_TOKEN`.
- **PowerShell vs bash:** `<< 'EOF'` es sintaxis **bash**; en Windows usa `plink` y ejecuta bloques **bash** ya *dentro* del servidor.
- **Datos en disco:** `docker system prune -a --volumes -f` puede borrar volúmenes; en **producción** exige backups verificados y decisión explícita.

---

## Requisitos previos

| Herramienta | Versión mínima | Descarga | Notas |
|-------------|----------------|----------|-------|
| PowerShell | 5.1+ | Preinstalado en Windows 10/11 | Ejecutar como **Administrador** al instalar dependencias. |
| Pandoc | 3.1+ | [pandoc.org](https://pandoc.org/installing.html) | Marcar **Añadir Pandoc al PATH**. |
| MiKTeX | 23.3+ | [miktex.org](https://miktex.org/download) | Necesario para PDF con `pdflatex`. |
| LibreOffice | 7.5+ | [libreoffice.org](https://www.libreoffice.org) | Opcional; el DOCX del flujo actual lo genera **Pandoc** (`--reference-doc`). |
| PuTTY / plink | 0.78+ | [PuTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) | Requerido para `deploy_hetzner.ps1`; opcional `PLINK_PATH` si no está en Program Files. |
| Git | 2.39+ | [git-scm.com](https://git-scm.com/downloads) | Clonar repositorio. |

---

## Instrucciones de ejecución

### 1. Configuración inicial

```powershell
git clone https://github.com/tu-usuario/castuo-system.git
cd castuo-system

Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
Get-ChildItem scripts\*.ps1 | Unblock-File
```

### 2. Estructura y documentos legales (PDF / DOCX)

```powershell
.\scripts\Setup-RepoStructure.ps1
.\scripts\Generate-LegalPdfs.ps1
Get-ChildItem docs\legal\TRL10\pdfs\*.pdf
```

### 3. Variables de entorno (Hetzner)

```powershell
$env:HETZNER_API_TOKEN = "tu_token_aqui"

# Opcional
# $env:SSH_KEY_PATH = "$env:USERPROFILE\.ssh\id_rsa.pub"
# $env:SSH_PRIVATE_KEY_PATH = "$env:USERPROFILE\.ssh\id_rsa"
# $env:PLINK_PATH = "C:\Program Files\PuTTY\plink.exe"
# $env:DOMAIN_NAME = "tu-dominio.com"
# $env:CONTACT_EMAIL = "admin@castuo-system.com"
```

Definir el token **solo en la sesión actual** o vía **SecretManagement** / **GitHub Secrets** en CI; evita dejarlo fijo en perfiles `.ps1` en texto plano.

### 4. Despliegue

```powershell
.\scripts\deploy_hetzner.ps1 -Verbose
```

### 5. Verificación post-despliegue

```powershell
$serverIp = (Get-Content .hetzner_ip | Select-Object -First 1).Trim()
Invoke-WebRequest -Uri "http://${serverIp}:3000" -UseBasicParsing
Invoke-WebRequest -Uri "http://${serverIp}:8000/health" -UseBasicParsing
```

*Si `.hetzner_ip` tuviera líneas en blanco o espacios, `Trim()` evita URLs rotas.*

---

## Estado final del repositorio (v1.2.1)

*(Estructura verificada y ejecutable; sin claims legales absolutos en la guía técnica.)*

| Documento | Versión | Ubicación | Propósito |
|-----------|---------|-----------|-----------|
| Prontuario Maestro | 1.2.1 | `docs/PRONTUARIO_MAESTRO_ESCALADO_TRL9_TRL13.md` | Hoja de ruta técnica/legal (sin claims absolutos) |
| Guía Windows + Runbook | 1.2 | `docs/legal/TRL10/README_WINDOWS.md` | Instrucciones PowerShell + Runbook de incidencias (15 min) |
| Despliegue Hetzner (PS) | 1.2 | `scripts/deploy_hetzner.ps1` | Despliegue seguro (validaciones + manejo de errores) |
| Despliegue Hetzner (Linux) | — | `scripts/deploy_hetzner.sh` | Alternativa Bash |
| Contrato CTAEX | Final | `docs/legal/TRL10/pdfs/contrato_ctaex_*.pdf` | Documento legal para firma (eIDAS 2, GDPR, RD 903/2025) |
| Checklist ISO 9001 | 1.0 | `docs/legal/TRL10/checklist_iso_9001_2025.md` | Cláusulas 4–10 (30+ ítems) + nota para anexo futuro |
| Conectividad UE (borrador) | — | `docs/architecture/TRL10-CONEC-EU-SATELIOT-NEXTEPC-ARSYS.md` | NTN / 5G / IoT; GEMelo-céntrico (`sateliot_gemelo_bridge.py`, `gemelo-centric.yml`); DPIA §4.1 |

---

## Cambios clave aplicados (v1.2.1)

- **Lenguaje legal preciso** en tablas de cumplimiento: marcos normativos + evidencias; sin “100% legal” ni “garantizado” en documentación técnica.
- **Runbook:** título unificado *Runbook Express / Runbook de incidencias*; el prontuario §14.2 enlaza aquí.
- **Comandos válidos:** conexión `plink` desde PowerShell y **bash en el servidor**; **nunca** `<< 'EOF'` en PowerShell.
- **`deploy_hetzner.ps1` v1.2:** prerequisitos, API, plink, claves SSH, token no volcado en log.
- **ISO 9001:** checklist alineado al artefacto (cláusulas 4–10); núcleo estable; ampliación tipo “62 acciones” como anexo futuro si CTAEX o el consultor lo requieren.
- **Desarrollo vs producción:** `docker system prune` sin `-f` en dev para revisar el alcance; `prune -f` solo con backups; `--build` cuando proceda reconstruir imágenes (el script de despliegue no lo fuerza por defecto).
- **Conectividad UE (TRL10):** prontuario §17.3 + `docs/architecture/TRL10-CONEC-EU-SATELIOT-NEXTEPC-ARSYS.md`; modo **GEMelo-céntrico:** `sateliot_gemelo_bridge.py` + `scripts/gemelo-centric.yml`; alternativa MQTT `sateliot_bridge.py` / `arsys_bridge.py`; plantilla `docker/nextepc-compose.template.yml` (validar imágenes y DPAs antes de producción).

---

## Ajustes técnicos aplicados: Docker y emergencia

### Docker Compose V2

Uso consistente de **`docker compose`** (sin guión) en los scripts de despliegue y en esta documentación:

```bash
docker compose -f docker-compose.prod.yml up -d   # V2 (sin guión)
```

**Nota sobre compatibilidad:**

- El script **`deploy_hetzner.ps1`** usa **Docker Compose V2** (`docker compose`) por defecto.
- Si el servidor solo tiene el **plugin V2** (sin el binario `docker-compose`), usar **`docker compose`** (sin guión).
- Si solo existe el binario **`docker-compose`** (legacy), suele ser equivalente; prioriza **`docker compose`** cuando el plugin esté instalado (`docker compose version`).

### `docker system prune` con `-f`

Limpieza forzada en el runbook de emergencia:

```bash
docker system prune -a --volumes -f   # -f para evitar confirmación interactiva
```

**Advertencia:**

- El flag **`-f`** evita la confirmación interactiva.
- **Solo usar en producción con backups verificados** (borra imágenes/volúmenes no usados).
- En entornos de **desarrollo**, omitir **`-f`** para revisar qué se eliminará.

### Bloque de referencia (bash, en el servidor)

```bash
# Dentro del servidor (bash):
cd /opt/castuo-system
docker compose -f docker-compose.prod.yml down      # V2 (preferido)
docker system prune -a --volumes -f                  # Limpieza forzada
git pull
docker compose -f docker-compose.prod.yml up -d     # V2 (sin --build)
```

**Nota sobre `--build`:**

- Si necesitas reconstruir imágenes (p. ej. cambios en Dockerfiles), añade **`--build`**:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

El script **`deploy_hetzner.ps1`** **no** incluye `--build` por defecto (asume imágenes vía `pull` / registro, alineado con `docker compose … up -d`).

*Si no existe el plugin V2, sustituye `docker compose` por `docker-compose` en todos los pasos.*

---

## Estructura de repositorio (referencia)

```text
castuo-system/
├── docs/
│   ├── PRONTUARIO_MAESTRO_ESCALADO_TRL9_TRL13.md
│   └── legal/TRL10/
│       ├── README_WINDOWS.md
│       ├── pdfs/
│       ├── contrato_ctaex_*.md
│       ├── sla_20260320.md
│       ├── politica_privacidad_gdpr_2026.md
│       ├── terminos_servicio_suscripciones.md
│       └── checklist_iso_9001_2025.md
└── scripts/
    ├── Generate-LegalPdfs.ps1
    ├── Setup-RepoStructure.ps1
    ├── deploy_hetzner.ps1
    └── deploy_hetzner.sh
```

---

## Flujo de trabajo depurado (próximos 7 días)

### Paso 1: Firma del contrato con CTAEX

```powershell
Invoke-Item docs\legal\TRL10\pdfs\contrato_ctaex_final_20260320.pdf
# Firma con DocuSign/Adobe Acrobat y envía los 3 PDFs (plantilla abajo).
```

Firma digital (DocuSign, Adobe Acrobat u otro flujo acordado con asesoría). **Confirmar** destinatario y canal oficial antes de enviar datos sensibles.

**Plantilla de correo (ajustar destinatario):**

- **Asunto:** `Envío de documentación contractual - Proyecto CT-2026-001`
- **Cuerpo:**  
  *Adjunto encontrarán la documentación técnica y legal revisada para el proyecto CASTÚO-SYSTEM TRL9. Quedamos a la espera de su confirmación para proceder con la firma.*

**Adjuntos típicos** (tras `Generate-LegalPdfs.ps1`; nombres según salida real en `pdfs/`):

- `contrato_ctaex_final_20260320.pdf`
- `sla_20260320.pdf`
- `politica_privacidad_gdpr_2026.pdf`

### Paso 2: Despliegue en Hetzner Cloud

```powershell
$env:HETZNER_API_TOKEN = "tu_token_seguro_2026"
.\scripts\deploy_hetzner.ps1 -Verbose
$serverIp = (Get-Content .hetzner_ip | Select-Object -First 1).Trim()
Invoke-WebRequest -Uri "http://$serverIp:3000" -UseBasicParsing   # Frontend (PS 5.1: -UseBasicParsing recomendado)
Invoke-WebRequest -Uri "http://$serverIp:8000/health" -UseBasicParsing   # Backend
```

### Paso 3: Inicio del proceso ISO 9001

```powershell
Invoke-Item docs\legal\TRL10\checklist_iso_9001_2025.md
# Contrata consultor (ej: AENOR) y asigna responsables (Calidad, DevOps, RRHH).
```

Consultor externo (p. ej. AENOR u otro). Responsables sugeridos:

- **Documentación / calidad:** `Setup-RepoStructure.ps1` y mantenimiento de `docs/legal/`.
- **Auditoría interna:** DevOps.
- **Formación:** RRHH.

### Paso 4: Configuración de CI/CD

Crear `.github/workflows/deploy.yml`. Usar **GitHub Secrets** para token y claves; no valores en claro. En `ubuntu-latest` el despliegue real suele ser **SSH**, **API Hetzner** o **runner self-hosted** con PowerShell; no depender de `plink` en Linux.

```yaml
# .github/workflows/deploy.yml
name: Deploy to Hetzner
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Hetzner
        run: |
          # Ilustración (runner Windows / paso pwsh): secrets + script local
          # $env:HETZNER_API_TOKEN = "${{ secrets.HETZNER_API_TOKEN }}"
          # .\scripts\deploy_hetzner.ps1 -Verbose
          # Nota: En ubuntu-latest, usar SSH/API en lugar de plink.
          echo "Sustituir por pasos reales (ssh, scp, docker compose remoto, etc.)."
```

---

## Runbook Express / Runbook de incidencias (15 minutos)

*El prontuario §14.2 enlaza aquí como referencia operativa inmediata.*

### Triage rápido

| Problema | Diagnóstico | Solución rápida | Escalar a |
|----------|-------------|-----------------|-----------|
| PDFs no se generan | `pandoc --version` | Instalar Pandoc/MiKTeX; `.\scripts\Generate-LegalPdfs.ps1 -Verbose` | [Emergencia](#procedimiento-de-emergencia-si-todo-falla) |
| Error en despliegue | `Test-NetConnection` puerto 22 | Token definido **sin imprimirlo**; comprobar red | Reinicio desde Hetzner Console |
| SSH falla | `Test-Path "$env:USERPROFILE\.ssh\id_rsa"` | `ssh-keygen -t rsa -b 4096`; clave en Hetzner | Firewall / SSH Keys |
| Contenedores caídos | En servidor: `docker ps -a` | `docker restart` de servicios afectados | Backup según política |
| Certbot / SSL | `Invoke-WebRequest "http://$serverIp:80"` | En servidor: `certbot --dry-run`; DNS | DNS + Nginx |

#### Criterios de escalado (alineado con prontuario §14.2)

- **Nivel 1 — Operativo:** tabla anterior + secciones *Detalle* de esta guía.
- **Nivel 2 — DevOps:** si >15 min sin resolución, [procedimiento de emergencia](#procedimiento-de-emergencia-si-todo-falla) y revisión de logs `-Verbose`.
- **Nivel 3 — Externo:** soporte Hetzner (infra) o consultor ISO / legal según naturaleza del incidente.

### Comandos válidos (sin `<< 'EOF'` en PowerShell)

**No** uses heredoc `<< 'EOF'` en PowerShell. **Opción A:** `plink` interactivo y luego bash en el servidor (véase [Procedimiento de emergencia](#procedimiento-de-emergencia-si-todo-falla)). **Ejemplo mínimo:**

```powershell
# 1. Reiniciar servidor desde Hetzner Console si aplica.
# 2. Conéctate al servidor (luego ejecuta el bloque bash en la sesión remota):
$plinkExe = if ($env:PLINK_PATH) { $env:PLINK_PATH } else { "$env:ProgramFiles\PuTTY\plink.exe" }
$ipHost = "root@$((Get-Content .hetzner_ip | Select-Object -First 1).Trim())"
& $plinkExe -i "$env:USERPROFILE\.ssh\id_rsa" $ipHost
```

**Dentro del servidor (bash)** — mismo [bloque de referencia](#ajustes-técnicos-aplicados-docker-y-emergencia): **V2**, **`prune -f`** solo con backups verificados.

```bash
cd /opt/castuo-system
docker compose -f docker-compose.prod.yml down
docker system prune -a --volumes -f
git pull
docker compose -f docker-compose.prod.yml up -d     # V2 (sin --build)
```

- *Legacy:* `docker-compose` si no hay subcomando `compose`.
- *Rebuild:* `up -d --build` (véase **Nota sobre `--build`** en *Ajustes técnicos aplicados: Docker y emergencia*).


**Opción B:** comando remoto acotado (sin sesión interactiva):

```powershell
$plink = if ($env:PLINK_PATH) { $env:PLINK_PATH } else { "$env:ProgramFiles\PuTTY\plink.exe" }
$key = "$env:USERPROFILE\.ssh\id_rsa"
$ip = (Get-Content .hetzner_ip | Select-Object -First 1).Trim()
$remote = "cd /opt/castuo-system && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d"
& $plink -i $key -batch "root@$ip" "bash -lc '$remote'"
```

Ajusta rutas y nombres de servicios según tu `docker-compose.prod.yml`. Cualquier `prune` forzado (`-f`) implica riesgo de datos: solo con backups verificados.

---

### Detalle: `Generate-LegalPdfs.ps1`

| Síntoma | Causa probable | Solución rápida | Verificación |
|---------|----------------|-----------------|--------------|
| Pandoc no encontrado | PATH | Reinstalar Pandoc | `pandoc --version` |
| PDF falla | `pdflatex` | MiKTeX | `pdflatex --version` |
| DOCX / plantilla | `legal_template.docx` | Dejar que el script genere o crear plantilla | `Test-Path scripts\legal_template.docx` |
| Encoding | UTF-8 | Guardar `.md` en UTF-8 | `Get-Content ... -Encoding UTF8 -TotalCount 3` |

```powershell
pandoc --version
"# Prueba" | Out-File test.md -Encoding utf8
pandoc test.md -o test.pdf --pdf-engine=pdflatex
```

---

### Detalle: `deploy_hetzner.ps1`

| Síntoma | Causa probable | Solución rápida |
|---------|----------------|-----------------|
| plink no encontrado | PuTTY | `$env:PLINK_PATH` |
| API error | Token / permisos | Regenerar token; no loguear el secreto |
| SSH timeout | Arranque / firewall | Consola Hetzner |

```powershell
$null -ne $env:HETZNER_API_TOKEN
$headers = @{ Authorization = "Bearer $($env:HETZNER_API_TOKEN)" }
Invoke-RestMethod -Uri "https://api.hetzner.cloud/v1/servers" -Headers $headers
if (Test-Path .hetzner_ip) {
  $ip = (Get-Content .hetzner_ip | Select-Object -First 1).Trim()
  Test-NetConnection -ComputerName $ip -Port 22
}
```

---

### Detalle: SSH (plink)

```powershell
$ip = (Get-Content .hetzner_ip | Select-Object -First 1).Trim()
$plinkExe = if ($env:PLINK_PATH) { $env:PLINK_PATH } else { "$env:ProgramFiles\PuTTY\plink.exe" }
& $plinkExe -i "$env:USERPROFILE\.ssh\id_rsa" -batch "root@$ip" "echo ok"
```

---

### Detalle: contenedores (en el servidor)

```bash
docker ps -a
docker compose -f docker-compose.prod.yml logs --tail 50
```

---

### Detalle: SSL / Certbot (en el servidor)

| Síntoma | Acción |
|---------|--------|
| certbot ausente | `apt-get install -y certbot python3-certbot-nginx` |
| DNS | `nslookup tu-dominio.com` |
| Rate limit | `certbot --dry-run` |

---

## Cumplimiento legal y técnico (marco verificable)

Redacción deliberadamente **no** prometedora (“100% legal”, “garantizado”): el alcance jurídico depende de revisión profesional y de lo firmado por las partes.

| Área | Medida | Documento / evidencia | Normativa aplicable (marco) |
|------|--------|-------------------------|----------------------------|
| Contratos | Firmas digitales / archivo de PDF (trazabilidad de versiones) | `docs/legal/TRL10/pdfs/*` | eIDAS 2; Reglamento (UE) n.º 910/2014 (marco); derecho civil aplicable |
| Despliegue | Validaciones previas, secretos por entorno, logs `-Verbose` | `scripts/deploy_hetzner.ps1` v1.2 | Buenas prácticas; ISO 27001 como **objetivo** de gobernanza |
| Datos personales | Política y minimización | `politica_privacidad_gdpr_2026.md` | GDPR (UE 2016/679) |
| Trazabilidad agronómica | Cadena y certificados (donde implementado) | GaiaChain, módulos backend | RD 903/2025 (donde aplique) |
| Calidad | Checklist cláusulas 4–10 | `checklist_iso_9001_2025.md` | ISO 9001:2025 como **objetivo** de certificación |

*Validez jurídica y encaje normativo: revisión caso por caso con asesoría.*

---

## Próximos pasos críticos (7 días)

| Acción | Plazo | Responsable | Resultado | Documentación |
|--------|-------|-------------|-----------|---------------|
| Firmar contrato CTAEX | 2 días | Gregorio | Acuerdo activo | `pdfs/contrato_ctaex_final_*.pdf` |
| Desplegar Hetzner | 3 días | Equipo técnico | Nube operativa | `deploy_hetzner.ps1` |
| Iniciar ISO 9001 | 1 día | Consultor | Plan | `checklist_iso_9001_2025.md` |
| CI/CD | 2 días | DevOps | Pipeline | `.github/workflows/` |
| Webinar / stakeholders | 7 días | Marketing | Sesión registrada | `docs/presentaciones/` (crear si aplica) |

---

## Comandos útiles

```powershell
pandoc --version
pdflatex --version
where.exe plink
git --version
$env:Path -split ';'

.\scripts\Setup-RepoStructure.ps1 -Verbose
.\scripts\Generate-LegalPdfs.ps1 -Verbose
.\scripts\deploy_hetzner.ps1 -Verbose
```

---

## Documentos generados (salidas)

| Script | Salida | Ubicación |
|--------|--------|-----------|
| `Setup-RepoStructure.ps1` | Carpetas base | `docs/legal/`, `scripts/` |
| `Generate-LegalPdfs.ps1` | PDF + DOCX | `docs/legal/TRL10/pdfs/` |
| `deploy_hetzner.ps1` | Servidor + bootstrap | `.hetzner_ip` en la raíz del repo |

---

## Procedimiento de emergencia (si todo falla)

### 🚨 Procedimiento de emergencia

1. **Reiniciar servidor** desde [Hetzner Console](https://console.hetzner.cloud).
2. **Reconstruir contenedores** — conectar por **SSH desde Windows** con `plink` (**nunca** `<< 'EOF'` en PowerShell):

```powershell
# Conéctate al servidor (PowerShell). Si PuTTY no está en Program Files, define $env:PLINK_PATH.
$plinkExe = if ($env:PLINK_PATH) { $env:PLINK_PATH } else { "$env:ProgramFiles\PuTTY\plink.exe" }
$ipHost = "root@$((Get-Content .hetzner_ip | Select-Object -First 1).Trim())"
& $plinkExe -i "$env:USERPROFILE\.ssh\id_rsa" $ipHost
```

3. **Una vez dentro del servidor (bash)**, ejecuta (mismo criterio que [Ajustes técnicos: Docker y emergencia](#ajustes-técnicos-aplicados-docker-y-emergencia)):

```bash
cd /opt/castuo-system
docker compose -f docker-compose.prod.yml down      # V2
docker system prune -a --volumes -f                  # Limpieza forzada (-f)
git pull
docker compose -f docker-compose.prod.yml up -d     # V2 (sin --build por defecto)
```

**Nota:** si no existe el plugin V2, sustituye `docker compose` por `docker-compose`. Para reconstruir imágenes, añade **`--build`** al último comando. **`prune -f`:** solo con backups verificados; en desarrollo, valorar `prune` sin `-f`.

4. **Backups:** `ls -lah /backups` si existen; restaurar solo con procedimiento aprobado y copia validada.

---

## Errores comunes en Windows

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
Restart-Service com.docker.service
```

---

## Notas finales

- **`prune` / despliegue / reinicios** alteran continuidad y datos del stack: en **producción** cada comando debe asumir impacto en el **territorio operativo** (usuarios, integridad, copias de seguridad).
- No commitear tokens ni contraseñas.
- DOCX del flujo: **Pandoc** + `scripts\legal_template.docx`.
- Retención `/backups/`: depende del bootstrap del servidor; validar en producción.
- Mantener **versión** de esta guía alineada con el **Prontuario Maestro** cuando cambien procedimientos críticos (despliegue, legal TRL10).

---

## Referencia cruzada (versiones)

| Artefacto | Versión | Ruta |
|-----------|---------|------|
| Prontuario Maestro | 1.2.1 | `docs/PRONTUARIO_MAESTRO_ESCALADO_TRL9_TRL13.md` |
| Esta guía | 1.2.1 | `docs/legal/TRL10/README_WINDOWS.md` |
| `deploy_hetzner.ps1` | 1.2 | `scripts/deploy_hetzner.ps1` |

---

## Commit final depurado (ejemplo)

```bash
git add docs/legal/TRL10/README_WINDOWS.md
git commit -m "docs: actualiza README_WINDOWS.md con ajustes técnicos para Docker Compose V2 y emergencia
- Añade sección 'Ajustes técnicos aplicados: Docker y emergencia'.
- Unifica uso de 'docker compose' (V2) en scripts y runbook.
- Incluye advertencias para 'docker system prune -f' en producción.
- Actualiza procedimiento de emergencia con comandos válidos y notas sobre --build.
- Alinea con deploy_hetzner.ps1 (docker compose up -d sin --build por defecto).
- Añade notas sobre desarrollo vs producción para 'prune -f' y '--build'.
- Refuerza índice, seguridad, escalado, .hetzner_ip Trim y CI/CD ejecutable."
git push
```
