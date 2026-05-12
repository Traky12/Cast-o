# Guía de Despliegue del Dashboard de Verificación (Junta de Extremadura)

Dashboard para verificación de propiedades ForestOwnershipToken, cálculo de subvenciones y consulta de certificaciones.

**Versión:** 1.2

---

## 1. Requisitos técnicos

| Componente | Especificación |
|------------|----------------|
| Servidor | 2 CPU, 8 GB RAM, 100 GB SSD (mínimo) |
| Sistema operativo | Ubuntu 22.04 LTS |
| Docker | 20.10+ |
| Nginx | 1.18+ (incluido en imagen) |
| Acceso | HTTPS con certificado (Let's Encrypt recomendado) |

---

## 2. Variables de entorno (build time)

El frontend React necesita la dirección del contrato en tiempo de compilación:

- **REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS:** Dirección del contrato ForestOwnershipToken desplegado en GaiaChain.

Copiar y editar:

```bash
cd frontend/extremadura-dashboard
cp .env.example .env
# Editar .env y asignar:
# REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS=0x...
```

---

## 3. Construcción de la imagen Docker

```bash
cd frontend/extremadura-dashboard
docker build -t extremadura-dashboard:latest \
  --build-arg REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS=0xTU_DIRECCION .
```

O usando el `.env`:

```bash
export $(grep -v '^#' .env | xargs)
docker build -t extremadura-dashboard:latest \
  --build-arg REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS=$REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS .
```

---

## 4. Despliegue con Docker Compose

```bash
docker-compose up -d
```

El servicio queda expuesto en el puerto 80. Para producción, colocar un proxy inverso (Nginx o Caddy) delante con SSL (Let's Encrypt) y servir el puerto 80/443.

---

## 5. Comprobación

- Abrir en navegador: `http://<IP_SERVIDOR>` (o `https://` si hay SSL).
- Conectar wallet (MetaMask) a la red GaiaChain.
- Introducir un Token ID existente y pulsar «Cargar datos»: deben mostrarse parcela, área, certificaciones y subvenciones calculadas.

---

## 6. Reinicio y logs

```bash
docker-compose restart
docker-compose logs -f dashboard
```

---

*Para requisitos detallados de red (GaiaChain RPC, firewall), ver documentación de infraestructura CASTÚO-SYSTEM™ y [PLAN_FORMACION_TECNICOS.md](../junta-extremadura/PLAN_FORMACION_TECNICOS.md) §7.*
