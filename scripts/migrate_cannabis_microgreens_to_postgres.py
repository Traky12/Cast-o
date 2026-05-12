#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migra datos de cannabis y microgreens desde diccionarios en memoria a PostgreSQL.
Requisitos: esquemas cannabis y microgreens creados en PostgreSQL (ver docs/POSTGRESQL-MIGRATION-PLAN.md).
Variables de entorno: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.
Uso (desde raíz del repo):
  PYTHONPATH=. python scripts/migrate_cannabis_microgreens_to_postgres.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

# Añadir raíz del repo al path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from backend.database import get_db_connection
except Exception as e:
    print("Error: backend.database no disponible.", e)
    sys.exit(1)

try:
    import psycopg2
    from psycopg2 import extras
except ImportError:
    print("Error: pip install psycopg2-binary")
    sys.exit(1)


def _serialize_dt(dt):
    if dt is None:
        return None
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    return str(dt)


def migrate_cannabis_licenses(conn, licenses_db):
    """Inserta licencias de cannabis en cannabis.cannabis_licenses."""
    if not licenses_db:
        return 0
    with conn.cursor() as cur:
        for lid, lic in licenses_db.items():
            cur.execute(
                """
                INSERT INTO cannabis.cannabis_licenses
                (license_id, holder, valid_from, valid_until, allowed_strains, max_cultivation_area,
                 aemps_reference, status, blockchain_tx)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (license_id) DO NOTHING
                """,
                (
                    lic.license_id,
                    lic.holder,
                    _serialize_dt(getattr(lic, "valid_from", None)),
                    _serialize_dt(getattr(lic, "valid_until", None)),
                    extras.Json(lic.allowed_strains if hasattr(lic, "allowed_strains") else []),
                    getattr(lic, "max_cultivation_area", None),
                    getattr(lic, "aemps_reference", ""),
                    getattr(lic, "status", "active"),
                    getattr(lic, "blockchain_tx", None),
                ),
            )
    conn.commit()
    return len(licenses_db)


def migrate_cannabis_batches(conn, batches_db):
    """Inserta lotes de cannabis en cannabis.cannabis_batches."""
    if not batches_db:
        return 0
    n = 0
    with conn.cursor() as cur:
        for bid, batch in batches_db.items():
            strain = getattr(batch, "strain", None)
            strain_id = strain.strain_id if strain else ""
            thc = None
            if batch.lab_test_results and isinstance(batch.lab_test_results, dict):
                thc = batch.lab_test_results.get("thc")
            if thc is None and strain:
                thc = getattr(strain, "thc_percentage", None)
            blockchain_tx = getattr(batch, "blockchain_tx", None) or f"tx_{bid}_migrated"
            try:
                cur.execute(
                    """
                    INSERT INTO cannabis.cannabis_batches
                    (batch_id, strain_id, cultivation_site, planting_date, harvest_date, weight,
                     lab_test_results, thc_percentage, blockchain_tx, status, certification_status, account_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (batch_id) DO NOTHING
                    """,
                    (
                        batch.batch_id,
                        strain_id,
                        getattr(batch, "cultivation_site", ""),
                        _serialize_dt(getattr(batch, "planting_date", None)) or datetime.utcnow().isoformat(),
                        _serialize_dt(getattr(batch, "harvest_date", None)),
                        getattr(batch, "weight", None),
                        extras.Json(batch.lab_test_results) if getattr(batch, "lab_test_results", None) else None,
                        thc,
                        blockchain_tx,
                        getattr(batch, "status", "planted"),
                        getattr(batch, "certification_status", "pending"),
                        getattr(batch, "account_id", "") or "",
                    ),
                )
                n += 1
            except Exception as e:
                print(f"  Skip batch {bid}: {e}")
    conn.commit()
    return n


def migrate_microgreen_batches(conn, batches_db):
    """Inserta lotes de microgreens en microgreens.microgreen_batches."""
    if not batches_db:
        return 0
    n = 0
    with conn.cursor() as cur:
        for bid, batch in batches_db.items():
            variety = getattr(batch, "variety", None)
            variety_id = variety.variety_id if variety else ""
            try:
                cur.execute(
                    """
                    INSERT INTO microgreens.microgreen_batches
                    (batch_id, variety_id, tray_id, planting_date, harvest_date, weight,
                     environmental_data, blockchain_tx, status, certification_status, account_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (batch_id) DO NOTHING
                    """,
                    (
                        batch.batch_id,
                        variety_id,
                        getattr(batch, "tray_id", ""),
                        _serialize_dt(getattr(batch, "planting_date", None)) or datetime.utcnow().isoformat(),
                        _serialize_dt(getattr(batch, "harvest_date", None)),
                        getattr(batch, "weight", None),
                        extras.Json(batch.environmental_data or {}),
                        getattr(batch, "blockchain_tx", None),
                        getattr(batch, "status", "planted"),
                        getattr(batch, "certification_status", "pending"),
                        getattr(batch, "account_id", "") or "",
                    ),
                )
                n += 1
            except Exception as e:
                print(f"  Skip microgreen batch {bid}: {e}")
    conn.commit()
    return n


def main():
    # Cargar datos desde backend (diccionarios en memoria)
    try:
        from backend.routers import pro_accounts

        cannabis_licenses_db = getattr(pro_accounts, "cannabis_licenses_db", {})
        cannabis_batches_db = getattr(pro_accounts, "cannabis_batches_db", {})
        microgreen_batches_db = getattr(pro_accounts, "microgreen_batches_db", {})
    except Exception as e:
        print("No se pudieron cargar los diccionarios del backend (¿PYTHONPATH?).", e)
        print("Asegúrate de ejecutar desde la raíz del repo: PYTHONPATH=. python scripts/migrate_cannabis_microgreens_to_postgres.py")
        sys.exit(1)

    print("Conectando a PostgreSQL...")
    conn = get_db_connection()
    try:
        n_lic = migrate_cannabis_licenses(conn, cannabis_licenses_db)
        print(f"  Licencias cannabis: {n_lic}")
        n_batch = migrate_cannabis_batches(conn, cannabis_batches_db)
        print(f"  Lotes cannabis: {n_batch}")
        n_mg = migrate_microgreen_batches(conn, microgreen_batches_db)
        print(f"  Lotes microgreens: {n_mg}")
        print("Migración finalizada.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
