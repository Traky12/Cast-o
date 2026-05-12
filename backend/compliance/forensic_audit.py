# backend/compliance/forensic_audit.py — Informes forenses (ISO 27018, GDPR, NIST SP 800-86)

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from backend.security.end_to_end_encryption import EndToEndEncryption
    _E2E = True
except ImportError:
    EndToEndEncryption = None
    _E2E = False

try:
    from backend.compliance.immutable_traceability import ImmutableTraceability
    _TRACE = True
except ImportError:
    ImmutableTraceability = None
    _TRACE = False


def _blake3_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    try:
        return hashlib.blake3(data).hexdigest()
    except AttributeError:
        return hashlib.sha3_512(data).hexdigest()


class ForensicAuditGenerator:
    """
    Generador de informes forenses:
    - Evidencias criptográficamente verificables
    - Cumplimiento ISO 27018, GDPR
    - Trazabilidad para procesos legales
    """

    def __init__(
        self,
        encryption: Any,
        traceability: Any,
        audit_private_key: Optional[bytes] = None,
    ) -> None:
        self.encryption = encryption
        self.traceability = traceability
        self.audit_private_key = audit_private_key

    def generate_audit_report(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Genera informe forense para el período [start_time, end_time] (ISO8601)."""
        try:
            chain = getattr(self.traceability, "current_chain", [])
            in_range = [b for b in chain if start_time <= b.get("timestamp", "") <= end_time]
            forensic_events = [b for b in in_range if b.get("event_type") == "forensic_evidence"]
            report: Dict[str, Any] = {
                "metadata": {
                    "report_type": "forensic_audit",
                    "period": {"start": start_time, "end": end_time},
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "total_events": len(forensic_events),
                    "normative_compliance": [
                        "ISO_27018:2019",
                        "GDPR:Art.33",
                        "GDPR:Art.34",
                        "NIST_SP_800-86",
                    ],
                },
                "evidences": [],
                "statistics": {"by_type": {}, "by_severity": {}, "timeline": []},
            }
            for block in forensic_events:
                try:
                    event = block.get("event") or {}
                    envelope = event.get("encrypted_evidence")
                    evidence = None
                    if envelope and self.audit_private_key and self.encryption:
                        decrypted, valid = self.encryption.verify_and_decrypt_envelope(
                            envelope,
                            self.audit_private_key,
                        )
                        if valid and decrypted is not None:
                            evidence = decrypted if isinstance(decrypted, dict) else json.loads(decrypted) if isinstance(decrypted, str) else None
                    if evidence is None:
                        evidence = event.get("evidence_plain")
                    if evidence is None:
                        continue
                    block_hash = self.traceability._generate_block_hash(block)
                    report["evidences"].append({
                        "block_hash": block_hash,
                        "evidence": evidence,
                        "timestamp": block.get("timestamp", ""),
                    })
                    etype = evidence.get("type", "unknown")
                    sev = evidence.get("severity", "low")
                    report["statistics"]["by_type"][etype] = report["statistics"]["by_type"].get(etype, 0) + 1
                    report["statistics"]["by_severity"][sev] = report["statistics"]["by_severity"].get(sev, 0) + 1
                    report["statistics"]["timeline"].append({
                        "timestamp": block.get("timestamp", ""),
                        "type": etype,
                        "severity": sev,
                    })
                except Exception as e:
                    logger.debug("Error procesando bloque forense: %s", e)
                    if self.traceability:
                        self.traceability.register_event({
                            "type": "forensic_audit_error",
                            "error": str(e),
                            "block_hash": self.traceability._generate_block_hash(block),
                            "severity": "critical",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
            by_type = report["statistics"]["by_type"]
            by_sev = report["statistics"]["by_severity"]
            report["summary"] = {
                "total_evidences": len(report["evidences"]),
                "most_common_type": max(by_type.items(), key=lambda x: x[1], default=("none", 0))[0] if by_type else "none",
                "most_severe": max(by_sev.items(), key=lambda x: x[1], default=("none", 0))[0] if by_sev else "none",
                "period_covered": f"{start_time} to {end_time}",
            }
            report_hash = _blake3_hex(json.dumps(report, sort_keys=True))
            if self.traceability:
                self.traceability.register_event({
                    "type": "forensic_audit_generated",
                    "report_hash": report_hash,
                    "period": {"start": start_time, "end": end_time},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "normative_references": ["ISO_27018:7.1.2", "GDPR:Art.30", "NIST_SP_800-86:6.3"],
                })
            return report
        except Exception as e:
            if self.traceability:
                self.traceability.register_event({
                    "type": "forensic_audit_error",
                    "error": str(e),
                    "severity": "critical",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            raise

    def export_audit_report(self, report: Dict[str, Any], output_file: str, recipient_public_key: bytes) -> str:
        """Exporta informe forense a archivo cifrado y firmado."""
        report_hash = _blake3_hex(json.dumps(report, sort_keys=True))
        envelope = self.encryption.create_encrypted_envelope(
            report,
            recipient_public_key,
            metadata={
                "type": "forensic_audit_export",
                "report_hash": report_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "normative_compliance": ["ISO_27018:7.1.3", "GDPR:Art.30", "NIST_SP_800-86:6.4"],
            },
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2)
        if self.traceability:
            self.traceability.register_event({
                "type": "forensic_audit_exported",
                "report_hash": report_hash,
                "output_file": output_file,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        return output_file


def _main() -> None:
    import argparse
    import os
    from datetime import datetime, timezone, timedelta
    parser = argparse.ArgumentParser(description="Forensic audit report generator")
    parser.add_argument("--period", type=int, default=7, help="Days to include")
    parser.add_argument("--output", type=str, default="/var/traceability/daily_forensic_audit.json")
    parser.add_argument("--register-gaiachain", action="store_true")
    args = parser.parse_args()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.period)
    start_str = start.isoformat()
    end_str = end.isoformat()
    try:
        from backend.security.end_to_end_encryption import EndToEndEncryption
        from backend.compliance.immutable_traceability import ImmutableTraceability
        enc = EndToEndEncryption()
        trace = ImmutableTraceability(enc)
        priv, pub = enc.generate_key_pair()
        gen = ForensicAuditGenerator(enc, trace, audit_private_key=priv)
        report = gen.generate_audit_report(start_str, end_str)
        gen.export_audit_report(report, args.output, pub)
        print(f"Report written to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    _main()
