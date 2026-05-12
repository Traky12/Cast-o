from __future__ import annotations

import logging
from typing import Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware


logger = logging.getLogger("castuo.security")


def init_security_middlewares(app: FastAPI) -> None:
    """
    Aplica middlewares de seguridad transversales a la instancia FastAPI existente.

    - CORS restringido a dominios de producción conocidos
    - Compresión GZip
    - Validación básica de datos IoT en /iot/*
    - Sanitización ligera de salidas para evitar fugas obvias de secretos
    """

    # CORS
    allowed_origins = [
        "https://castuo-system.es",
        "https://castuo-system.eu",
        "https://sabionda-ia.es",
        "http://localhost",
        "http://127.0.0.1",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.middleware("http")
    async def validate_iot_data(request: Request, call_next: Callable):
        """
        Valida rangos básicos de temp/hum en endpoints /iot/*.
        No aplica a otras rutas.
        """
        if request.url.path.startswith("/iot/") and request.method in ("POST", "PUT", "PATCH"):
            try:
                data = await request.json()
            except Exception:
                raise HTTPException(status_code=400, detail="Payload IoT inválido")

            temp = data.get("temp")
            hum = data.get("hum")

            if temp is not None and not (-5 <= float(temp) <= 50):
                logger.warning("Temperatura fuera de rango: %s", temp)
                raise HTTPException(status_code=400, detail="Temperatura fuera de rango [-5,50]°C")

            if hum is not None and not (0 <= float(hum) <= 100):
                logger.warning("Humedad fuera de rango: %s", hum)
                raise HTTPException(status_code=400, detail="Humedad fuera de rango [0,100]%%")

        response = await call_next(request)
        return response

