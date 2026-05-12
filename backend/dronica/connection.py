from datetime import datetime

connection_status = {
    "drones": ["drone_001", "drone_002"],
    "gateway": "CASTUO-Gate-001",
    "status": "online",
    "last_connection": datetime.now().isoformat(),
}


def get_status() -> dict:
    return connection_status
