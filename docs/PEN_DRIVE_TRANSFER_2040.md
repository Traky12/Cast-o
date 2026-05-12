# PEN_DRIVE_TRANSFER_2040.md

Transferencia soberana de CASTUO-SYSTEM a pen drive con evidencias cifradas, checksums y trazabilidad opcional en GaiaChain 3.0.

## Limitacion importante (recuperabilidad)
`backend/scripts/encrypt_document.py` en este repo **no implementa** modo `--decrypt`.
Por ello:
- Por defecto, el script **no borra** el texto plano tras cifrar (preserva restauracion).
- Si habilitas `--remove-plaintext-after-encrypt`, la transferencia sera mas confidencial pero la restauracion automatica no existe en este repo.

## Uso: transferir
1. Conecta el pen drive y confirma que la ruta existe.
2. Ejecuta desde la raiz del repo:

```powershell
python scripts\pen_drive\transfer_to_pen.py `
  --source-dir . `
  --pen-drive-path "E:\CASTUO-SYSTEM_ORIGINAL" `
  --encrypt-sensitive `
```

Opcional (GaiaChain):
```powershell
$env:GAIA_CHAIN_API_URL="https://gaiachain.castuo-system.com"
$env:GAIA_CHAIN_API_KEY="TU_KEY"

python scripts\pen_drive\transfer_to_pen.py `
  --pen-drive-path "E:\CASTUO-SYSTEM_ORIGINAL" `
  --encrypt-sensitive `
  --gaiachain
```

## Uso: validar
```powershell
python scripts\pen_drive\validate_transfer.py --pen-drive-path "E:\CASTUO-SYSTEM_ORIGINAL"
```

Genera `validation_report.json` en la raiz del pen drive.

## Archivado y evidencias
- `transfer_manifest.json`: checksums + mapa de cifrados + resultados gemelos.
- `validation_report.json`: resultado de comparacion en el pen drive.
- `04_GAIACHAIN/*`: se rellena solo si activas `--gaiachain`.

## Globs de sensibilidad
El cifrado se aplica por defecto a:
- `docs/legal/**` y `docs/compliance/**`
- `contracts/**/*.sol`
- ficheros de credenciales (`.env*`, `*.key`, `*.pem`, `*.crt`)

Si quieres definir tu lista exacta de globs:
- prepara un JSON array (ej: `["docs/legal/**", "contracts/**/*.sol"]`)
- pasa `--sensitive-globs-file <ruta>`.

## Modo seguro (2040)
- Por defecto el script **conserva el texto plano** tras cifrar (`keep-plaintext-after-encrypt=true`).
- Para modo confidencial sin plaintext (no recomendado si necesitas restauracion automatica), usa `--remove-plaintext-after-encrypt`.

