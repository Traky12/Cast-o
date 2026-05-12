# 🚀 Hetzner CAX21 - Sabionda Deployment

## Servidor
- **IP**: 89.167.5.233 (Helsinki - 20ms España)
- **Specs**: 4 ARM vCPU | 8GB RAM | 80GB NVMe | €7.25/mes
- **Ruta assets**: `/castuo-ctaex/frontend/public/assets/sabionda/`

## Deploy (PowerShell)
```powershell
# 1. Subir JPGs
scp "C:\Users\traky\Downloads\sabionda-profile.jpg" root@89.167.5.233:/root/
scp "C:\Users\traky\Downloads\sabionda-tech.jpg" root@89.167.5.233:/root/

# 2. Mover + Live (1 línea)
ssh root@89.167.5.233 "mkdir -p /castuo-ctaex/frontend/public/assets/sabionda && mv /root/sabionda-*.jpg /castuo-ctaex/frontend/public/assets/sabionda/ && cd /castuo-ctaex && docker-compose up -d frontend nginx"
```

## Verificar
```powershell
(Invoke-WebRequest -Uri "http://89.167.5.233/assets/sabionda/sabionda-profile.jpg" -Method Head).StatusCode
# → 200 = OK
```

## WinSCP (alternativa)
1. **winscp.net** → instalar (gratis)
2. Host: `89.167.5.233` | Usuario: `root` | Contraseña Hetzner
3. Local: `C:\Users\traky\Downloads` → Remoto: `/castuo-ctaex/frontend/public/assets/sabionda/`
4. Drag & Drop de `sabionda-profile.jpg` y `sabionda-tech.jpg`
5. SSH: `cd /castuo-ctaex && docker-compose up -d frontend nginx`

## Ahorro
- **Apagar** hasta 17/03: Hetzner Console → servidor → **Power → Shutdown** → 0€
- **Encender** 17/03: **Power → Power On** → esperar 1–2 min → `ssh root@89.167.5.233 "cd /castuo-ctaex && docker-compose up -d"`
