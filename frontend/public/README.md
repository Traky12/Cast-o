# CASTUO-SYSTEM — Frontend público

Páginas HTML con menú lateral (Tailwind + Font Awesome). Servir con un servidor HTTP para probar en local o desplegar en Hetzner.

## 1. Estructura de archivos

```
frontend/
└── public/
    ├── index.html
    ├── grid-iot.html
    ├── catalogo.html
    ├── control-rpi.html
    ├── cuaderno.html
    ├── qr-trazabilidad.html
    ├── 3d-virtual.html
    ├── escalado.html
    ├── marketplace.html
    ├── metricas.html
    ├── sabionda-ia.html
    ├── ayuda.html
    ├── mi-cuenta.html
    ├── assets/
    │   └── sabionda/   (opcional: sabionda-profile.jpg, sabionda-tech.jpg)
    └── README.md
```

## 2. Ver en local

En una terminal (en la raíz del repo):

```bash
cd frontend/public/
npx serve -p 3000
```

Luego abre: **http://localhost:3000/**

## 3. Subir a Hetzner

Desde la raíz del proyecto (PowerShell o Git Bash):

```bash
scp -r frontend/public/ root@89.167.5.233:/frontend/
```

En el servidor:

```bash
ssh root@89.167.5.233
cd /frontend
docker-compose -f docker-compose.hetzner.yml up -d nginx
```

(Si usas otro compose, sustituye por el que tengas, por ejemplo `docker-compose up -d nginx`.)

## 4. Acceder desde el navegador

- **Local:** http://localhost:3000/
- **Hetzner:** http://89.167.5.233/

---

## Resumen de comandos

| Acción            | Comando |
|-------------------|--------|
| Ver en local      | `cd frontend/public/` y `npx serve -p 3000` |
| Abrir local       | http://localhost:3000/ |
| Subir a Hetzner   | `scp -r frontend/public/ root@89.167.5.233:/frontend/` |
| Reiniciar Nginx   | `ssh root@89.167.5.233` → `cd /frontend` → `docker-compose -f docker-compose.hetzner.yml up -d nginx` |
| Abrir producción  | http://89.167.5.233/ |
