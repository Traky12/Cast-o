# Guía de operación — control hidropónico remoto (CTAEX)

**Versión:** 1.0  
**Fecha:** 2026-03-25  
**Ámbito:** API `hydro_remote` + dashboard `frontend/ctaex-hydro-dashboard`.

## 1. Introducción

El backend expone zonas de laboratorio (`zone_cannabis_1`, `zone_microgreens_1`) con sensores simulados, actuadores lógicos y parada de emergencia. Los actuadores físicos deben suscribirse a MQTT con los scripts en `scripts/iot/` (GPIO real o modo simulación sin RPi).

## 2. Dashboard

- Ruta UI: `/hidroponic/{zone_id}` en la app Vite.
- Requiere JWT (Keycloak) o backend con `AUTH_DISABLED=true` en entornos cerrados.

## 3. Actuadores

| Actuador | ID API | Notas |
|----------|--------|--------|
| Válvula agua | `valvula_agua` | Limitar duración; riesgo de inundación. |
| Válvula nutrientes | `valvula_nutrientes` | Coordinar con riego. |
| Ventilador | `ventilador` | No mantener apagado si hay calor acumulado. |
| Luz LED | `luz_led` | Intensidad vía MQTT en edge (`led_controller.py`). |

Duración máxima por comando: configurable con `HYDRO_ACTUATOR_MAX_DURATION_S` (por defecto 3600 s).

## 4. Parada de emergencia

`POST /api/zones/{zone_id}/actuators/emergency_stop` pone todos los actuadores de la zona en OFF y cancela temporizadores en memoria del backend. **No** garantiza parada física si el edge no recibe MQTT: diseñar fail-safe en campo.

## 5. Parámetros ideales

Solo se pueden actualizar claves ya definidas en la zona (`temperatura_c`, `humedad_pct`, `ph`, `ec_ms`, …).  
`POST /api/zones/{zone_id}/parameters` con `{ "parameter": "...", "value": n }`.

## 6. Monitorización

- Telemetría MQTT: ver `docs/user/MQTT_GUIDE.md`.
- Métricas agregadas: Prometheus/Grafana según despliegue.

## 7. Soporte

Los contactos concretos (correo, teléfono, canal interno) los define el responsable del despliegue en CTAEX; no versionar datos personales en el repositorio.
