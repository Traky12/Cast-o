# Prontuario maestro — deploy real (Hetzner / bare metal)

**Versión:** 1.0 · **Ámbito:** systemd + repo en `/opt/castuo-system` · **No** sustituye hardening, firewall ni TLS.

> **Oneshot:** `castuo-autonomous-agents` puede mostrar `inactive (dead)` con `RemainAfterExit=yes` — es **esperado** tras un arranque correcto del lanzador.

---

## 0. Conflictos de rutas (leer antes)

| Unidad | Ruta por defecto en git |
|--------|-------------------------|
| `castuo-iot-coop*.service` | `User=root`, `WorkingDirectory=/root/castuo-system/backend` |
| `castuo-autonomous-agents.service.example` | `User=castuo`, `/opt/castuo-system` |

Si despliegas en **`/opt/castuo-system`**, las coops **no** funcionan tal cual: usa **overrides** systemd (§4) o edita las unidades **antes** de `daemon-reload`.

---

## 1. Desde tu máquina (SSH)

```bash
ssh root@TU_IP_HETZNER
```

---

## 2. En el servidor (como `root`) — usuario y árbol

```bash
install -d -m 0755 /opt/castuo-system /etc/castuo-system /var/log/castuo /var/lib/castuo-agents

# Usuario de servicio (sin login interactivo si prefieres):
id castuo &>/dev/null || useradd -r -s /usr/sbin/nologin -d /opt/castuo-system -m castuo

# Tras copiar el repo (§3), propietario:
chown -R castuo:castuo /opt/castuo-system /var/log/castuo /var/lib/castuo-agents
chmod 750 /etc/castuo-system
```

---

## 3. Código en `/opt/castuo-system`

**Opción A — desde tu PC:**

```bash
rsync -avz --delete ./Castuo-System/ root@TU_IP_HETZNER:/opt/castuo-system/
ssh root@TU_IP_HETZNER 'chown -R castuo:castuo /opt/castuo-system'
```

**Opción B — en el servidor:** `git clone` como `castuo` en `/opt/castuo-system` (ajustar rama y secretos).

`start_agents.py` se invoca con `python3` en `ExecStart`; **`chmod +x` es opcional**.

---

## 4. Overrides para coops IoT en `/opt` (recomendado)

Evita editar a mano los `.service` del repo; mantén el upstream y añade:

```bash
for n in 1 2 3; do
  install -d "/etc/systemd/system/castuo-iot-coop${n}.service.d"
  cat > "/etc/systemd/system/castuo-iot-coop${n}.service.d/override.conf" <<EOF
[Service]
User=castuo
Group=castuo
WorkingDirectory=/opt/castuo-system/backend
Environment=BACKEND_URL=http://127.0.0.1:8001
Environment=IOT_MONITOR_LOG=/opt/castuo-system/backend/logs/iot-monitor-coop${n}.log
EOF
done
install -d -m 0755 /opt/castuo-system/backend/logs
chown castuo:castuo /opt/castuo-system/backend/logs
```

*(Si el backend escucha en otro puerto/host, cambia `BACKEND_URL`.)*

---

## 5. Instalar unidades (desde rutas **dentro del repo** ya desplegado)

```bash
REPO=/opt/castuo-system
SD="$REPO/scripts/systemd"

cp "$SD/castuo-iot-coop1.service" /etc/systemd/system/
cp "$SD/castuo-iot-coop2.service" /etc/systemd/system/
cp "$SD/castuo-iot-coop3.service" /etc/systemd/system/

cp "$SD/castuo-autonomous-agents.service.example" /etc/systemd/system/castuo-autonomous-agents.service
cp "$SD/castuo-system.target.example" /etc/systemd/system/castuo-system.target

install -m 0640 -o root -g castuo /dev/null /etc/castuo-system/agents.env 2>/dev/null || true
cp "$SD/agents.env.example" /etc/castuo-system/agents.env
chmod 640 /etc/castuo-system/agents.env
chown root:castuo /etc/castuo-system/agents.env
# Editar secretos:
# nano /etc/castuo-system/agents.env
```

**No** uses `cp scripts/systemd/*.service.example` para las coops: no llevan `.example`.

### 5b. Script único (mantenimiento centralizado)

Con el **repo ya desplegado** en `REPO_BASE` y ejecutando como **root** desde cualquier CWD:

```bash
cd /opt/castuo-system
CASTUO_BACKEND_URL=http://127.0.0.1:8000 bash scripts/deploy/bootstrap-hetzner.sh --status
```

- `--dry-run`: imprime acciones sin ejecutarlas.
- `--no-start`: solo `enable` (sin arrancar).
- `--verify-only`: solo `systemctl` + `journalctl` (no modifica `/etc` ni `agents.env`; requiere root).
- `CASTUO_FORCE_AGENTS_ENV=1`: vuelve a copiar `agents.env.example` sobre `agents.env` (cuidado en producción).

Auditoría rápida (evidencia interna; **no** sustituye informe de organismo de certificación / CB):

```bash
cd /opt/castuo-system
bash scripts/deploy/bootstrap-hetzner.sh --verify-only | tee "audit-systemd-$(date +%Y%m%d).txt"
```

(`tee` recibe **un** fichero de salida; no añadir `scripts/deploy/` como segundo argumento.)

Fuente: `scripts/deploy/bootstrap-hetzner.sh` (v1.1).

---

## 6. Python y dependencias

En el servidor, el usuario `castuo` necesita el intérprete y paquetes usados por `iot_monitor_3_coops.py` y `start_agents.py` (venv en `/opt/castuo-system/venv` recomendado). Ajusta `ExecStart` si usas venv:

`ExecStart=/opt/castuo-system/venv/bin/python3 ...`

---

## 7. Activar

```bash
systemctl daemon-reload
systemctl enable castuo-system.target
systemctl enable --now castuo-iot-coop1.service castuo-iot-coop2.service castuo-iot-coop3.service
systemctl enable --now castuo-autonomous-agents.service
```

---

## 8. Verificación (salida para auditoría interna)

```bash
systemctl status castuo-system.target
systemctl status castuo-autonomous-agents.service
systemctl status castuo-iot-coop1.service castuo-iot-coop2.service castuo-iot-coop3.service
journalctl -u castuo-autonomous-agents.service -n 80 --no-pager
ls -la /var/log/castuo/
```

---

## 9. Paquete de evidencia (opcional)

```bash
AUDIT=/tmp/castuo-audit-$(date +%Y%m%d)
mkdir -p "$AUDIT"
systemctl show castuo-autonomous-agents.service > "$AUDIT/autonomous-show.txt"
systemctl show castuo-iot-coop1.service > "$AUDIT/coop1-show.txt"
journalctl -u castuo-autonomous-agents.service --since today > "$AUDIT/autonomous-journal.log"
ls -la /var/log/castuo/ > "$AUDIT/logs-ls.txt"
tar czf "${AUDIT}.tar.gz" -C "$(dirname "$AUDIT")" "$(basename "$AUDIT")"
```

---

## 10. Monitoring / BioCoin Castúo

- Grafana en `localhost:3000` **solo** si levantas el stack en `castu-monitoring/`; el `curl` al dashboard puede fallar si no hay servicio.
- Texto **BioCoin Castúo:** `grep -r "BioCoin Castuo" /opt/castuo-system/castu-monitoring/` (reglas Prometheus).

---

## Referencias

- `scripts/systemd/README.md`
- [ARTEFACTOS-SYSTEMD-MONITORING-SPINOFFS.md](./ARTEFACTOS-SYSTEMD-MONITORING-SPINOFFS.md)
- [PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md](../legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md)
- FDE / LUKS2 (Hetzner): [hetzner/FDE-LUKS2-CASTUO-HETZNER.md](./hetzner/FDE-LUKS2-CASTUO-HETZNER.md)
