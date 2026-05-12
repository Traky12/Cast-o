# -*- coding: utf-8 -*-
"""API Cuentas Pro: jerarquía, permisos, moderación y cumplimiento ético."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from backend.models.pro_account import (
    ContentRestriction,
    EthicalGuideline,
    ProAccount,
    ProAccountActivity,
    ProAccountTier,
    ProUserProfile,
)
from backend.models.cannabis_specific import (
    CannabisBatch,
    CannabisLicense,
    CannabisStrain,
)
from backend.models.microgreens_specific import (
    MicrogreenBatch,
    MicrogreenCertificate,
    MicrogreenVariety,
)
from backend.models.permissions import ACCOUNT_TIERS, ROLE_PERMISSIONS, check_permission
from backend.services.compliance_validator import ComplianceValidator
from backend.services.content_moderator import ContentModerator
from backend.services.transparency_report import TransparencyReport
from backend.services.cannabis_compliance import CannabisComplianceValidator
from backend.services.blockchain_integration import CannabisBlockchainService
from backend.services.microgreen_compliance import MicrogreenComplianceValidator
from backend.services.iot_integration import MicrogreenIoTService

router = APIRouter(prefix="/pro-accounts", tags=["Pro Accounts"])

pro_accounts_db: Dict[str, ProAccount] = {}
pro_users_db: Dict[str, ProUserProfile] = {}
token_to_user: Dict[str, str] = {}  # token -> user_id (para login simple)

# Cannabis medicinal (RD 903/2025)
cannabis_licenses_db: Dict[str, CannabisLicense] = {}
cannabis_batches_db: Dict[str, CannabisBatch] = {}

# Microgreens
microgreen_varieties_db: Dict[str, MicrogreenVariety] = {}
microgreen_batches_db: Dict[str, MicrogreenBatch] = {}
microgreen_certificates_db: Dict[str, MicrogreenCertificate] = {}

cannabis_validator = CannabisComplianceValidator()
blockchain_service = CannabisBlockchainService()
microgreen_validator = MicrogreenComplianceValidator()
iot_service = MicrogreenIoTService()


def _register_account_in_master(account: ProAccount) -> None:
    """Registra la cuenta en el core SABIONDA para permisos y validación de contenido."""
    try:
        from backend.services.sabionda_master import get_sabionda_master
        get_sabionda_master().register_pro_account(account)
    except Exception:
        pass

validator_compliance = ComplianceValidator()
transparency = TransparencyReport()


# --- Auth: dependencia opcional (Bearer token o X-User-ID para desarrollo) ---
async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
) -> Optional[ProUserProfile]:
    """Obtiene el usuario actual si hay token o X-User-ID."""
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        user_id = token_to_user.get(token)
    if not user_id and x_user_id:
        user_id = x_user_id.strip()
    if user_id and user_id in pro_users_db:
        return pro_users_db[user_id]
    return None


async def get_current_user(
    user: Optional[ProUserProfile] = Depends(get_current_user_optional),
) -> ProUserProfile:
    """Exige usuario autenticado."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado. Usa Authorization: Bearer <token> o X-User-ID.",
        )
    if user.status in ("suspended", "banned"):
        raise HTTPException(status_code=403, detail="Cuenta suspendida o bloqueada")
    return user


# --- Request bodies ---
class CreateProAccountBody(BaseModel):
    email: str = ""
    full_name: str = ""
    tier: str = "basic"
    ethics: Dict[str, Any] = {}
    restrictions: Dict[str, Any] = {}


class AddMemberBody(BaseModel):
    email: str = ""
    full_name: str = ""
    role: str = "user"
    restrictions: Dict[str, Any] = {}


class LoginBody(BaseModel):
    email: str = ""
    password: str = ""


class ModerateBody(BaseModel):
    content: Dict[str, Any] = {}


class ConsentBody(BaseModel):
    """Registro de consentimiento (GDPR Art. 7)."""
    user_id: str = ""
    purpose: str = ""  # ej: marketing, analytics, necessary


class HarvestCannabisBody(BaseModel):
    """Datos de cosecha de cannabis."""
    weight: float = 0.0
    lab_test_results: Optional[Dict[str, Any]] = None


class HarvestMicrogreenBody(BaseModel):
    """Datos de cosecha de microgreens."""
    weight: float = 0.0
    notes: Optional[str] = None


def _ensure_microgreen_varieties() -> None:
    """Inicializa variedades de microgreens si están vacías."""
    if microgreen_varieties_db:
        return
    microgreen_varieties_db["radish"] = MicrogreenVariety(
        variety_id="radish",
        name="Rábano",
        scientific_name="Raphanus sativus",
        growth_cycle=7,
        ideal_ph=6.0,
        ideal_ec=1.2,
        ideal_temperature=(18.0, 22.0),
        ideal_humidity=(60.0, 70.0),
        nutritional_value={"vitamin_c": "high", "antioxidants": "medium"},
    )
    microgreen_varieties_db["broccoli"] = MicrogreenVariety(
        variety_id="broccoli",
        name="Brócoli",
        scientific_name="Brassica oleracea",
        growth_cycle=10,
        ideal_ph=6.2,
        ideal_ec=1.5,
        ideal_temperature=(20.0, 24.0),
        ideal_humidity=(65.0, 75.0),
        nutritional_value={"vitamin_k": "high", "fiber": "high"},
    )


@router.get("/", response_model=List[ProAccount])
async def list_pro_accounts() -> List[ProAccount]:
    """Lista cuentas Pro (en producción restringir por permisos)."""
    return list(pro_accounts_db.values())


@router.post("/", response_model=ProAccount)
async def create_pro_account(body: CreateProAccountBody) -> ProAccount:
    """Crea una nueva cuenta Pro."""
    if body.tier not in ACCOUNT_TIERS:
        raise HTTPException(status_code=400, detail="Nivel de cuenta no válido")

    account_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    tier = ACCOUNT_TIERS[body.tier]
    ethics = EthicalGuideline(**(body.ethics or {}))
    restrictions = ContentRestriction(**(body.restrictions or {}))

    owner = ProUserProfile(
        user_id=user_id,
        email=body.email or "owner@example.com",
        full_name=body.full_name or "Owner",
        role="admin",
        tier=tier,
        restrictions=restrictions,
        ethics=ethics,
    )

    new_account = ProAccount(
        account_id=account_id,
        owner=owner,
        members=[owner],
        status="active",
    )
    pro_accounts_db[account_id] = new_account
    pro_users_db[user_id] = owner
    _register_account_in_master(new_account)
    return new_account


@router.get("/{account_id}", response_model=ProAccount)
async def get_pro_account(
    account_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> ProAccount:
    """Obtiene una cuenta Pro (solo miembros)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro de esta cuenta")
    return account


@router.post("/{account_id}/members", response_model=ProUserProfile)
async def add_member(
    account_id: str,
    body: AddMemberBody,
    current_user: ProUserProfile = Depends(get_current_user),
) -> ProUserProfile:
    """Añade un miembro (solo admin/owner)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if account.owner and current_user.user_id != account.owner.user_id:
        raise HTTPException(status_code=403, detail="Solo el dueño puede añadir miembros")

    member_id = str(uuid.uuid4())
    restrictions = ContentRestriction(**(body.restrictions or {}))
    member = ProUserProfile(
        user_id=member_id,
        email=body.email or "",
        full_name=body.full_name or "",
        role=body.role if body.role in ("user", "moderator", "auditor", "data_protection_officer") else "user",
        tier=account.owner.tier if account.owner else None,
        restrictions=restrictions,
    )
    account.members.append(member)
    pro_users_db[member_id] = member

    account.activity_log.append(
        ProAccountActivity(
            action="member_added",
            metadata={"member_id": member_id, "member_email": member.email},
        )
    )
    return member


@router.get("/{account_id}/members", response_model=List[ProUserProfile])
async def list_members(
    account_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> List[ProUserProfile]:
    """Lista los miembros de una cuenta Pro."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro de esta cuenta")
    return account.members


@router.put("/{account_id}/members/{user_id}/role", response_model=ProUserProfile)
async def update_member_role(
    account_id: str,
    user_id: str,
    new_role: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> ProUserProfile:
    """Actualiza el rol de un miembro (solo admin)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if account.owner and current_user.user_id != account.owner.user_id:
        raise HTTPException(status_code=403, detail="Solo el dueño puede cambiar roles")

    member = next((m for m in account.members if m.user_id == user_id), None)
    if not member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    if new_role not in ("user", "moderator", "auditor", "data_protection_officer"):
        raise HTTPException(status_code=400, detail="Rol no válido")

    old_role = member.role
    member.role = new_role
    account.activity_log.append(
        ProAccountActivity(
            action="role_updated",
            metadata={"user_id": user_id, "old_role": old_role, "new_role": new_role},
        )
    )
    return member


@router.get("/{account_id}/activity", response_model=List[ProAccountActivity])
async def get_activity_log(
    account_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> List[ProAccountActivity]:
    """Registro de actividad (solo admin/auditor)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro")
    if current_user.role not in ("admin", "auditor", "data_protection_officer"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    return account.activity_log


@router.put("/{account_id}/restrictions", response_model=ProAccount)
async def update_restrictions(
    account_id: str,
    restrictions: ContentRestriction,
    current_user: ProUserProfile = Depends(get_current_user),
) -> ProAccount:
    """Actualiza restricciones de contenido (solo admin)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if account.owner and current_user.user_id != account.owner.user_id:
        raise HTTPException(status_code=403, detail="Solo el dueño puede actualizar restricciones")

    for member in account.members:
        member.restrictions = restrictions
    account.activity_log.append(
        ProAccountActivity(action="restrictions_updated", metadata={})
    )
    return account


@router.get("/{account_id}/compliance", response_model=List[Dict[str, Any]])
async def get_compliance_reports(
    account_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Informes de cumplimiento (solo admin/auditor)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.role not in ("admin", "auditor", "data_protection_officer"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    return account.compliance_reports


@router.post("/{account_id}/compliance", response_model=ProAccount)
async def generate_compliance_report(
    account_id: str,
    report_type: str = "monthly",
    current_user: ProUserProfile = Depends(get_current_user),
) -> ProAccount:
    """Genera un informe de cumplimiento (solo admin/auditor/DPO)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.role not in ("admin", "auditor", "data_protection_officer"):
        raise HTTPException(status_code=403, detail="Permiso denegado")

    report = validator_compliance.generate_compliance_report(account)
    account.compliance_reports.append(report)
    account.activity_log.append(
        ProAccountActivity(
            action="compliance_report_generated",
            metadata={"report_type": report_type},
        )
    )
    return account


@router.post("/{account_id}/login")
async def login(
    account_id: str,
    body: LoginBody,
) -> Dict[str, str]:
    """Inicia sesión y devuelve un token (en producción usar bcrypt + JWT)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    user = next(
        (u for u in account.members if u.email == body.email),
        None,
    )
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    # Demo: cualquier contraseña aceptada; en producción verificar hash
    token = str(uuid.uuid4())
    token_to_user[token] = user.user_id
    account.activity_log.append(
        ProAccountActivity(
            action="login",
            metadata={"user_id": user.user_id, "email": user.email},
        )
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/{account_id}/moderate")
async def moderate_content_endpoint(
    account_id: str,
    body: ModerateBody,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida contenido según las restricciones de la cuenta."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if current_user.user_id not in [m.user_id for m in pro_accounts_db[account_id].members]:
        raise HTTPException(status_code=403, detail="No eres miembro")

    moderator = ContentModerator(current_user.restrictions)
    results: Dict[str, Any] = {}
    for key, value in (body.content or {}).items():
        if isinstance(value, str):
            is_valid, message = moderator.moderate_text(value)
            results[key] = {"valid": is_valid, "message": message}
        elif isinstance(value, dict) and "url" in value:
            results[key] = {
                "valid": moderator.moderate_url(str(value["url"])),
                "message": "URL validada",
            }
    return {
        "results": results,
        "overall_valid": all(r.get("valid", False) for r in results.values()),
    }


@router.get("/{account_id}/audit")
async def run_ethics_audit(
    account_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Ejecuta una auditoría ética en la cuenta (solo admin/auditor)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.role not in ("admin", "auditor", "data_protection_officer"):
        raise HTTPException(status_code=403, detail="Permiso denegado")

    report = validator_compliance.generate_compliance_report(account)
    account.compliance_reports.append(report)
    account.activity_log.append(
        ProAccountActivity(action="ethics_audit", metadata={})
    )
    return report


@router.post("/{account_id}/consent")
async def record_consent(
    account_id: str,
    body: ConsentBody,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, str]:
    """Registra el consentimiento del usuario (GDPR Art. 7). Solo admin o data_protection_officer."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro de esta cuenta")
    if current_user.role not in ("admin", "data_protection_officer"):
        raise HTTPException(status_code=403, detail="Permiso denegado")

    record = {
        "user_id": body.user_id,
        "purpose": body.purpose or "general",
        "consent_date": datetime.utcnow().isoformat(),
        "recorded_by": current_user.user_id,
    }
    account.consent_records.append(record)
    account.activity_log.append(
        ProAccountActivity(
            action="consent_recorded",
            metadata={"user_id": body.user_id, "purpose": body.purpose},
        )
    )
    return {"status": "consent_recorded"}


@router.delete("/{account_id}/users/{user_id}/data")
async def erase_user_data(
    account_id: str,
    user_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, str]:
    """Solicitud de borrado de datos de un usuario (GDPR Art. 17 - Derecho al olvido). Solo admin o data_protection_officer."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro de esta cuenta")
    if current_user.role not in ("admin", "data_protection_officer"):
        raise HTTPException(status_code=403, detail="Permiso denegado")

    member = next((m for m in account.members if m.user_id == user_id), None)
    if member:
        member.status = "data_erased"
        pro_users_db[user_id] = member
    account.activity_log.append(
        ProAccountActivity(
            action="data_erasure_request",
            metadata={"user_id": user_id, "requested_by": current_user.user_id},
        )
    )
    return {"status": "data_erasure_requested"}


@router.get("/{account_id}/transparency")
async def get_transparency_report(
    account_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Informe de transparencia para el usuario (GDPR)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro")

    account.activity_log.append(
        ProAccountActivity(
            action="transparency_report_generated",
            metadata={"user_id": current_user.user_id},
        )
    )
    return transparency.generate_report(account, current_user)


# ---------- Cannabis medicinal (RD 903/2025) ----------

@router.post("/{account_id}/cannabis/licenses", response_model=CannabisLicense)
async def create_cannabis_license(
    account_id: str,
    license_data: CannabisLicense,
    current_user: ProUserProfile = Depends(get_current_user),
) -> CannabisLicense:
    """Crea una licencia de cultivo de cannabis medicinal (solo admin/moderator)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro de esta cuenta")
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    tier = account.owner.tier if account.owner else None
    if tier and "cannabis_management" not in getattr(tier, "features", []) and "all" not in getattr(tier, "features", []):
        raise HTTPException(status_code=403, detail="Tu tier no soporta gestión de cannabis")

    license_id = f"CAN-{datetime.utcnow().strftime('%Y%m%d')}-{len(cannabis_licenses_db) + 1}"
    license_data.license_id = license_id
    cannabis_licenses_db[license_id] = license_data
    account.activity_log.append(
        ProAccountActivity(
            action="cannabis_license_created",
            metadata={"license_id": license_id, "holder": license_data.holder},
        )
    )
    return license_data


@router.get("/{account_id}/cannabis/licenses", response_model=List[CannabisLicense])
async def list_cannabis_licenses(
    account_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> List[CannabisLicense]:
    """Lista las licencias de cannabis de una cuenta."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro")
    if current_user.role not in ("admin", "moderator", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    owner_email = account.owner.email if account.owner else ""
    return [lic for lic in cannabis_licenses_db.values() if lic.holder == owner_email]


@router.post("/{account_id}/cannabis/batches", response_model=CannabisBatch)
async def create_cannabis_batch(
    account_id: str,
    batch_data: CannabisBatch,
    current_user: ProUserProfile = Depends(get_current_user),
) -> CannabisBatch:
    """Registra un lote de cannabis medicinal."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro")
    if current_user.role not in ("admin", "moderator", "user"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    lic_key = batch_data.strain.cultivation_license
    if lic_key not in cannabis_licenses_db:
        raise HTTPException(status_code=400, detail="Licencia no válida")
    if cannabis_licenses_db[lic_key].status != "active":
        raise HTTPException(status_code=400, detail="Licencia no activa")

    batch_id = f"BATCH-{datetime.utcnow().strftime('%Y%m%d')}-{len(cannabis_batches_db) + 1}"
    batch_data.batch_id = batch_id
    batch_data.account_id = account_id
    batch_data.status = "planted"
    cannabis_batches_db[batch_id] = batch_data
    batch_data.blockchain_tx = f"tx_{batch_id}_cannabis"
    account.activity_log.append(
        ProAccountActivity(
            action="cannabis_batch_created",
            metadata={"batch_id": batch_id, "strain": batch_data.strain.name},
        )
    )
    return batch_data


@router.get("/{account_id}/cannabis/batches", response_model=List[CannabisBatch])
async def list_cannabis_batches(
    account_id: str,
    status: Optional[str] = None,
    current_user: ProUserProfile = Depends(get_current_user),
) -> List[CannabisBatch]:
    """Lista los lotes de cannabis de una cuenta."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if current_user.user_id not in [m.user_id for m in pro_accounts_db[account_id].members]:
        raise HTTPException(status_code=403, detail="No eres miembro")
    if current_user.role not in ("admin", "moderator", "user", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    batches = [b for b in cannabis_batches_db.values() if b.account_id == account_id]
    if status:
        batches = [b for b in batches if b.status == status]
    return batches


@router.put("/{account_id}/cannabis/batches/{batch_id}/harvest", response_model=CannabisBatch)
async def mark_batch_as_harvested(
    account_id: str,
    batch_id: str,
    body: HarvestCannabisBody,
    current_user: ProUserProfile = Depends(get_current_user),
) -> CannabisBatch:
    """Marca un lote como cosechado y registra resultados de laboratorio."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in cannabis_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro")
    if current_user.role not in ("admin", "moderator", "user"):
        raise HTTPException(status_code=403, detail="Permiso denegado")

    batch = cannabis_batches_db[batch_id]
    batch.weight = body.weight
    batch.harvest_date = datetime.utcnow()
    batch.lab_test_results = body.lab_test_results
    batch.status = "harvested"
    if batch.lab_test_results and batch.lab_test_results.get("thc", 0) > 0.3:
        batch.certification_status = "rejected"
        account.activity_log.append(
            ProAccountActivity(
                action="cannabis_batch_thc_rejected",
                metadata={"batch_id": batch_id, "thc": batch.lab_test_results.get("thc")},
            )
        )
        raise HTTPException(status_code=400, detail="Nivel de THC excede el límite legal (0.3%)")
    batch.blockchain_tx = f"tx_{batch_id}_harvested_{datetime.utcnow().strftime('%Y%m%d')}"
    account.activity_log.append(
        ProAccountActivity(
            action="cannabis_batch_harvested",
            metadata={"batch_id": batch_id, "weight": batch.weight},
        )
    )
    return batch


@router.post("/{account_id}/cannabis/batches/{batch_id}/certify")
async def certify_cannabis_batch(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Genera un certificado de cumplimiento para un lote de cannabis."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in cannabis_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    account = pro_accounts_db[account_id]
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    batch = cannabis_batches_db[batch_id]
    if batch.status != "harvested":
        raise HTTPException(status_code=400, detail="El lote no está cosechado")

    certificate = {
        "batch_id": batch_id,
        "strain": batch.strain.name,
        "weight": batch.weight,
        "thc": (batch.lab_test_results or {}).get("thc", 0),
        "cbd": (batch.lab_test_results or {}).get("cbd", 0),
        "compliance": batch.strain.compliance_standards,
        "blockchain_tx": batch.blockchain_tx,
        "certification_date": datetime.utcnow().isoformat(),
        "issued_by": "CTAEX + AEMPS",
        "qr_code": f"https://certificates.castu.system/cannabis/{batch_id}",
    }
    batch.status = "certified"
    batch.certification_date = datetime.utcnow()
    batch.certification_status = "approved"
    account.activity_log.append(
        ProAccountActivity(
            action="cannabis_batch_certified",
            metadata={"batch_id": batch_id, "certificate_id": certificate.get("blockchain_tx")},
        )
    )
    return certificate


@router.get("/{account_id}/cannabis/licenses/{license_id}/validate")
async def validate_cannabis_license(
    account_id: str,
    license_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida una licencia de cannabis con AEMPS."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if license_id not in cannabis_licenses_db:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    if current_user.role not in ("admin", "moderator", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    is_valid, errors = cannabis_validator.validate_cannabis_license(
        cannabis_licenses_db[license_id]
    )
    return {"valid": is_valid, "errors": errors}


@router.get("/{account_id}/cannabis/batches/{batch_id}/validate")
async def validate_cannabis_batch(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida un lote de cannabis según RD 903/2025."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in cannabis_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if current_user.role not in ("admin", "moderator", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    is_valid, errors = cannabis_validator.validate_cannabis_batch(
        cannabis_batches_db[batch_id], cannabis_licenses_db
    )
    return {"valid": is_valid, "errors": errors}


@router.get("/{account_id}/cannabis/batches/{batch_id}/aemps-report")
async def generate_aemps_report(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Genera un informe para AEMPS (formato oficial)."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in cannabis_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if current_user.role not in ("admin", "moderator", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    report = cannabis_validator.generate_aemps_report(
        cannabis_batches_db[batch_id], cannabis_licenses_db
    )
    pro_accounts_db[account_id].activity_log.append(
        ProAccountActivity(
            action="aemps_report_generated",
            metadata={"batch_id": batch_id, "report_id": report.get("blockchain_tx")},
        )
    )
    return report


@router.post("/{account_id}/cannabis/licenses/{license_id}/blockchain")
async def register_license_in_blockchain(
    account_id: str,
    license_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Registra una licencia de cannabis en GaiaChain."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if license_id not in cannabis_licenses_db:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    lic = cannabis_licenses_db[license_id]
    tx_hash = blockchain_service.register_cannabis_license(lic)
    lic.blockchain_tx = tx_hash
    cannabis_licenses_db[license_id] = lic
    pro_accounts_db[account_id].activity_log.append(
        ProAccountActivity(
            action="cannabis_license_registered_in_blockchain",
            metadata={"license_id": license_id, "tx_hash": tx_hash},
        )
    )
    return {"tx_hash": tx_hash, "status": "registered"}


@router.post("/{account_id}/cannabis/batches/{batch_id}/blockchain")
async def register_batch_in_blockchain(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Registra un lote de cannabis en GaiaChain."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in cannabis_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if current_user.role not in ("admin", "moderator", "user"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    batch = cannabis_batches_db[batch_id]
    tx_hash = blockchain_service.register_cannabis_batch(batch)
    batch.blockchain_tx = tx_hash
    cannabis_batches_db[batch_id] = batch
    pro_accounts_db[account_id].activity_log.append(
        ProAccountActivity(
            action="cannabis_batch_registered_in_blockchain",
            metadata={"batch_id": batch_id, "tx_hash": tx_hash},
        )
    )
    return {"tx_hash": tx_hash, "status": "registered"}


@router.get("/{account_id}/cannabis/batches/{batch_id}/blockchain/verify")
async def verify_batch_in_blockchain(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Verifica un lote de cannabis en GaiaChain."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in cannabis_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if current_user.role not in ("admin", "moderator", "user", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    verification = blockchain_service.verify_cannabis_batch(batch_id)
    pro_accounts_db[account_id].activity_log.append(
        ProAccountActivity(
            action="cannabis_batch_verified_in_blockchain",
            metadata={"batch_id": batch_id, "valid": verification.get("valid")},
        )
    )
    return verification


# ---------- Microgreens ----------

@router.get("/{account_id}/microgreens/varieties", response_model=List[MicrogreenVariety])
async def list_microgreen_varieties(
    account_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> List[MicrogreenVariety]:
    """Lista las variedades de microgreens disponibles."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if current_user.user_id not in [m.user_id for m in pro_accounts_db[account_id].members]:
        raise HTTPException(status_code=403, detail="No eres miembro")
    _ensure_microgreen_varieties()
    return list(microgreen_varieties_db.values())


@router.post("/{account_id}/microgreens/batches", response_model=MicrogreenBatch)
async def create_microgreen_batch(
    account_id: str,
    batch_data: MicrogreenBatch,
    current_user: ProUserProfile = Depends(get_current_user),
) -> MicrogreenBatch:
    """Crea un lote de microgreens."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    account = pro_accounts_db[account_id]
    if current_user.user_id not in [m.user_id for m in account.members]:
        raise HTTPException(status_code=403, detail="No eres miembro")
    if current_user.role not in ("admin", "moderator", "user"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    _ensure_microgreen_varieties()
    if batch_data.variety.variety_id not in microgreen_varieties_db:
        raise HTTPException(status_code=400, detail="Variedad no válida")

    batch_id = f"MG-{datetime.utcnow().strftime('%Y%m%d')}-{len(microgreen_batches_db) + 1}"
    batch_data.batch_id = batch_id
    batch_data.account_id = account_id
    batch_data.status = "planted"
    microgreen_batches_db[batch_id] = batch_data
    batch_data.blockchain_tx = f"tx_{batch_id}_microgreens"
    account.activity_log.append(
        ProAccountActivity(
            action="microgreen_batch_created",
            metadata={"batch_id": batch_id, "variety": batch_data.variety.name},
        )
    )
    return batch_data


@router.put("/{account_id}/microgreens/batches/{batch_id}/environment", response_model=MicrogreenBatch)
async def update_batch_environment(
    account_id: str,
    batch_id: str,
    env_data: Dict[str, float],
    current_user: ProUserProfile = Depends(get_current_user),
) -> MicrogreenBatch:
    """Actualiza los datos ambientales de un lote de microgreens."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in microgreen_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    account = pro_accounts_db[account_id]
    if current_user.role not in ("admin", "moderator", "user"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    batch = microgreen_batches_db[batch_id]
    batch.environmental_data = env_data
    variety = batch.variety
    if env_data.get("ph") is not None and abs(env_data["ph"] - variety.ideal_ph) > 0.5:
        account.activity_log.append(
            ProAccountActivity(
                action="microgreen_ph_alert",
                metadata={"batch_id": batch_id, "current_ph": env_data["ph"], "ideal_ph": variety.ideal_ph},
            )
        )
    temp = env_data.get("temperature")
    if temp is not None and (temp < variety.ideal_temperature[0] or temp > variety.ideal_temperature[1]):
        account.activity_log.append(
            ProAccountActivity(
                action="microgreen_temperature_alert",
                metadata={"batch_id": batch_id, "current_temp": temp},
            )
        )
    return batch


@router.put("/{account_id}/microgreens/batches/{batch_id}/harvest", response_model=MicrogreenBatch)
async def mark_microgreen_batch_as_harvested(
    account_id: str,
    batch_id: str,
    body: HarvestMicrogreenBody,
    current_user: ProUserProfile = Depends(get_current_user),
) -> MicrogreenBatch:
    """Marca un lote de microgreens como cosechado."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in microgreen_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    account = pro_accounts_db[account_id]
    if current_user.role not in ("admin", "moderator", "user"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    batch = microgreen_batches_db[batch_id]
    batch.harvest_date = datetime.utcnow()
    batch.weight = body.weight
    batch.status = "harvested"
    batch.blockchain_tx = f"tx_{batch_id}_harvested_{datetime.utcnow().strftime('%Y%m%d')}"
    account.activity_log.append(
        ProAccountActivity(
            action="microgreen_batch_harvested",
            metadata={"batch_id": batch_id, "weight": batch.weight},
        )
    )
    return batch


@router.post("/{account_id}/microgreens/batches/{batch_id}/certify", response_model=MicrogreenCertificate)
async def certify_microgreen_batch(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> MicrogreenCertificate:
    """Genera un certificado de calidad para un lote de microgreens."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in microgreen_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    account = pro_accounts_db[account_id]
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    batch = microgreen_batches_db[batch_id]
    if batch.status != "harvested":
        raise HTTPException(status_code=400, detail="El lote no está cosechado")

    certificate_id = f"CERT-MG-{datetime.utcnow().strftime('%Y%m%d')}-{len(microgreen_certificates_db) + 1}"
    cert = MicrogreenCertificate(
        certificate_id=certificate_id,
        batch_id=batch_id,
        variety=batch.variety.name,
        weight=batch.weight or 0,
        harvest_date=batch.harvest_date or datetime.utcnow(),
        environmental_compliance=batch.environmental_data or {},
        organic_status=True,
        blockchain_tx=f"tx_{certificate_id}_certificate",
        issued_by="CTAEX + GlobalGAP",
        issue_date=datetime.utcnow(),
        expiration_date=datetime.utcnow() + timedelta(days=365),
        qr_code=f"https://certificates.castu.system/microgreens/{certificate_id}",
    )
    microgreen_certificates_db[certificate_id] = cert
    batch.certification_status = "approved"
    account.activity_log.append(
        ProAccountActivity(
            action="microgreen_batch_certified",
            metadata={"batch_id": batch_id, "certificate_id": certificate_id},
        )
    )
    return cert


@router.get("/{account_id}/microgreens/batches/{batch_id}/certificate", response_model=MicrogreenCertificate)
async def get_microgreen_certificate(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> MicrogreenCertificate:
    """Obtiene el certificado de un lote de microgreens."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if current_user.user_id not in [m.user_id for m in pro_accounts_db[account_id].members]:
        raise HTTPException(status_code=403, detail="No eres miembro")
    for cert in microgreen_certificates_db.values():
        if cert.batch_id == batch_id:
            return cert
    raise HTTPException(status_code=404, detail="Certificado no encontrado")


@router.get("/{account_id}/microgreens/certificates", response_model=List[MicrogreenCertificate])
async def list_microgreen_certificates(
    account_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> List[MicrogreenCertificate]:
    """Lista los certificados de microgreens de una cuenta."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if current_user.role not in ("admin", "moderator", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    account_batch_ids = {b.batch_id for b in microgreen_batches_db.values() if b.account_id == account_id}
    return [c for c in microgreen_certificates_db.values() if c.batch_id in account_batch_ids]


@router.get("/{account_id}/microgreens/batches/{batch_id}/validate")
async def validate_microgreen_batch(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida un lote de microgreens según GlobalGAP."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in microgreen_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if current_user.role not in ("admin", "moderator", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    batch = microgreen_batches_db[batch_id]
    variety = microgreen_varieties_db.get(batch.variety.variety_id)
    if not variety:
        raise HTTPException(status_code=400, detail="Variedad del lote no encontrada")
    is_valid, errors = microgreen_validator.validate_microgreen_batch(batch, variety)
    return {"valid": is_valid, "errors": errors}


@router.get("/{account_id}/microgreens/batches/{batch_id}/globalgap-report")
async def generate_globalgap_report(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Genera un informe de cumplimiento con GlobalGAP."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in microgreen_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if current_user.role not in ("admin", "moderator", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    batch = microgreen_batches_db[batch_id]
    variety = microgreen_varieties_db.get(batch.variety.variety_id)
    if not variety:
        raise HTTPException(status_code=400, detail="Variedad del lote no encontrada")
    report = microgreen_validator.generate_globalgap_report(batch, variety)
    pro_accounts_db[account_id].activity_log.append(
        ProAccountActivity(
            action="globalgap_report_generated",
            metadata={"batch_id": batch_id, "compliance": report.get("globalgap_compliance")},
        )
    )
    return report


@router.get("/{account_id}/microgreens/batches/{batch_id}/iot")
async def get_microgreen_iot_data(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Obtiene datos de IoT para un lote de microgreens."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in microgreen_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if current_user.role not in ("admin", "moderator", "user", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    iot_data = iot_service.get_environmental_data(batch_id)
    microgreen_batches_db[batch_id].environmental_data = iot_data
    return iot_data


@router.post("/{account_id}/microgreens/batches/{batch_id}/iot")
async def update_microgreen_iot_data(
    account_id: str,
    batch_id: str,
    iot_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Actualiza datos de IoT para un lote de microgreens."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in microgreen_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    account = pro_accounts_db[account_id]
    if current_user.role not in ("admin", "moderator", "user"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    microgreen_batches_db[batch_id].environmental_data = iot_data
    account.activity_log.append(
        ProAccountActivity(
            action="microgreen_iot_data_updated",
            metadata={"batch_id": batch_id},
        )
    )
    return {"status": "success", "batch_id": batch_id}


@router.get("/{account_id}/microgreens/batches/{batch_id}/iot/analysis")
async def analyze_microgreen_environment(
    account_id: str,
    batch_id: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Analiza el entorno de un lote de microgreens y sugiere ajustes."""
    if account_id not in pro_accounts_db:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if batch_id not in microgreen_batches_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    account = pro_accounts_db[account_id]
    if current_user.role not in ("admin", "moderator", "user", "auditor"):
        raise HTTPException(status_code=403, detail="Permiso denegado")
    batch = microgreen_batches_db[batch_id]
    variety = microgreen_varieties_db.get(batch.variety.variety_id, batch.variety)
    analysis = iot_service.analyze_environment(batch, variety)
    if analysis.get("suggestions"):
        account.activity_log.append(
            ProAccountActivity(
                action="microgreen_environment_alert",
                metadata={"batch_id": batch_id, "suggestions": analysis["suggestions"]},
            )
        )
    return analysis
