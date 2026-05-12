# Evidencia TRL6 (artefactos locales — no commitear salvo política interna)

**Generación:** desde la raíz del repo:

```powershell
.\scripts\windows\Export-TRL6-Evidence.ps1
```

```bash
bash scripts/posix/export_trl6_evidence.sh
```

**Contenido típico (gitignored):** `junit.xml`, `manifest.json`, `pytest-console.txt`.

**Uso legal / auditoría:** rellenar [INFORME-EVIDENCIA-TRL6-PLANTILLA.md](../../docs/legal/INFORME-EVIDENCIA-TRL6-PLANTILLA.md) y adjuntar `manifest` + `junit` al ticket DPO o expediente de despliegue. Esto **no** reemplaza firma DPO ni DPIA.

**Trazabilidad:** el manifiesto incluye `git_commit` (si hay `.git`) y marca de tiempo UTC.
