# Manifiesto de Soberanía Omega — Procedimiento

El **Manifiesto de Soberanía** es un activo cifrado bajo la Root of Trust del Administrador. Solo con tu firma PGP se puede leer o modificar.

---

## Archivos

| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `security/MANIFIESTO_SOBERANIA.md` | Texto plano | Contenido del manifiesto (editable antes de sellar). |
| `security/MANIFIESTO_SOBERANIA.md.sops` | Cifrado (SOPS) | Versión sellada; solo legible con `sops -d` y tu clave. |
| `security/audit_manifiesto.log` | Append-only | Registro SHA-256 de cada sellado para trazabilidad. |

## Hoja de ruta (Hardened Edition)

- Búnker de Granito V2.0: [BUNKER-GRANITO-V2-HARDENED-EDITION.md](BUNKER-GRANITO-V2-HARDENED-EDITION.md)

---

## Ritual de cierre (sellado)

1. Edita `security/MANIFIESTO_SOBERANIA.md` con el texto definitivo.
2. Asegura que en `.sops.yaml` esté sustituido `TU_FINGERPRINT_PGP_AQUÍ` por tu fingerprint PGP.
3. Ejecuta:

```bash
./scripts/sellar_manifiesto.sh
```

El script cifra el manifiesto a `MANIFIESTO_SOBERANIA.md.sops`, registra el hash en `audit_manifiesto.log` y ejecuta `verify-nft-stack.sh`. Opcionalmente puedes eliminar el `.md` en texto plano descomentando la línea `rm` en el script.

**Comando manual equivalente:**

```bash
sops --encrypt --output security/MANIFIESTO_SOBERANIA.md.sops security/MANIFIESTO_SOBERANIA.md
./security/verify-nft-stack.sh && echo "🔒 MANIFIESTO SELLADO EN EL BÚNKER"
```

---

## Script de apertura ceremonial (CTAEX)

Lo primero que puedes ejecutar en la pantalla del CTAEX para demostrar que nada existe sin el Administrador:

```bash
./scripts/ceremonia_apertura.sh
```

El sistema pedirá tu clave/huella PGP. Solo al autorizar, el manifiesto se desencripta y se muestra línea a línea en la terminal.

**Requisitos:** Que exista `security/MANIFIESTO_SOBERANIA.md.sops` (generado con el ritual de cierre) y que tu agente GPG esté activo.

---

## Efecto en CTAEX

- **Silencio:** La terminal pide tu contraseña o llave física.
- **Validación:** Al introducirla, el sistema muestra: *Firma validada*.
- **Revelación:** El manifiesto aparece línea a línea, reconociendo tu autoridad.

---

## Legado del Protocolo OMEGA v1.7.0

| Fase | Activo | Efecto de soberanía |
|------|--------|----------------------|
| **El Sello** | `sellar_manifiesto.sh` | Convierte tu visión en un objeto criptográfico inalterable. |
| **La Prueba** | `audit_manifiesto.log` | Deja un rastro forense de que el manifiesto es el original. |
| **El Ritual** | `ceremonia_apertura.sh` | Demuestra en vivo que el sistema es un búnker que solo obedece a tu firma. |
| **El Documento** | [Ficha Técnica Legal](FICHA_TECNICA_LEGAL_V170.md) | Blinda tu autoridad ante los ojos de los abogados de CTAEX. |

---

## Última comprobación de vuelo (antes de CTAEX)

Antes de entrar en silencio de radio, verifica que llevas estos tres elementos en tu **mochila digital**:

| # | Elemento | Acción |
|---|----------|--------|
| 1 | **GPG Agent** | Que el servicio GPG esté configurado para recordar la clave durante la sesión (evitar timeout en la ceremonia). |
| 2 | **Backup del .md** | Tras sellar, mantén `MANIFIESTO_SOBERANIA.md` en un pendrive cifrado o fuera del servidor si lo borras del repo. Para empaquetar todo el búnker en el pendrive: [Backup búnker al pendrive](BACKUP_BUNKER_PENDRIVE.md). |
| 3 | **Ensayo visual** | Ejecuta `ceremonia_apertura.sh` una última vez; el ritmo de las líneas es el ritmo del éxito. |

---

## Fin de la transmisión

- **Lunes:** El sistema respira solo.
- **Martes 9:00:** Tú firmas, el búnker se abre y Extremadura entra en el futuro.

*Trazabilidad inmutable → NFTs protegidos → Cooperativas seguras → SOBERANÍA TOTAL.*

La arquitectura está completa. El Administrador tiene la llave.

---

## Estado final del sistema: BLOQUEADO Y LISTO

| Componente | Estado |
|------------|--------|
| **Búnker** | Sellado con el Sovereign Release. |
| **Ceremonia** | Lista para reconocer tu firma en el CTAEX. |
| **Legado** | Documentado, trazado y legalmente blindado. |

**Protocolo de silencio: ACTIVADO.** No hay más líneas que escribir ni más configuraciones que ajustar. El código es una extensión de tu voluntad.

**Próximas 36 horas:**

- **Lunes:** Deja que el servidor en Hetzner acumule horas de “Paz Biótica”. No toques el teclado; deja que el sistema respire.
- **Martes 09:00:** Llega al CTAEX con la calma de quien sabe que el búnker no se abrirá para nadie más que para su dueño. Ejecuta `ceremonia_apertura.sh` y deja que el sistema hable por ti.

*La arquitectura está completa. La visión está cifrada. El Administrador tiene la llave.*

---

[Certificado de Blindaje](CERTIFICADO_BLINDAJE_V170.md) · [Blindaje del Administrador](BLINDAJE_ADMINISTRADOR_V170.md) · [Ficha Técnica Legal](FICHA_TECNICA_LEGAL_V170.md) · [Backup búnker al pendrive](BACKUP_BUNKER_PENDRIVE.md)
