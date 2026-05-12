# -*- coding: utf-8 -*-
"""
Generador de documentación AEMPS (RD 903/2025): solicitud de autorización, plan de seguridad, trazabilidad.
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = __import__("logging").getLogger(__name__)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class AEMPSDocumentGenerator:
    """
    Genera documentación para cumplimiento AEMPS (RD 903/2025): solicitud de autorización,
    plan de seguridad, protocolos de trazabilidad. Registro en GaiaChain.
    """

    def __init__(self, gaiachain_client: Optional[Any] = None, output_dir: str = "./aemps_docs") -> None:
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = self._init_styles() if HAS_REPORTLAB else {}

    def _init_styles(self) -> Any:
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Title", fontSize=18, leading=22, alignment=1, spaceAfter=20))
        styles.add(ParagraphStyle(name="Heading1", fontSize=14, leading=18, spaceBefore=12, spaceAfter=12))
        styles.add(ParagraphStyle(name="Heading2", fontSize=12, leading=16, spaceBefore=8, spaceAfter=8))
        styles.add(ParagraphStyle(name="BodyText", fontSize=10, leading=12, spaceAfter=6))
        return styles

    def generate_application(self, project_data: Dict[str, Any]) -> str:
        """Genera documento de solicitud de autorización AEMPS. Devuelve ruta del archivo."""
        project_id = project_data.get("project_id", "CASTUA-2026")
        filename = f"AEMPS_Solicitud_{project_id}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        if HAS_REPORTLAB:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []

            story.append(Paragraph(
                "SOLICITUD DE AUTORIZACIÓN PARA CULTIVO DE CANNABIS CON FINES MÉDICOS",
                self.styles["Title"],
            ))
            story.append(Paragraph(f"Proyecto: {project_data.get('project_name', '')}", self.styles["Heading1"]))
            story.append(Paragraph(f"ID: {project_id}", self.styles["Heading1"]))
            story.append(Spacer(1, 0.25 * inch))

            applicant = project_data.get("applicant", {})
            story.append(Paragraph("1. DATOS DEL SOLICITANTE", self.styles["Heading1"]))
            solicitante_data = [
                ["Nombre/Razón Social", applicant.get("name", "")],
                ["NIF/CIF", applicant.get("tax_id", "")],
                ["Dirección", applicant.get("address", "")],
                ["Teléfono", applicant.get("phone", "")],
                ["Email", applicant.get("email", "")],
                ["Representante Legal", applicant.get("legal_representative", "")],
            ]
            t1 = Table(solicitante_data, colWidths=[2.5 * inch, 3 * inch])
            t1.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a6fa5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t1)
            story.append(Spacer(1, 0.25 * inch))

            story.append(Paragraph("2. DATOS DEL PROYECTO", self.styles["Heading1"]))
            proyecto_data = [
                ["Nombre del Proyecto", project_data.get("project_name", "")],
                ["Ubicación", project_data.get("location", "")],
                ["Variedades", ", ".join(project_data.get("cannabis_strains", []))],
                ["Capacidad (kg/año)", str(project_data.get("production_capacity", 0))],
                ["Fines", "Medicinales (RD 903/2025)"],
                ["Duración (meses)", str(project_data.get("duration_months", 0))],
                ["Fecha de Inicio", project_data.get("start_date", "")],
            ]
            t2 = Table(proyecto_data, colWidths=[2.5 * inch, 3 * inch])
            t2.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a6fa5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t2)
            story.append(Spacer(1, 0.25 * inch))

            story.append(Paragraph("3. PLAN DE SEGURIDAD", self.styles["Heading1"]))
            security_plan = [
                ["Medida", "Descripción", "Cumplimiento"],
                ["Cercado perimetral", "Malla 2.5m, sensores vibración", "EN 10223-3"],
                ["Videovigilancia", "Cámaras 360° Axis Q6075-E", "ISO 22301"],
                ["Control de acceso", "MFA YubiKey + huella + HSM FIPS 140-2", "FIPS 140-2"],
                ["Anti-drones", "Dedrone + jammer selectivo", "ETSI EN 303 413"],
                ["Trazabilidad", "GaiaChain HoneyBadgerBFT + ZKP", "eIDAS"],
                ["Almacenamiento", "HSM Thales Luna 7, backups WORM", "ISO 27040"],
                ["Respuesta incidentes", "SOC TheHive + Velociraptor", "ISO 27035"],
            ]
            t3 = Table(security_plan, colWidths=[1.5 * inch, 3 * inch, 1 * inch])
            t3.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a6fa5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t3)
            story.append(Spacer(1, 0.25 * inch))

            story.append(Paragraph("4. COMPROMISOS", self.styles["Heading1"]))
            for line in [
                "Cumplimiento RD 903/2025 y Ley 17/1967.",
                "Plan de seguridad nivel 4, auditoría trimestral.",
                "Trazabilidad completa en GaiaChain.",
                "Colaboración con Fuerzas y Cuerpos de Seguridad.",
            ]:
                story.append(Paragraph(f"• {line}", self.styles["BodyText"]))

            story.append(Paragraph("5. FIRMA", self.styles["Heading1"]))
            story.append(Paragraph(
                f"Lugar y fecha: {datetime.now().strftime('%d/%m/%Y')}. "
                f"Nombre y cargo: {applicant.get('legal_representative', '')}.",
                self.styles["BodyText"],
            ))
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph(
                "Documento generado por CASTUO-SYSTEM™. Registros inmutables en GaiaChain.",
                self.styles["BodyText"],
            ))
            doc.build(story)
        else:
            with open(filepath.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
                f.write(f"SOLICITUD AEMPS - Proyecto: {project_data.get('project_name')}\n")
                f.write(f"ID: {project_id}\n")
                f.write(f"Ubicación: {project_data.get('location')}\n")
                f.write(f"Variedades: {project_data.get('cannabis_strains')}\n")
            filename = filename.replace(".pdf", ".txt")
            filepath = os.path.join(self.output_dir, filename)

        if self.gaiachain:
            self.gaiachain.log_compliance_document({
                "document_type": "aemps_application",
                "project_id": project_id,
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "cannabis_strains": project_data.get("cannabis_strains", []),
                    "production_capacity": project_data.get("production_capacity"),
                    "location": project_data.get("location"),
                },
            })
        return filepath
