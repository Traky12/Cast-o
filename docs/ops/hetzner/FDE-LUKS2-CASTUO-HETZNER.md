# Cifrado de disco completo (FDE) — Hetzner + CASTÚO-SYSTEM

**Objetivo:** LUKS2 en raíz con **AES-XTS** (modo práctico habitual: `aes-xts-plain64`, clave efectiva 256 bit por especificación XTS), alineado con buenas prácticas NIST SP 800-38E / FIPS en despliegues que lo requieran.  
**Alcance:** infraestructura del VPS; **no** sustituye DPIA ni contrato DPA con Hetzner.

> **Aviso:** `sgdisk -Z`, `cryptsetup luksFormat` y reparticionado **borran datos**. Snapshot / backup **antes**. Contrastar siempre con la [documentación actual de Hetzner](https://docs.hetzner.com/) y el rescue de tu producto (AX/EX/CX).

---

## 1. Rescue Mode (Hetzner)

1. Cloud Console → servidor → **Rescue** → sistema Linux 64 bit.  
2. Activar **SSH key** conocida.  
3. **Reset** al rescue.  
4. Conexión típica: `ssh root@IP -p 2222` (puerto habitual del rescue; ver panel).

---

## 2. Vía A — Manual (control máximo, alto riesgo operativo)

Ejemplo conceptual en disco **`/dev/sda`** (sustituir por `nvme0n1` si aplica).

```bash
# DESTRUCTIVO — solo en VPS vacío o con backup verificado
sgdisk -Z /dev/sda
sgdisk -n 1:0:+512M -t 1:ef02 /dev/sda   # BIOS boot (o usar EFI ef00 según firmware)
# … definir EFI + /boot + partición LUKS según firmware UEFI vs BIOS …
```

En **UEFI** suele usarse partición EFI (`ef00`), `/boot` sin cifrar y partición para LUKS.

```bash
cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 --key-size 512 \
  --pbkdf argon2id --iter-time 5000 \
  /dev/sdaN

cryptsetup luksOpen /dev/sdaN castuo_root
mkfs.ext4 /dev/mapper/castuo_root
# montar y debootstrap / instalar — procedimiento largo; muchos equipos prefieren Vía B.
```

**Nota:** El layout exacto (EFI vs BIOS, tamaños) depende del **AX/EX** y de si reutilizas **installimage** de Hetzner.

---

## 3. Vía B — `installimage` (Hetzner)

Script oficial del proveedor para instalar Debian/Ubuntu con particiones definidas. Los ficheros de configuración **cambian** con el tiempo; no copies ciegamente un `config.yml` genérico.

1. En rescue, seguir la guía Hetzner para descargar y ejecutar `installimage`.  
2. Activar cifrado LUKS en el asistente o plantilla que distribuya el proveedor para **FDE**.  
3. Tras instalación, el primer arranque puede pedir frase de descifrado en consola (KVM / LARA) o flujo **NBDE** (Clevis+Tang) si lo configuras **después** en el sistema instalado.

---

## 4. Desbloqueo remoto (Clevis + Tang) — post-instalación Ubuntu

**Ubuntu 24.04** usa normalmente **initramfs** con `update-initramfs`, no `dracut` (típico de RHEL/Fedora).

Paquetes orientativos:

```bash
apt update
apt install -y clevis clevis-luks clevis-initramfs tang
```

1. Desplegar **Tang** en un VPS de confianza (TLS obligatorio en producción; el ejemplo `http://` es solo laboratorio).  
2. Asociar ranura LUKS:

```bash
clevis luks bind -d /dev/sdaN tang '{"url":"https://tang.ejemplo.invalid"}'
update-initramfs -u -k all
```

**Riesgo:** dependencia de red y del servidor Tang; modelo de amenazas y revocación deben estar documentados (no “zero-trust” solo por añadir Tang).

---

## 5. Rescue: `cryptroot-unlock` (cuando el initramfs lo expone)

En algunos instaladores derivados de Debian existe utilidad para abrir LUKS desde rescue vía SSH; el nombre exacto depende de la imagen. Si no está disponible, desbloqueo manual con `cryptsetup luksOpen` desde rescue.

---

## 6. Contenedor offline (VeraCrypt / hardware)

Copia **offline** de secretos o snapshot cifrado en soporte físico:

- Generar contenedor VeraCrypt en estación de trabajo endurecida.  
- **No** almacenar solo copia en el mismo cloud sin segunda ubicación.

---

## 7. Capa aplicación CASTÚO (repo)

| Elemento | Ruta / nota |
|----------|----------------|
| Cripto PQC / simétrica (código) | `backend/security/pq_crypto.py` |
| Despliegue “zero-leak” (compose) | `docker-compose.hetzner.zero-leak.yml` (raíz del repo) |
| Arquitectura estación de trabajo | [ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md](../../ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md) |

**Restic / backups cifrados:** no hay playbooks `restic` versionados en este monorepo a fecha de redacción; si los usas, documenta bucket, retención y prueba de restauración **fuera** de este fichero.

---

## 8. Verificación (en sistema ya arrancado)

```bash
sudo cryptsetup status /dev/mapper/nombre_mapper
lsblk -f
sudo blkid | grep crypto_LUKS
```

---

## 9. Costes y RTO/RPO

Las cifras (VPS Tang, pendrive, “15 min RTO”) son **orientativas** y dependen de contrato, snapshots y procedimiento real de restore. No constituyen SLA.

---

## 10. Relación con CASTÚO en `/opt/castuo-system`

FDE protege **disco en reposo** en Hetzner. Sigue siendo necesario: TLS, secretos en `agents.env`, hardening SSH, firewall y política de backups (ver [PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md](../PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md)).

---

*Documento operativo; validar cada comando en entorno de prueba antes de producción.*
