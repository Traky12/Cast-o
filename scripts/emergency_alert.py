#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SABIONDA v7.1 | Alertas de emergencia (Barreras v7.1). Temp >30°C → SMS, pausar farm, log GaiaChain.
Uso: python scripts/emergency_alert.py [farm_id]
"""
import os
import sys

def get_sensor_data(farm_id: str, metric: str):
    """Obtiene dato de sensor (API interna o mock)."""
    api_url = os.getenv("CASTUO_API_URL", "http://localhost:8000")
    try:
        import httpx
        r = httpx.get(f"{api_url.rstrip('/')}/iot/ingest", params={"farm_id": farm_id})
        if r.status_code == 200 and r.json():
            return r.json().get(metric, 0)
    except Exception:
        pass
    return 0

def send_sms(farm_id: str, message: str) -> None:
    """Envía SMS (Twilio). Configurar TWILIO_* en producción."""
    if os.getenv("TWILIO_ACCOUNT_SID"):
        try:
            from twilio.rest import Client
            client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
            client.messages.create(
                body=message,
                from_=os.getenv("TWILIO_FROM"),
                to=os.getenv("EMERGENCY_PHONE"),
            )
        except Exception as e:
            print(f"SMS send failed: {e}")
    else:
        print(f"[SMS stub] {farm_id}: {message}")

def pause_farm(farm_id: str) -> None:
    """Pausa farm (API o dispositivo)."""
    api_url = os.getenv("CASTUO_API_URL", "http://localhost:8000")
    try:
        import httpx
        httpx.post(f"{api_url.rstrip('/')}/iot/pause", json={"farm_id": farm_id}, timeout=5.0)
    except Exception:
        print(f"[Pause stub] farm {farm_id}")

def log_to_gaiachain(farm_id: str, action: str, payload: dict) -> None:
    """Registra incidencia en GaiaChain (auditoría)."""
    api_url = os.getenv("CASTUO_API_URL", "http://localhost:8000")
    try:
        import httpx
        httpx.post(
            f"{api_url.rstrip('/')}/blockchain/register_batch",
            json={
                "batch_id": f"emergency-{farm_id}",
                "strain_id": action,
                "thc_percentage": 0,
                "cbd_percentage": 0,
                "weight_kg": 0,
                "lab_results": payload,
                "account_id": "emergency",
            },
            timeout=10.0,
        )
    except Exception as e:
        print(f"GaiaChain log failed: {e}")

def check_emergency(farm_id: str) -> None:
    temp = get_sensor_data(farm_id, "temp")
    if temp > 30:
        send_sms(farm_id, f"🚨 Temp {temp}°C > 30°C — Farm {farm_id}")
        pause_farm(farm_id)
        log_to_gaiachain(farm_id, "emergency_stop", {"temp": temp})

def main():
    farm_id = (sys.argv[1:] or ["1"])[0]
    check_emergency(farm_id)

if __name__ == "__main__":
    main()
