from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any


def _load_root_audit_module() -> types.ModuleType:
    root = Path(__file__).resolve().parents[2]
    module_path = root / "services" / "audit" / "audit_logger.py"
    spec = importlib.util.spec_from_file_location("castuo_root_audit_logger", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"No se pudo cargar modulo de auditoria: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # necesario para que @dataclass resuelva __module__ en Python 3.12
    spec.loader.exec_module(module)
    return module


_ROOT_AUDIT = _load_root_audit_module()

AuditLogger = _ROOT_AUDIT.AuditLogger
AuditEvent = _ROOT_AUDIT.AuditEvent
AuditAction = _ROOT_AUDIT.AuditAction
AuditSeverity = _ROOT_AUDIT.AuditSeverity
get_audit_logger = _ROOT_AUDIT.get_audit_logger

# Permite `from services.audit.audit_logger import ...` cuando `services` apunta a `api/services`.
_submodule_name = f"{__name__}.audit_logger"
if _submodule_name not in sys.modules:
    audit_logger_module = types.ModuleType(_submodule_name)
    module_any: Any = audit_logger_module
    module_any.AuditLogger = AuditLogger
    module_any.AuditEvent = AuditEvent
    module_any.AuditAction = AuditAction
    module_any.AuditSeverity = AuditSeverity
    module_any.get_audit_logger = get_audit_logger
    sys.modules[_submodule_name] = audit_logger_module

__path__: list[str] = []

__all__ = [
    "AuditLogger",
    "AuditEvent",
    "AuditAction",
    "AuditSeverity",
    "get_audit_logger",
]
