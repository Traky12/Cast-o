from __future__ import annotations


def generate_acl(sensor_id: str) -> str:
    return f"user {sensor_id}\ntopic readwrite castuo/sensors/{sensor_id}/#\n"


if __name__ == "__main__":
    print(generate_acl("sensor-demo"))
