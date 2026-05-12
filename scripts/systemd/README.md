# Unidades systemd (plantillas en repo)

**Estado `ACTIVE (running)`:** solo lo puede confirmar `systemctl status` **en el servidor** donde estén instaladas. El git **no** demuestra que un servicio esté en marcha.

## Unidades presentes en este directorio

| Archivo | Propósito |
|---------|-----------|
| `castuo-iot-coop1.service` | Monitor IoT coop 1 (`iot_monitor_3_coops.py --coop 1`) |
| `castuo-iot-coop2.service` | Idem coop 2 |
| `castuo-iot-coop3.service` | Idem coop 3 |
| `*-watchdog-ctaex.service` | Vigilancia docker / postgres / mqtt / nginx / disco (CTAEX) |
| `castuo-autonomous-agents.service.example` | Orquestador agentes (`start_agents.py all --background`); ver nota **Type=oneshot** abajo |
| `castuo-system.target.example` | Target opcional para `PartOf=` del servicio anterior |
| `agents.env.example` | Plantilla para `/etc/castuo-system/agents.env` (secretos fuera de git) |

Rutas en las unidades (`WorkingDirectory`, `User`) son **ejemplo típico** (`/opt/castuo-system`); ajustar antes de `systemctl enable`.

### `castuo-autonomous-agents.service.example`

- **ExecStart** usa `python3 …/start_agents.py all --background`: el script principal termina tras lanzar los agentes → **`Type=oneshot`** + **`RemainAfterExit=yes`** (no `Type=simple`).
- Crea usuario sistema `castuo` y directorios; logs por defecto en `/var/log/castuo` (ver `ReadWritePaths`).
- Si **no** usas `castuo-system.target`, comenta `PartOf=` en la unidad o instala la plantilla `castuo-system.target.example`.
- Ajusta la URL `Documentation=` si el remoto Git no coincide con tu organización.

## Lo que **no** está versionado como unidad final

- `castuo-autonomous-agents.service` (sin `.example`) — se genera en el servidor copiando la plantilla.

## Instalación (referencia)

```bash
sudo cp scripts/systemd/castuo-iot-coop1.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now castuo-iot-coop1.service
```

### Autonomous agents (plantilla)

**No** instales con `cp scripts/systemd/*.service.example`: las coops IoT son `castuo-iot-coop*.service` (sin `.example`); solo el orquestador usa la plantilla renombrada a `.service`.

```bash
sudo mkdir -p /etc/castuo-system
sudo cp scripts/systemd/agents.env.example /etc/castuo-system/agents.env
sudo chmod 640 /etc/castuo-system/agents.env
sudo chown root:castuo /etc/castuo-system/agents.env
sudo cp scripts/systemd/castuo-system.target.example /etc/systemd/system/castuo-system.target
sudo cp scripts/systemd/castuo-autonomous-agents.service.example /etc/systemd/system/castuo-autonomous-agents.service
sudo systemctl daemon-reload
sudo systemctl enable --now castuo-system.target
sudo systemctl enable --now castuo-autonomous-agents.service
```

**Deploy completo (Hetzner, `/opt/castuo-system`, overrides IoT):** [docs/ops/PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md](../../docs/ops/PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md) · `bash scripts/deploy/bootstrap-hetzner.sh --status` (instala + status) · `bash scripts/deploy/bootstrap-hetzner.sh --verify-only` (solo comprobación, sin tocar ficheros).
