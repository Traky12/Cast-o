# CASTUO-SYSTEM™ | Monitoring (Git + BioCoin Castúo)

Prometheus + Grafana + git-exporter + Alertmanager para métricas de Git y alertas de commits sin TX hash.

## Despliegue rápido

Desde la raíz del repositorio:

```bash
chmod +x castu-monitoring/scripts/setup.sh
./castu-monitoring/scripts/setup.sh
```

O desde `castu-monitoring/`:

```bash
docker-compose up -d
```

## git-exporter

Si la imagen `prometheuscommunity/git-exporter` no existe, construir desde [d0ugal/git-exporter](https://github.com/d0ugal/git-exporter):

```bash
git clone https://github.com/d0ugal/git-exporter.git
cd git-exporter && docker build -t git-exporter:local .
```

En `docker-compose.yml` cambiar la imagen del servicio `git-exporter` a `git-exporter:local`.

El volumen del repo en git-exporter es `..:/repo` (raíz del repo cuando castu-monitoring está dentro). Si despliegas en otra ruta, edita el volumen a la ruta absoluta de tu repo.

## Accesos

| Servicio       | URL                    | Credenciales   |
|----------------|------------------------|----------------|
| Grafana        | http://localhost:3001  | admin / castuo123 |
| Prometheus     | http://localhost:9090  | —              |
| git-exporter   | http://localhost:9091/metrics | — |
| Alertmanager   | http://localhost:9093  | —              |

## Multi-repo (varias granjas)

Para monitorizar varios repos (castu-finca1, castu-finca2, ...):

```bash
docker-compose --profile multirepo up -d
```

Ajusta en `docker-compose.yml` los volúmenes de `git-exporter-finca2` a la ruta real de cada repo. En Grafana, el dashboard permite filtrar por **Granja** (variable `$finca`).

## Drones y sensores IoT

La API principal (`api:8000`) expone métricas Prometheus: `castu_drones_online`, `castu_drones_battery`, `castu_drones_missions`, `castu_sensor_temperature`, `castu_sensor_humidity`, `castu_sensor_soil_moisture`. El dashboard incluye paneles de Drones Castuo Link y Sensores IoT (filtro por granja). Las alertas (batería &lt; 20%, temperatura fuera de rango, humedad suelo crítica) están en `prometheus/rules/drones_sensors.yml`.

## Verificación

- Métricas Git: `curl -s 'http://localhost:9090/api/v1/query?query=git_commits_total'`
- Métricas Drones: `curl -s 'http://localhost:9090/api/v1/query?query=castu_drones_online'`
- Dashboard: Grafana → "CASTUO-SYSTEM™ | Git + BioCoin + Drones + Sensores"
