# -*- coding: utf-8 -*-
"""Conexión a PostgreSQL para SABIONDA Pro (cannabis, microgreens).
Cuando se usa migración a PostgreSQL, instalar: pip install psycopg2-binary
Variables de entorno: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.
"""
from __future__ import annotations

import os
from typing import Any, Optional

_psycopg2: Any = None
_RealDictCursor: Any = None

try:
    import psycopg2
    from psycopg2 import extras

    _psycopg2 = psycopg2
    _RealDictCursor = extras.RealDictCursor
except ImportError:
    pass


def get_db_connection():
    """Obtiene una conexión a PostgreSQL (RealDictCursor para filas como dict).
    Lanza RuntimeError si psycopg2 no está instalado o faltan variables de entorno.
    """
    if _psycopg2 is None:
        raise RuntimeError(
            "psycopg2 no instalado. Para usar PostgreSQL: pip install psycopg2-binary"
        )
    host = os.getenv("DB_HOST", "localhost")
    if not host or not os.getenv("DB_PASSWORD"):
        raise RuntimeError(
            "Configura DB_HOST y DB_PASSWORD (y opcionalmente DB_NAME, DB_USER, DB_PORT) para PostgreSQL"
        )
    return _psycopg2.connect(
        dbname=os.getenv("DB_NAME", "castuo_ctaex"),
        user=os.getenv("DB_USER", "castuo_admin"),
        password=os.getenv("DB_PASSWORD", ""),
        host=host,
        port=int(os.getenv("DB_PORT", "5432")),
        cursor_factory=_RealDictCursor,
    )


def is_postgres_available() -> bool:
    """Comprueba si PostgreSQL está configurado y psycopg2 disponible."""
    if _psycopg2 is None:
        return False
    return bool(os.getenv("DB_HOST") and os.getenv("DB_PASSWORD"))
