import json


def process_message(device_eui: str, payload: str, gateway_id: str) -> None:
    try:
        payload_data = json.loads(payload)
        print(f"Message from {device_eui} via {gateway_id}: {payload_data}")
        # Aquí iría la lógica para procesar el mensaje LoRaWAN
    except Exception as e:
        print(f"Error processing message from {device_eui}: {e}")
