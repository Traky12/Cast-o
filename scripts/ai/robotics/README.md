# Robotics Edge — script de laboratorio

## Integración backend

`backend/integrations/robotics/README.md`, `lab_stub_app.py`, DPIA en `docs/legal/DPIA-Robotics-2026.md`.

## Mock (sin hardware)

```powershell
$env:CASTUO_ROBOT_SERIAL_MOCK="1"
python scripts/ai/robotics/robot_controller.py --command "MOVE X 10"
```

## Serial real

```powershell
pip install -r scripts/ai/robotics/requirements_robotics.txt
$env:CASTUO_ROBOT_SERIAL_MOCK="0"
python scripts/ai/robotics/robot_controller.py --port COM5 --command "PING"
```

## Visión lab

```bash
python scripts/ai/robotics/ai_vision.py
# CNN + cámara (dependencias extra):
pip install -r scripts/ai/robotics/requirements_robotics_vision.txt
python scripts/ai/robotics/ai_vision.py --torch
# python scripts/ai/robotics/ai_vision.py --camera --torch
```

## PRONT A4

`docs/deploy/PRONT-CASTUO-ROBOTICS-v1-2026.md`
