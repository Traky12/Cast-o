# -*- coding: utf-8 -*-
"""
Cumplimiento AEMPS (Agencia Española de Medicamentos y Productos Sanitarios).
Documentación para licencias de cultivo y procesamiento de cannabis (investigación/médico).
Referencia: Ley 17/1967, RD 903/2025 — España.
"""
import json
from datetime import datetime
from typing import Any, Dict, List


class AEMPSCompliance:
    """
    Preparación de solicitudes y documentación para AEMPS.
    Investigación: cannabis fines investigación. Médico: cultivo estupefacientes.
    """

    def __init__(self) -> None:
        self.base_url = "https://www.aemps.gob.es"
        self.required_documents = {
            "investigation": [
                "solicitud_cannabis_fines_investigacion.pdf",
                "proyecto_investigacion.pdf",
                "curriculum_investigador.pdf",
                "autorizacion_etica.pdf",
                "plan_seguridad.pdf",
            ],
            "medical": [
                "solicitud_cultivo_estupefacientes.pdf",
                "proyecto_tecnico.pdf",
                "curriculum_responsable_tecnico.pdf",
                "plan_seguridad_ampliado.pdf",
                "contrato_suministro_sanidad.pdf",
            ],
        }

    def prepare_investigation_application(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara solicitud de autorización para cannabis con fines de investigación."""
        return {
            "type": "investigation",
            "project_name": project_data.get("name", ""),
            "investigator": project_data.get("investigator", ""),
            "institution": project_data.get("institution", ""),
            "objectives": project_data.get("objectives", ""),
            "cannabis_strains": project_data.get("strains", []),
            "quantity_kg": project_data.get("quantity", 0),
            "duration_months": project_data.get("duration", 0),
            "documents": self._generate_documents(project_data, "investigation"),
        }

    def prepare_medical_application(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara solicitud para producción de cannabis medicinal."""
        return {
            "type": "medical",
            "company_name": project_data.get("company_name", ""),
            "responsible_technician": project_data.get("responsible_technician", ""),
            "cultivation_site": project_data.get("cultivation_site", ""),
            "production_capacity_kg": project_data.get("production_capacity", 0),
            "security_plan": project_data.get("security_plan", ""),
            "supply_contract": project_data.get("supply_contract", ""),
            "documents": self._generate_documents(project_data, "medical"),
        }

    def _generate_documents(self, project_data: Dict[str, Any], application_type: str) -> Dict[str, Any]:
        """Genera contenido de documentos requeridos por AEMPS."""
        documents: Dict[str, Any] = {}
        for doc in self.required_documents.get(application_type, []):
            if "solicitud" in doc or "proyecto_investigacion" in doc:
                documents[doc] = self._generate_main_application(project_data)
            elif "proyecto_tecnico" in doc:
                documents[doc] = self._generate_technical_project(project_data)
            elif "plan_seguridad" in doc:
                documents[doc] = self._generate_security_plan(project_data)
            else:
                documents[doc] = {"content": f"Documento: {doc}", "metadata": {"type": doc}}
        return documents

    def _generate_main_application(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera contenido de solicitud principal (texto para PDF)."""
        app_type = project_data.get("type", "INVESTIGACIÓN").upper()
        return {
            "content": f"""
SOLICITUD DE AUTORIZACIÓN PARA CULTIVO DE CANNABIS CON FINES DE {app_type}
(AEMPS — Ley 17/1967, RD 903/2025)

1. DATOS DEL SOLICITANTE
Nombre: {project_data.get('investigator', project_data.get('company_name', ''))}
Institución/Empresa: {project_data.get('institution', project_data.get('company_name', ''))}
NIF: {project_data.get('nif', '')}
Dirección: {project_data.get('address', '')}

2. DATOS DEL PROYECTO
Nombre del proyecto: {project_data.get('name', '')}
Objetivos: {project_data.get('objectives', '')}
Variedades de cannabis: {', '.join(project_data.get('strains', []))}
Cantidad solicitada: {project_data.get('quantity', 0)} kg
Duración: {project_data.get('duration', 0)} meses

3. COMPROMISOS
- Cumplimiento de la Ley 17/1967 y RD 903/2025.
- Implementación de plan de seguridad nivel 4.
- Destino exclusivo para {project_data.get('type', 'investigación')}.
- Registro detallado en sistema de trazabilidad (GaiaChain).

Fecha: {datetime.now().strftime('%d/%m/%Y')}
Firma: ________________________
""",
            "metadata": {"type": "main_application", "project_id": project_data.get("id", ""), "timestamp": datetime.now().isoformat()},
        }

    def _generate_security_plan(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera plan de seguridad (AEMPS / RD 903/2025)."""
        return {
            "content": f"""
PLAN DE SEGURIDAD PARA CULTIVO DE CANNABIS
Proyecto: {project_data.get('name', '')}
Ubicación: {project_data.get('cultivation_site', project_data.get('address', ''))}

1. MEDIDAS FÍSICAS (RD 903/2025)
- Cercado perimetral con sensores de movimiento.
- Cámaras de vigilancia 24/7.
- Acceso controlado por tarjetas RFID + biometría.
- Almacén de cosecha con puerta blindada y sistema anti-intrusión.

2. MEDIDAS DIGITALES
- Trazabilidad blockchain (GaiaChain) para registro de cada planta.
- Monitoreo con CASTUO Cloud 5.0 (Sentinel v5).
- Alertas automáticas a Fuerzas y Cuerpos de Seguridad del Estado en caso de intrusión.

3. PROTOCOLOS
- Inventario diario con verificación blockchain.
- Auditorías semanales por entidad certificadora.
- Plan de contingencia para robos o pérdidas.

Responsable de Seguridad: {project_data.get('security_responsible', '')}
Fecha: {datetime.now().strftime('%d/%m/%Y')}
""",
            "metadata": {"type": "security_plan", "project_id": project_data.get("id", ""), "timestamp": datetime.now().isoformat()},
        }

    def _generate_technical_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera proyecto técnico (producción médico)."""
        return {
            "content": f"Proyecto técnico: {project_data.get('name', '')}. Capacidad: {project_data.get('production_capacity', 0)} kg.",
            "metadata": {"type": "technical_project", "timestamp": datetime.now().isoformat()},
        }

    def submit_application(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """Envía solicitud a AEMPS (simulado; en producción usar API/ventanilla AEMPS)."""
        return {
            "status": "received",
            "application_id": f"AEMPS-{datetime.now().strftime('%Y%m%d')}-{hash(application.get('project_name', '')) % 10000}",
            "estimated_processing_time": "6-12 meses",
            "required_fees": 5000,  # €
            "next_steps": ["Pago de tasas", "Inspección inicial", "Revisión de documentación", "Aprobación final"],
        }
