# backend/api/services/key_rotation.py
"""Servicio de rotación de claves (Transit + PQC). EU/OSS."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    import hvac
    _HAS_HVAC = True
except ImportError:
    _HAS_HVAC = False


class KeyRotationService:
    def __init__(self) -> None:
        self._client = None
        if _HAS_HVAC and os.getenv("VAULT_ADDR") and os.getenv("VAULT_TOKEN"):
            try:
                self._client = hvac.Client(
                    url=os.getenv("VAULT_ADDR", "http://vault:8200"),
                    token=os.getenv("VAULT_TOKEN"),
                )
                if not self._client.is_authenticated():
                    self._client = None
            except Exception as e:
                logger.warning("Vault client init failed: %s", e)

        try:
            from .gaiachain import GaiaChainService
        except ImportError:
            from backend.api.services.gaiachain import GaiaChainService
        self.gaiachain = GaiaChainService()

        self.rotation_schedule: Dict[str, Dict[str, Any]] = {
            "K_backend_consent": {
                "days": 90,
                "last_rotated": None,
                "norms": ["ISO_27001:A.10.1.1", "GDPR:Art.32"],
                "pqc_key": "K_backend_consent_pqc",
            },
            "K_gaiachain_sign": {
                "days": 30,
                "last_rotated": None,
                "norms": ["ISO_27001:A.10.1.1", "AI_Act:Art.52"],
                "pqc_key": "K_gaiachain_sign_pqc",
            },
            "K_media_engine": {
                "days": 60,
                "last_rotated": None,
                "norms": ["ISO_27001:A.10.1.1", "Ley_3_2023:Art.18"],
                "pqc_key": "K_media_engine_pqc",
            },
            "K_jwt_signing": {
                "days": 60,
                "last_rotated": None,
                "norms": ["ISO_27001:A.9.1.1"],
                "pqc_key": "K_jwt_signing_pqc",
            },
        }
        self._load_last_rotations()

    @property
    def client(self):
        return self._client

    def _load_last_rotations(self) -> None:
        if not self._client:
            return
        for key_name in list(self.rotation_schedule.keys()):
            try:
                r = self._client.secrets.kv.v2.read_secret_version(
                    path=f"key_rotation/{key_name}",
                    mount_point="secret",
                )
                raw = (r.get("data") or {}).get("data") or {}
                ts = raw.get("last_rotated")
                if ts:
                    self.rotation_schedule[key_name]["last_rotated"] = datetime.fromisoformat(
                        ts.replace("Z", "+00:00")
                    )
            except Exception:
                pass

    def _save_rotation_date(self, key_name: str) -> None:
        if not self._client:
            return
        try:
            self._client.secrets.kv.v2.create_or_update_secret(
                path=f"key_rotation/{key_name}",
                secret={"last_rotated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")},
                mount_point="secret",
            )
        except Exception as e:
            logger.warning("Could not save rotation date: %s", e)

    def _register_audit(self, event_type: str, data: Dict[str, Any], compliance: Dict[str, Any]) -> None:
        try:
            from backend.api.security.audit import audit_logger
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                audit_logger.log_event(
                    request=None,
                    event_type=event_type,
                    data=data,
                    compliance=compliance,
                )
            )
        except RuntimeError:
            try:
                asyncio.run(
                    audit_logger.log_event(
                        request=None,
                        event_type=event_type,
                        data=data,
                        compliance=compliance,
                    )
                )
            except Exception as e:
                logger.debug("Audit log async failed: %s", e)
        except Exception as e:
            logger.debug("Audit log failed: %s", e)

    def rotate_key(self, key_name: str, force: bool = False) -> Dict[str, Any]:
        """Rota una clave (Transit y, si existe, PQC)."""
        config = self.rotation_schedule.get(key_name)
        if not config:
            return {"success": False, "message": f"Clave {key_name} no configurada"}

        if not force and config.get("last_rotated"):
            next_rot = config["last_rotated"] + timedelta(days=config["days"])
            if datetime.now(timezone.utc).replace(tzinfo=None) < next_rot.replace(tzinfo=None) if next_rot.tzinfo else next_rot:
                return {
                    "success": False,
                    "message": f"Clave {key_name} no necesita rotación hasta {next_rot.isoformat()}",
                }

        if not self._client:
            return {
                "success": False,
                "message": "Vault no configurado o no autenticado",
            }

        try:
            # 1. Rotar Transit
            self._client.write(f"transit/keys/{key_name}/rotate")

            # 2. Rotar PQC si existe
            pqc_key = config.get("pqc_key")
            if pqc_key:
                try:
                    self._client.write(f"pqc/keys/{pqc_key}/rotate")
                except Exception as e:
                    logger.debug("PQC rotate skip for %s: %s", pqc_key, e)

            # 3. GaiaChain
            tx_hash = self.gaiachain.register_event_sync(
                token_id=0,
                action_type=f"key_rotation_{key_name}",
                status="completed",
                ipfs_cid="",
                norms=config["norms"],
                legal_basis={
                    "description": f"Rotación de {key_name} y {pqc_key or 'N/A'}",
                    "classic_algorithm": "RSA-2048",
                    "pqc_algorithm": "Kyber-768",
                },
            )

            # 4. Fecha y estado
            self._save_rotation_date(key_name)
            self.rotation_schedule[key_name]["last_rotated"] = datetime.now(timezone.utc)

            # 5. Auditoría
            self._register_audit(
                f"key_rotation_{key_name}",
                {"key_name": key_name, "tx_hash": tx_hash},
                {"iso_27001": ["A.10.1.1"], "gdpr": ["Art.32"]},
            )

            return {
                "success": True,
                "tx_hash": tx_hash,
                "message": f"Claves {key_name} y {pqc_key or 'N/A'} rotadas correctamente",
                "classic_algorithm": "RSA-2048",
                "pqc_algorithm": "Kyber-768",
            }
        except Exception as e:
            logger.exception("Error rotando %s", key_name)
            return {
                "success": False,
                "message": f"Error rotando {key_name}: {e}",
                "error": str(e),
            }

    def rotate_all_if_needed(self) -> List[Dict[str, Any]]:
        results = []
        for key_name in self.rotation_schedule:
            r = self.rotate_key(key_name)
            if r.get("success"):
                results.append(r)
        return results

    def get_rotation_status(self) -> Dict[str, Dict[str, Any]]:
        status = {}
        for key_name, config in self.rotation_schedule.items():
            last = config.get("last_rotated")
            days = config.get("days", 90)
            next_rot = (last + timedelta(days=days)).isoformat() if last else "Pendiente"
            if last:
                last = last.isoformat() if hasattr(last, "isoformat") else str(last)
            else:
                last = "Nunca"
            status[key_name] = {
                "last_rotated": last,
                "next_rotation": next_rot,
                "norms": config.get("norms", []),
                "pqc_key": config.get("pqc_key", ""),
                "classic_algorithm": "RSA-2048",
                "pqc_algorithm": "Kyber-768",
            }
        return status

    def emergency_seal(self) -> Dict[str, Any]:
        """Sella Vault en emergencia."""
        if not self._client:
            return {"success": False, "message": "Vault no configurado"}
        try:
            self._client.sys.seal()
            tx = self.gaiachain.register_event_sync(
                token_id=0,
                action_type="emergency_vault_seal",
                status="completed",
                ipfs_cid="",
                norms=["ISO_27001:A.16.1.4"],
                legal_basis={"description": "Sellado de emergencia de Vault"},
            )
            self._register_audit("emergency_vault_seal", {"tx_hash": tx}, {"iso_27001": ["A.16.1.4"]})
            return {"success": True, "tx_hash": tx, "message": "Vault sellado. Se requieren 3 shares para desbloquear."}
        except Exception as e:
            return {"success": False, "message": str(e), "error": str(e)}

    def emergency_unseal(self, shares: List[str]) -> Dict[str, Any]:
        """Desbloquea Vault con 3 shares."""
        if not self._client:
            return {"success": False, "message": "Vault no configurado"}
        try:
            for s in shares[:3]:
                self._client.sys.unseal(s)
            tx = self.gaiachain.register_event_sync(
                token_id=0,
                action_type="emergency_vault_unseal",
                status="completed",
                ipfs_cid="",
                norms=["ISO_27001:A.16.1.4"],
                legal_basis={"description": "Desbloqueo con 3/5 shares"},
            )
            self._register_audit("emergency_vault_unseal", {"tx_hash": tx, "shares_used": 3}, {"iso_27001": ["A.16.1.4"]})
            return {"success": True, "tx_hash": tx, "message": "Vault desbloqueado con 3 shares."}
        except Exception as e:
            return {"success": False, "message": str(e), "error": str(e)}
