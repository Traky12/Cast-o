import time
from datetime import datetime

missions_db = {}


def run_mission(mission_id: str, drone_id: str, waypoints: list) -> None:
    missions_db[mission_id] = {
        "drone_id": drone_id,
        "waypoints": waypoints,
        "status": "in_progress",
        "start_time": datetime.now().isoformat(),
    }
    print(f"Mission {mission_id} started for drone {drone_id}")
    # Simulación de la misión
    time.sleep(10)
    missions_db[mission_id]["status"] = "completed"
    print(f"Mission {mission_id} completed")


def get_mission_status(mission_id: str) -> str:
    mission = missions_db.get(mission_id, {})
    return mission.get("status", "not_found")
