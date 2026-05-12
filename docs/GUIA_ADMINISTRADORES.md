# Guia para Administradores - CASTUO-SYSTEM

## 1) Activacion en produccion

### Infraestructura base

```bash
ssh root@IP_SERVIDOR
apt update && apt upgrade -y
apt install -y docker.io docker-compose postgresql nginx certbot
```

### Dominio y TLS

```bash
certbot --nginx -d castuo.ctaex.es
curl -I https://castuo.ctaex.es
```

### Stack aplicacion

```bash
docker-compose up -d
docker-compose ps
```

## 2) Seguridad operativa

### WireGuard

```bash
apt install -y wireguard
wg genkey | tee privatekey | wg pubkey > publickey
wg show
```

### SSH + MFA

```bash
apt install -y libpam-google-authenticator
google-authenticator
```

### Firewall

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 51820/udp
ufw enable
ufw status
```

## 3) Backup y restauracion

```bash
bash scripts/backup_castuo.sh
```

Cron recomendado:

```bash
0 3 * * * /ruta/al/repo/scripts/backup_castuo.sh
```

Verificacion destino:

```bash
rclone ls scaleway:castuo-backups/
```

## 4) Monitorizacion

```bash
curl http://localhost:9090/rules
curl http://localhost:9090/metrics
```

Reglas THC en `prometheus/alert.rules.yml`.

## 5) Rutina diaria

| Tarea | Comando | Frecuencia |
|---|---|---|
| Verificar servicios | `docker-compose ps` | Diaria |
| Revisar logs backend | `docker-compose logs backend --tail 200` | Diaria |
| Revisar alertas | `curl http://localhost:9090/alerts` | Diaria |
| Validar backups | `rclone ls scaleway:castuo-backups/` | Semanal |
| Actualizacion SO | `apt update && apt upgrade -y` | Mensual |
