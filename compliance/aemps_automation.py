# -*- coding: utf-8 -*-
"""
Automatización AEMPS (RD 903/2025): documentación técnica, seguridad, trazabilidad, certificaciones.
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
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class AEMPSAutomation:
    """
    Genera documentación completa para AEMPS: solicitud, plan de seguridad,
    trazabilidad, cumplimiento normativo, certificaciones. Registro en GaiaChain.
    """

    def __init__(self, gaiachain_client: Optional[Any] = None, output_dir: str = "./aemps_docs") -> None:
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = self._init_styles() if HAS_REPORTLAB else {}
        self.aemps_requirements = self._load_aemps_requirements()

    def _init_styles(self) -> Dict[str, Any]:
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Title", fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=20, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name="Subtitle", fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=15, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name="Heading1", fontSize=14, leading=18, spaceBefore=12, spaceAfter=12, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name="Heading2", fontSize=12, leading=16, spaceBefore=8, spaceAfter=8, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name="BodyText", fontSize=10, leading=12, spaceAfter=6))
        styles.add(ParagraphStyle(name="Footer", fontSize=8, leading=10, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="Code", fontSize=9, leading=11, backColor=colors.HexColor("#f8f9fa")))
        return styles

    def _load_aemps_requirements(self) -> Dict[str, List[str]]:
        return {
            "general": [
                "Solicitud de autorización para cultivo, producción y distribución",
                "Plan de seguridad detallado",
                "Protocolos de trazabilidad desde semilla hasta producto final",
                "Certificación GMP",
                "Sistema de gestión de calidad (ISO 9001)",
            ],
            "security": [
                "Videovigilancia 24/7, grabación mínima 30 días",
                "Control de acceso biométrico",
                "Alarma conectada a fuerzas de seguridad",
                "Protección física (puertas blindadas, cercado)",
                "Auditorías de seguridad trimestrales",
            ],
            "traceability": [
                "Registro inmutable (blockchain)",
                "Identificación única por planta/lote",
                "Monitoreo continuo IoT",
                "Cadena de custodia en transporte",
            ],
        }

    def _table_style_header(self) -> List[tuple]:
        return [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]

    def generate_application_document(self, project_data: Dict[str, Any]) -> str:
        """Genera el documento de solicitud completo para AEMPS. Devuelve ruta del archivo."""
        project_id = project_data.get("project_id", "CASTUA-2026")
        filename = f"AEMPS_Solicitud_{project_id}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        if not HAS_REPORTLAB:
            with open(filepath.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
                f.write(f"AEMPS - Solicitud de autorización\nProyecto: {project_data.get('project_name')}\nID: {project_id}\n")
                f.write(f"Ubicación: {project_data.get('location')}\nVariedades: {project_data.get('cannabis_strains')}\n")
            filepath = filepath.replace(".pdf", ".txt")
            filename = os.path.basename(filepath)
            if self.gaiachain:
                self.gaiachain.log_compliance_document({
                    "document_type": "aemps_application",
                    "project_id": project_id,
                    "filename": filename,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": project_data,
                })
            return filepath

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        applicant = project_data.get("applicant", {})

        story.append(Paragraph("AGENCIA ESPAÑOLA DE MEDICAMENTOS Y PRODUCTOS SANITARIOS (AEMPS)", self.styles["Title"]))
        story.append(Paragraph("SOLICITUD DE AUTORIZACIÓN PARA CULTIVO DE CANNABIS CON FINES MÉDICOS", self.styles["Subtitle"]))
        story.append(Paragraph(f"Proyecto: {project_data.get('project_name', '')}", self.styles["Heading1"]))
        story.append(Paragraph(f"ID: {project_id}", self.styles["Heading1"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("1. DATOS DEL SOLICITANTE", self.styles["Heading1"]))
        applicant_data = [
            ["Nombre/Razón Social", applicant.get("name", "")],
            ["NIF/CIF", applicant.get("tax_id", "")],
            ["Dirección", applicant.get("address", "")],
            ["Teléfono", applicant.get("phone", "")],
            ["Email", applicant.get("email", "")],
            ["Representante Legal", applicant.get("legal_representative", "")],
            ["Nº Registro", applicant.get("registry_number", "N/A")],
        ]
        t1 = Table(applicant_data, colWidths=[2 * inch, 3.5 * inch])
        t1.setStyle(TableStyle(self._table_style_header()))
        story.append(t1)
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("2. DATOS DEL PROYECTO", self.styles["Heading1"]))
        project_rows = [
            ["Nombre del Proyecto", project_data.get("project_name", "")],
            ["ID", project_id],
            ["Ubicación", project_data.get("location", "")],
            ["Variedades", ", ".join(project_data.get("cannabis_strains", []))],
            ["Capacidad (kg/año)", str(project_data.get("production_capacity", 0))],
            ["Fines", "Medicinales (RD 903/2025)"],
            ["Duración (meses)", str(project_data.get("duration_months", 0))],
            ["Fecha Inicio", project_data.get("start_date", "")],
            ["Fecha Fin", project_data.get("end_date", "")],
            ["Inversión Total", f"€{project_data.get('total_investment', 0):,}"],
            ["Empleos", str(project_data.get("jobs_created", 0))],
        ]
        t2 = Table(project_rows, colWidths=[2 * inch, 3.5 * inch])
        t2.setStyle(TableStyle(self._table_style_header()))
        story.append(t2)
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("3. PLAN DE SEGURIDAD", self.styles["Heading1"]))
        story.append(Paragraph(
            "Plan de seguridad nivel 4 conforme a RD 903/2025. Sistemas certificados y auditados trimestralmente.",
            self.styles["BodyText"],
        ))
        security_measures = [
            ["Área", "Medida", "Normativa"],
            ["Perímetro", "Cercado 2.5m, sensores vibración cada 50m", "EN 10223-3"],
            ["Acceso", "MFA YubiKey + huella + HSM FIPS 140-2", "FIPS 140-2"],
            ["Vigilancia", "Cámaras 360° Axis Q6075-E, IA", "ISO 22301"],
            ["Drones", "Dedrone + jammer selectivo", "ETSI EN 303 413"],
            ["Red", "Cilium/eBPF, Palo Alto", "ISO 27033"],
            ["Datos", "Cifrado homomórfico, HSM Thales Luna 7", "ISO 27040"],
            ["Blockchain", "GaiaChain HoneyBadgerBFT + Dilithium", "eIDAS"],
        ]
        t3 = Table(security_measures, colWidths=[1 * inch, 3 * inch, 1.5 * inch])
        t3.setStyle(TableStyle(self._table_style_header() + [("ALIGN", (2, 1), (2, -1), "CENTER")]))
        story.append(t3)
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("4. SISTEMA DE TRAZABILIDAD", self.styles["Heading1"]))
        story.append(Paragraph(
            "Trazabilidad completa en GaiaChain (blockchain con consenso HoneyBadgerBFT y firmas Dilithium).",
            self.styles["BodyText"],
        ))
        traceability_points = [
            ["Punto", "Datos", "Tecnología"],
            ["Siembra", "ID semilla, variedad, fecha, GPS", "IoT + GaiaChain"],
            ["Cosecha", "Peso, fecha, personal", "Balanzas + MFA"],
            ["Procesado", "Método, peso, cannabinoides", "GMP + QA"],
            ["Transporte", "Ruta, temperatura, custodia", "GPS + IoT"],
        ]
        t4 = Table(traceability_points, colWidths=[1.2 * inch, 2.8 * inch, 1.5 * inch])
        t4.setStyle(TableStyle(self._table_style_header()))
        story.append(t4)
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("5. CUMPLIMIENTO NORMATIVO", self.styles["Heading1"]))
        for item in [
            "RD 903/2025 (cannabis uso medicinal)",
            "Ley 17/1967",
            "GMP productos farmacéuticos",
            "GDPR",
        ]:
            story.append(Paragraph(f"• {item}", self.styles["BodyText"]))
        story.append(Spacer(1, 0.1 * inch))
        certifications = [
            ["Certificación", "Ámbito", "Entidad", "Vigencia"],
            ["ISO 9001:2015", "Calidad", "AENOR", "2023-2026"],
            ["ISO 27001:2022", "Seguridad Información", "TÜV SÜD", "2024-2027"],
            ["ISO 14001:2015", "Ambiental", "Bureau Veritas", "2023-2026"],
            ["GMP", "Buenas Prácticas Fabricación", "AEMPS", "2024-2026"],
            ["FIPS 140-2 Level 4", "Módulos Criptográficos", "NIST", "2025-2030"],
        ]
        t5 = Table(certifications, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1 * inch])
        t5.setStyle(TableStyle(self._table_style_header()))
        story.append(t5)
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("6. COMPROMISOS Y FIRMA", self.styles["Heading1"]))
        story.append(Paragraph("Cumplimiento RD 903/2025 y Ley 17/1967. Trazabilidad en GaiaChain. Colaboración con Fuerzas y Cuerpos de Seguridad.", self.styles["BodyText"]))
        story.append(Paragraph(f"Lugar y fecha: {datetime.now().strftime('%d/%m/%Y')}. Representante: {applicant.get('legal_representative', '')}.", self.styles["BodyText"]))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("Documento generado por CASTUO-SYSTEM™. Registros inmutables en GaiaChain.", self.styles["Footer"]))

        doc.build(story)

        if self.gaiachain:
            self.gaiachain.log_compliance_document({
                "document_type": "aemps_application",
                "project_id": project_id,
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "metadata": {"cannabis_strains": project_data.get("cannabis_strains"), "production_capacity": project_data.get("production_capacity"), "location": project_data.get("location")},
            })
        return filepath
