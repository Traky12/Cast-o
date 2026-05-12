# Directorio `secrets/` (local — no commitear ficheros de token)

**Propósito:** materializar **Opción A** en desarrollo (`CASTUO_*_FILE` apuntando aquí) sin usar Opción C en `.env` compartido.

**Reglas**

- Solo `README.md` está versionado; el resto de ficheros en esta carpeta está en `.gitignore`.
- Usar **tokens opacos largos** generados (`openssl rand -base64 64 | tr -d '\n'` en POSIX); no etiquetar el contenido como “JWT” si no lo es.
- **Producción:** preferir Docker Swarm secrets o Vault en el servidor; no `scp` de esta carpeta hacia VPS con material real.

**Ejemplo de rutas env (dev)**

```text
CASTUO_ADMIN_GENERAL_BEARER_FILE=<repo>/secrets/castuo_admin_general_bearer
CASTUO_ROBOTICS_LAB_BEARER_TOKEN_FILE=<repo>/secrets/robotics_lab_bearer
```

**Checklist:** [docs/deploy/CHECKLIST-TRL6-HETZNER-STAGING.md](../docs/deploy/CHECKLIST-TRL6-HETZNER-STAGING.md)
