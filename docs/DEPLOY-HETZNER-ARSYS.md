# Despliegue CASTUO en Hetzner o ARSYS (Sabionda + Nginx)

Guía rápida para subir el proyecto a un VPS (Hetzner o ARSYS) con Docker, incluyendo las imágenes Sabionda.

---

## Opción A: Hetzner (nuevo servidor, ~5 min)

### 1. Conectar

```bash
ssh root@tu-ip-hetzner
```

### 2. Instalar Docker (1 línea)

```bash
curl -fsSL https://get.docker.com | sh && \
systemctl enable --now docker docker-compose
```

### 3. Copiar proyecto

Desde tu máquina (Cursor/Git Bash), con el repo clonado:

```bash
scp -r . root@tu-ip-hetzner:/root/castuo-ctaex/
```

O si tu carpeta local se llama `Castuo-System`:

```bash
scp -r . root@tu-ip-hetzner:/root/castuo-ctaex/
```

En el servidor:

```bash
ssh root@tu-ip-hetzner
cd /root/castuo-ctaex
```

### 4. Imágenes Sabionda (crítico)

En el servidor, crear la carpeta y luego copiar las imágenes desde local:

```bash
# En el servidor
mkdir -p frontend/public/assets/sabionda/
```

Desde tu PC (sustituye `user`/`tu-ip-hetzner` y la ruta del proyecto si es distinta):

```bash
scp ~/Descargas/sabionda-profile.jpg ~/Descargas/sabionda-tech.jpg root@tu-ip-hetzner:/root/castuo-ctaex/frontend/public/assets/sabionda/
```

Nombres exactos: **sabionda-profile.jpg** y **sabionda-tech.jpg**.

### 5. Build y arranque

En el servidor:

```bash
cd /root/castuo-ctaex
docker-compose -f docker-compose.hetzner.yml up -d --build
```

### 6. DNS (Cloudflare / Namecheap)

- Dominio: **castuo-system.es**
- Registro **A** → IP del servidor Hetzner

---

## Opción B: ARSYS (ya tienes el servidor, ~2 min)

### 1. Conectar

```bash
ssh user@castuo-system.arsys.es
```

### 2. Copiar solo las imágenes Sabionda

Desde tu PC:

```bash
scp ~/Descargas/sabionda-profile.jpg ~/Descargas/sabionda-tech.jpg user@castuo-system.arsys.es:/castuo-ctaex/frontend/public/assets/sabionda/
```

Nombres: **sabionda-profile.jpg** y **sabionda-tech.jpg**.

### 3. Reiniciar servicios

En ARSYS:

```bash
cd /castuo-ctaex
docker-compose -f docker-compose.hetzner.yml restart nginx
```

Así Nginx recarga y sirve las nuevas imágenes desde `frontend/public/assets/sabionda/`. Si usas otro compose con un servicio `frontend`, inclúyelo: `docker-compose restart frontend nginx`.

---

## Estructura que debe tener el servidor

```
castuo-ctaex/                    ← Raíz del proyecto
├── docker-compose.hetzner.yml   ✅
├── frontend/
│   ├── public/
│   │   └── assets/
│   │       └── sabionda/       ← Tú copias aquí las imágenes
│   │           ├── sabionda-profile.jpg
│   │           └── sabionda-tech.jpg
│   └── src/
│       └── components/
│           └── Sabionda.jsx    ✅
└── .env                         ✅ (crear/configurar en servidor)
```

---

## Comprobación en vivo (~30 s)

Tras el deploy (Hetzner o ARSYS):

```bash
# Que la página enlace a Sabionda
curl -s https://castuo-system.es/ | grep sabionda

# Que la imagen responda 200
curl -I https://castuo-system.es/assets/sabionda/sabionda-profile.jpg
# → HTTP/1.1 200 OK
```

Si tienes una ruta `/courses` que use Sabionda:

```bash
curl -s https://castuo-system.es/courses | grep sabionda
# → <img src="/assets/sabionda/sabionda-profile.jpg" ...
```

---

## Resumen rápido

| Acción | Hetzner | ARSYS |
|--------|---------|--------|
| Conectar | `ssh root@tu-ip-hetzner` | `ssh user@castuo-system.arsys.es` |
| Copiar imágenes | `scp sabionda*.jpg root@ip:/root/castuo-ctaex/frontend/public/assets/sabionda/` | `scp sabionda*.jpg user@arsys:/castuo-ctaex/frontend/public/assets/sabionda/` |
| Arrancar | `docker-compose -f docker-compose.hetzner.yml up -d --build` | `cd /castuo-ctaex && docker-compose -f docker-compose.hetzner.yml restart nginx` |

Recomendación: **ARSYS** si ya tienes todo montado (2 min). **Hetzner** si quieres un VPS nuevo y más barato (5 min).
