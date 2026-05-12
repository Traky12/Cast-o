#!/usr/bin/env python3
"""
Rotación de claves de cifrado homomórfico (HE) para Federated Learning.
- Genera nuevo contexto CKKS
- Registra en GaiaChain para auditoría
- Opción de distribuir a nodos (Kubernetes Job simulado)
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

_TS = None
_NUMPY = False
try:
    import tenseal as ts
    _TS = ts
except ImportError:
    ts = None
try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None


def _get_traceability():
    try:
        from backend.compliance.traceability import EndToEndTraceability
        return EndToEndTraceability()
    except Exception:
        return None


class HEKeyRotator:
    """Rota claves HE (CKKS) y registra en GaiaChain."""

    def __init__(self, scheme: str = "CKKS", dry_run: bool = True) -> None:
        self.scheme = scheme.upper()
        self.dry_run = dry_run
        self.traceability = _get_traceability()
        self.current_context: Any = None
        self.new_context: Any = None

    def generate_new_he_context(self) -> Any:
        """Genera un nuevo contexto HE (solo CKKS soportado con esta API)."""
        if not _TS:
            raise RuntimeError("tenseal no instalado. pip install tenseal")
        if self.scheme != "CKKS":
            raise ValueError("Solo CKKS soportado en esta versión; use --scheme CKKS")
        return ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=[60, 40, 40, 60],
        )

    def load_current_context(self) -> Optional[Any]:
        """Carga el contexto HE actual (simulado; en producción desde Vault/GaiaChain)."""
        try:
            logger.info("Cargando contexto HE actual (en producción usar Vault/GaiaChain)")
            ctx = self.generate_new_he_context()
            ctx.global_scale = 2**40
            ctx.generate_galois_keys()
            return ctx
        except Exception as e:
            logger.error("Error al cargar contexto: %s", e)
            return None

    def rotate_keys(self) -> Dict[str, Any]:
        """Genera nuevo contexto, registra en GaiaChain y opcionalmente distribuye."""
        try:
            self.current_context = self.load_current_context()
            if not self.current_context:
                return {"status": "error", "error": "No se pudo cargar el contexto actual"}

            self.new_context = self.generate_new_he_context()
            self.new_context.global_scale = 2**40
            self.new_context.generate_galois_keys()

            poly_old = getattr(self.current_context, "poly_modulus_degree", 8192)
            poly_new = getattr(self.new_context, "poly_modulus_degree", 8192)

            rotation_record = {
                "type": "he_key_rotation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "old_context": {"scheme": self.scheme, "poly_modulus_degree": poly_old, "security_level": "128-bit"},
                "new_context": {"scheme": self.scheme, "poly_modulus_degree": poly_new, "security_level": "128-bit"},
                "normative_references": ["ISO_27001:A.10.1.1", "GDPR:Art.32", "NIST_SP_800-56C"],
            }
            if self.traceability:
                self.traceability.register_event(rotation_record)

            if not self.dry_run:
                self._distribute_new_keys()

            return {
                "status": "success",
                "old_poly_modulus_degree": poly_old,
                "new_poly_modulus_degree": poly_new,
                "gaiachain_event": rotation_record,
            }
        except Exception as e:
            logger.error("Error en rotación: %s", e)
            return {"status": "error", "error": str(e)}

    def _distribute_new_keys(self) -> None:
        """Simula distribución a nodos (Kubernetes Job)."""
        logger.info("Distribución de nuevas claves a nodos (simulada)")
        try:
            subprocess.run(
                [
                    "kubectl", "create", "job", "--from=cronjob/he-key-rotation",
                    f"--namespace=castuo", f"he-key-rotation-{int(datetime.now(timezone.utc).timestamp())}",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.debug("kubectl no disponible o timeout: %s", e)

    def test_rotation(self, test_data: Optional[Any] = None) -> Dict[str, Any]:
        """Prueba rotación: cifra con contexto viejo, rota, cifra con nuevo y compara descifrados."""
        if not _NUMPY or np is None:
            return {"status": "error", "error": "numpy requerido para test"}
        if not _TS:
            return {"status": "error", "error": "tenseal requerido para test"}
        data = test_data if test_data is not None else np.random.randn(10)
        arr = np.array(data, dtype=float)
        try:
            self.current_context = self.load_current_context()
            if not self.current_context:
                return {"status": "error", "error": "No se pudo cargar contexto"}
            self.current_context.global_scale = 2**40
            self.current_context.generate_galois_keys()

            old_vector = ts.ckks_vector(self.current_context, arr.tolist())
            result = self.rotate_keys()
            if result.get("status") != "success":
                return result

            new_vector = ts.ckks_vector(self.new_context, arr.tolist())
            old_dec = np.array(old_vector.decrypt())
            new_dec = np.array(new_vector.decrypt())
            diff = np.abs(old_dec - new_dec)
            return {
                **result,
                "test_results": {
                    "max_diff": float(np.max(diff)),
                    "avg_diff": float(np.mean(diff)),
                    "test_status": "success" if np.max(diff) < 1e-5 else "warning",
                },
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Rotación de claves HE para Federated Learning")
    parser.add_argument("--scheme", choices=["CKKS"], default="CKKS", help="Esquema HE (CKKS)")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin cambios reales")
    parser.add_argument("--test", action="store_true", help="Ejecutar prueba con datos de ejemplo")
    parser.add_argument("--test-size", type=int, default=100, help="Tamaño del vector de prueba")
    args = parser.parse_args()

    rotator = HEKeyRotator(scheme=args.scheme, dry_run=args.dry_run)

    if args.test:
        test_data = np.random.randn(args.test_size) if _NUMPY else list(range(min(10, args.test_size)))
        logger.info("Ejecutando prueba con vector de tamaño %s", args.test_size)
        result = rotator.test_rotation(test_data)
        print(json.dumps(result, indent=2, default=str))
    else:
        logger.info("Rotando claves HE (%s) %s", args.scheme, "(simulación)" if args.dry_run else "")
        result = rotator.rotate_keys()
        print(json.dumps(result, indent=2, default=str))
        if result.get("status") == "success" and not args.dry_run:
            out_path = _root / "he_context.json"
            try:
                with open(out_path, "w") as f:
                    json.dump({
                        "scheme": args.scheme,
                        "rotation_time": datetime.now(timezone.utc).isoformat(),
                        "poly_modulus_degree": result.get("new_poly_modulus_degree", 8192),
                    }, f, indent=2)
                logger.info("Metadatos de contexto guardados en %s", out_path)
            except Exception as e:
                logger.warning("No guardar he_context.json: %s", e)


if __name__ == "__main__":
    main()
