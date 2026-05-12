# CASTUO-SYSTEM — Frontend público

Páginas HTML con menú lateral (Tailwind + Font Awesome). Servir con un servidor HTTP para probar en local o desplegar en Hetzner.

## 1. Estructura de archivos

En `castuo-ctaex/frontend/public/` deben estar:

- `index.html` — Inicio (dashboard)
- `grid-iot.html`
- `catalogo.html`
- `control-rpi.html`
- `cuaderno.html`
- `qr-trazabilidad.html`
- `3d-virtual.html`
- `escalado.html`
- `marketplace.html`
- `metricas.html`
- `sabionda-ia.html`
- `ayuda.html`
- `mi-cuenta.html`

(Opcional: `CASTUO-SYSTEM-v4.6-CTAEX.html`, `assets/sabionda/*.jpg`)

## 2. Ver en local (servidor estático)

Desde la raíz del proyecto:

```bash
cd castuo-ctaex/frontend/public/
npx serve -p 3000
```

O con `serve` instalado globalmente:

```bash
npm install -g serve
cd castuo-ctaex/frontend/public/
serve -p 3000
```

Abrir en el navegador: **http://localhost:3000/**

Se cargará `index.html`; el menú lateral enlaza al resto de páginas.

## 3. Comprobar enlaces

Revisar que desde Inicio se puede ir a Grid IoT, Catálogo, Control RPi, Cuaderno, QR Trazabilidad, 3D Virtual, Escalado, Marketplace, Métricas, SABIONDA IA, Ayuda y Mi cuenta, y que en cada página el menú lateral funciona.

## 4. Subir al servidor Hetzner

Subir toda la carpeta `public` al servidor:

```bash
scp -r castuo-ctaex/frontend/public/ root@89.167.5.233:/castuo-ctaex/frontend/
```

(En PowerShell, misma orden; te pedirá la contraseña de `root`.)

## 5. Nginx en Hetzner

Conectar por SSH y levantar/reiniciar los servicios (según tu compose):

```bash
ssh root@89.167.5.233
cd /castuo-ctaex
docker-compose -f docker-compose.hetzner.yml up -d nginx
```

(O el archivo compose que uses: por ejemplo `docker-compose up -d frontend nginx`.)

Asegúrate de que Nginx sirve los estáticos desde `/castuo-ctaex/frontend/public/` (o la ruta equivalente dentro del contenedor).

## 6. Abrir en el navegador

- Local: **http://localhost:3000/**
- Hetzner: **http://89.167.5.233/** (o el dominio que apunte a esa IP)

---

## Resumen de comandos

| Acción              | Comando |
|---------------------|--------|
| Servidor local      | `cd castuo-ctaex/frontend/public/` y `npx serve -p 3000` |
| Abrir local         | http://localhost:3000/ |
| Subir a Hetzner     | `scp -r castuo-ctaex/frontend/public/ root@89.167.5.233:/castuo-ctaex/frontend/` |
| Reiniciar Nginx     | `ssh root@89.167.5.233` → `cd /castuo-ctaex` → `docker-compose -f docker-compose.hetzner.yml up -d nginx` |
| Abrir en producción | http://89.167.5.233/ |

Más detalles de despliegue y assets Sabionda: `castuo-ctaex/docs/servidor-hetzner.md`.
