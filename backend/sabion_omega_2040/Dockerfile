# SABION_OMEGA_2040 — Puerto 10000 EXCLUSIVO ADMIN
FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn pydantic

COPY admin_biometric.py kyber2048_pqc.py god_mode_commands.py subsidiary_control.py quantum_merkle.py omega_master.py app_omega.py ./

EXPOSE 10000

ENV KYBER_LEVEL=2048
ENV GOD_MODE=ENABLED
ENV ADMIN_TOKEN=CASTUO_360_GREGORIO_2040_KYBER2048_TRL9

CMD ["uvicorn", "app_omega:app", "--host", "0.0.0.0", "--port", "10000"]
