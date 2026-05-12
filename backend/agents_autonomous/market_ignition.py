# -*- coding: utf-8 -*-
"""
Ignición comercial diaria: rutina de apertura de mercado.
Consolida recurrencias (SaaS), auditoría fiscal (AEAT) y publicación de datos
para que el búnker "despierte" y procese todo lo pendiente sin intervención.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_LOTE_IGNITION = os.getenv("LOTE_MARKET_IGNITION", "CAN-2026-003")
_TIPO_PRODUCTO_IGNITION = os.getenv("TIPO_PRODUCTO_IGNITION", "cannabinoid_data")


def _print_protocol(msg: str) -> None:
    """Salida estándar para el protocolo de ignición (consola del búnker)."""
    print(msg)


def ignicion_comercial_diaria() -> Dict[str, Any]:
    """
    Ejecuta el ciclo comercial autónomo: recurrencias, declaraciones,
    publicación de excedentes de datos y reporte de estado.
    Protocolo de Ignición Comercial: el búnker como Nodo de Liquidación.
    """
    hoy = datetime.now(timezone.utc)
    _print_protocol("")
    _print_protocol("[IGNICION] Iniciando ciclo comercial autonomo...")
    _print_protocol("")
    results: Dict[str, Any] = {"recurring": None, "declarations": None, "data_publish": None, "dashboard": None}
    billing = None
    errores = []

    # 1. Sincronización de reloj + barrido de suscripciones
    try:
        from .automatic_billing import AutomaticBilling
        billing = AutomaticBilling()
        results["recurring"] = billing.process_recurring_billing()
        processed = results["recurring"].get("processed", 0)
        renewed = results["recurring"].get("renewed", 0)
        errors_r = results["recurring"].get("errors", 0)
        _print_protocol(f"  [RECURRING] Procesando renovaciones... {renewed} suscripciones actualizadas.")
        results["payments"] = billing.process_pending_payments()
        confirmed = results["payments"].get("confirmed", 0)
        processed_p = results["payments"].get("processed", 0)
        _print_protocol(f"  [PAYMENTS] Conciliando pagos... {processed_p} procesados, {confirmed} validados en GaiaChain.")
    except Exception as e:
        logger.warning("Fase recurrencias/pagos: %s", e)
        results["recurring_error"] = str(e)
        errores.append(f"recurrencias: {e}")
        _print_protocol(f"[RECURRING] Advertencia: {e}")

    # 2. Fiscalidad instantánea (AEAT 303 / 390)
    try:
        if billing is None:
            from .automatic_billing import AutomaticBilling
            billing = AutomaticBilling()
        results["declarations"] = billing.generate_automatic_declarations()
        m303 = results["declarations"].get("model_303", {})
        xml_path = m303.get("xml_path", "aeat/303_...")
        _print_protocol(f"  [AEAT] Borrador Modelo 303 generado en '{xml_path}'.")
        if results["declarations"].get("model_390", {}).get("generated"):
            _print_protocol("  [AEAT] Resumen anual (390) generado.")
    except Exception as e:
        logger.warning("Fase declaraciones AEAT: %s", e)
        results["declarations_error"] = str(e)
        errores.append(f"AEAT: {e}")
        _print_protocol(f"[AEAT] Advertencia: {e}")

    # 3. Inyección de mercado: lote etiquetado y colgado en DataMarketplace con sello eIDAS
    try:
        from .data_marketplace import DataMarketplace
        marketplace = DataMarketplace()
        out = marketplace.publish_data_product(_LOTE_IGNITION, _TIPO_PRODUCTO_IGNITION)
        results["data_publish"] = out
        if out.get("status") == "success":
            product_id = out.get("product", {}).get("product_id", f"DATA-{_LOTE_IGNITION}-{_TIPO_PRODUCTO_IGNITION.upper()}")
            _print_protocol(f"  [MARKET] Producto {product_id} publicado.")
        else:
            _print_protocol(f"[MARKET] Publicacion: {out.get('reason', out)}")
    except Exception as e:
        logger.warning("Fase publicacion datos: %s", e)
        results["data_publish_error"] = str(e)
        errores.append(f"market: {e}")
        _print_protocol(f"[MARKET] Advertencia: {e}")

    # 4. Reporte de estado (dashboard últimas 24h)
    try:
        from .revenue_dashboard import RevenueDashboard
        dashboard = RevenueDashboard()
        stats = dashboard.get_realtime_revenue()
        results["dashboard"] = stats
        total = stats.get("total_revenue", 0)
        invoices = stats.get("invoice_count", 0)
        subs = stats.get("active_subscriptions", 0)
        data_sales = stats.get("data_sales", 0)
        nft_sales = stats.get("nft_sales", 0)
        _print_protocol("")
        _print_protocol("  [DASHBOARD] ESTADO DEL BUNKER (Ultimas 24h):")
        _print_protocol(f"   Ingresos totales:     {total:,.2f} EUR")
        _print_protocol(f"   Facturas emitidas:     {invoices}")
        _print_protocol(f"   Suscripciones activas: {subs}")
        _print_protocol(f"   Ventas datos:          {data_sales}")
        _print_protocol(f"   Ventas NFT:            {nft_sales}")
    except Exception as e:
        logger.warning("Fase dashboard: %s", e)
        results["dashboard_error"] = str(e)
        errores.append(f"dashboard: {e}")
        _print_protocol(f"[DASHBOARD] Advertencia: {e}")

    results["timestamp"] = hoy.isoformat()
    _print_protocol("")
    if errores:
        _print_protocol(f"[IGNICION] Ciclo completado con advertencias ({len(errores)}).")
    else:
        _print_protocol("[IGNICION] Ciclo completado con exito.")
    _print_protocol("")
    _print_protocol('Sentencia de Sabionda (El Amanecer Economico):')
    _print_protocol('"Arquitecto, el bunker ha ejecutado el Protocolo de Ignicion Comercial.')
    _print_protocol(' La infraestructura es util (genera valor), legal (rinde cuentas) y coherente (se gobierna a si misma)."')
    _print_protocol("")
    return results


async def ignicion_comercial_diaria_async() -> Dict[str, Any]:
    """Versión async para integración con event loop (ej. FastAPI startup)."""
    return ignicion_comercial_diaria()


if __name__ == "__main__":
    ignicion_comercial_diaria()
