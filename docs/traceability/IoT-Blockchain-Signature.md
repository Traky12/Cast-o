# Firma de Datos IoT con Blockchain — Barreras v6.1

**Objetivo**: Cada dato IoT firmado por el sensor (clave pública registrada en GaiaChain); hash del dato anterior para cadena de custodia; validación por 3 nodos antes de procesar.

---

## Flujo

1. **Registro**: Clave pública del sensor registrada en GaiaChain (una vez por sensor).
2. **Envío**: Sensor firma `{ sensor_id, timestamp, temp, hum, ... prev_hash }` con su clave privada; envía payload + firma.
3. **Verificación**: Backend verifica firma con clave pública en GaiaChain; comprueba que `prev_hash` coincida con último hash conocido para ese `sensor_id`.
4. **Validación**: 3 nodos GaiaChain (o lógica equivalente) confirman antes de aceptar el dato para trazabilidad.

---

## Ejemplo de validación (backend)

```python
def validate_iot_data(data):
    if not gaia_chain.verify_signature(data["signature"], data["sensor_public_key"]):
        return {"status": "error", "reason": "Firma inválida"}
    if data["prev_hash"] != gaia_chain.get_last_hash(data["sensor_id"]):
        return {"status": "error", "reason": "Cadena de custodia rota"}
    return {"status": "valid"}
```

---

## Referencias

- [Sabionda-Barriers-v6.1.md](../security/Sabionda-Barriers-v6.1.md) § 9.2
