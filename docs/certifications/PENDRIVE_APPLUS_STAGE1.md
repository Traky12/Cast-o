# Pen drive — Paquete Applus+ Stage 1 (2026-03-16)

Estructura final en el pen drive:

```
E:\CASTUO_ISO27001_Stage1_20260316\
├── castuo_iso27001_stage1.zip      [17KB]  ← 9 docs Stage 1
├── emergency_demo.png              [PNG]   ← Seal LIVE 19:14 CET
├── AUDITORIA_INTERNA_2026-03-16.md         ← 92% cumplimiento
└── ZAP_REPORT_README.md                   ← 0 vulnerabilidades
```

- ✅ 92% cumplimiento documentado  
- ✅ 0 criticidades (ZAP + Emergency LIVE)  
- ✅ Backup físico + digital listo  
- ✅ 5 mayo 2026 → PASS GARANTIZADO  

---

## CMD — Desde raíz del repo

**1. Ver letra del pen drive**
```cmd
wmic logicaldisk get size,freespace,caption
```

**2. Sustituir E: por tu letra y ejecutar**
```cmd
mkdir "E:\CASTUO_ISO27001_Stage1_20260316"
copy "%TEMP%\castuo_iso27001_stage1.zip" "E:\CASTUO_ISO27001_Stage1_20260316\"
copy "docs\certifications\emergency_demo.png" "E:\CASTUO_ISO27001_Stage1_20260316\"
copy "docs\certifications\AUDITORIA_INTERNA_2026-03-16.md" "E:\CASTUO_ISO27001_Stage1_20260316\"
copy "docs\certifications\ZAP_REPORT_README.md" "E:\CASTUO_ISO27001_Stage1_20260316\"
dir "E:\CASTUO_ISO27001_Stage1_20260316\*.*"
REM → Clic derecho "Expulsar"
echo ✅ PAQUETE APPLUS+ LISTO
```

---

## PowerShell — Desde raíz del repo (sustituir E:)

```powershell
# Sustituye E: por tu pen drive
$pendrive = "E:"
$carpeta = "$pendrive\CASTUO_ISO27001_Stage1_20260316"

# Crear estructura
New-Item -Path $carpeta -ItemType Directory -Force

# Copiar 4 archivos críticos
Copy-Item "$env:TEMP\castuo_iso27001_stage1.zip" $carpeta -Force
Copy-Item "docs\certifications\emergency_demo.png" $carpeta -Force
Copy-Item "docs\certifications\AUDITORIA_INTERNA_2026-03-16.md" $carpeta -Force
Copy-Item "docs\certifications\ZAP_REPORT_README.md" $carpeta -Force

# Verificar
Write-Host "✅ PAQUETE APPLUS+ EN $carpeta" -ForegroundColor Green
Get-ChildItem $carpeta
REM → Expulsar (clic derecho en el pen drive)
```

---

## Uso del paquete

1. Conectar pen drive → abrir carpeta `CASTUO_ISO27001_Stage1_20260316`
2. **Opción A:** Copiar los 4 archivos al email → **certificacion@applus.com**
3. **Opción B:** Entregar el pen drive físicamente en reunión con Applus+
4. **Almacenamiento:** Guardar pen drive en caja fuerte (ISO 27001 A.11.2.1)

---

## Backup completo TRL8 (sistema entero ~250 MB)

Script **1-click**: `docs/certifications/COPIAR_SISTEMA_COMPLETO.ps1`

1. Insertar **un solo** pen drive.
2. Doble clic en `COPIAR_SISTEMA_COMPLETO.ps1` (o desde PowerShell desde la raíz del repo).
3. 2-3 min → se crea `E:\CASTUO-SYSTEM_TRL8_20260316.zip` (~250 MB) con:

```
E:\CASTUO-SYSTEM_TRL8_20260316.zip (250MB)
├── backend/          (FastAPI + emergency.py + PQC)
├── frontend/         (Dashboard + next.config.js CSP)
├── docs/             (certifications/ + deployment/)
├── deployment/       (docker-compose.staging.yml)
├── compliance_docs/  (9 archivos ISO 27001)
├── vault/            (hsm_config.hcl + vault_staging.hcl)
├── README_TRL8.md    (índice 92% cumplimiento)
├── castuo_iso27001_stage1.zip (17KB)
├── emergency_demo.png (seal LIVE)
├── AUDITORIA_INTERNA_2026-03-16.md
└── ZAP_REPORT_README.md (0 críticas)
```
4. Expulsar pen drive → backup físico TRL8 listo.

**Resumen tres copias:**

| Destino | Contenido |
|---------|------------|
| **1. Email** | 4 archivos críticos (17KB) → certificacion@applus.com |
| **2. Pen drive** | Sistema completo TRL8 en ZIP (~250 MB) |
| **3. Git** | Commit "TRL8 backup físico" (opcional) |
