# -*- coding: utf-8 -*-
"""Estándares y reglas de cumplimiento para Canadá (Health Canada, GPP, SFCR)."""
from __future__ import annotations

from backend.models.international_compliance import (
    CountrySpecificRules,
    InternationalStandard,
    country_rules_db,
)

CANADA_STANDARDS: dict[str, InternationalStandard] = {
    "CA_HealthCanada": InternationalStandard(
        standard_id="CA_HC_2023",
        name="Health Canada Cannabis Regulations",
        country="CA",
        description="Regulaciones de Health Canada para cannabis medicinal y recreativo",
        requirements=[
            "Health Canada license (cultivation/processing/sale)",
            "THC < 0.3% for CBD products",
            "Seed-to-sale traceability",
            "Child-resistant packaging",
            "Contaminant testing (pesticides, heavy metals, mold)",
        ],
        applicable_to=["cannabis"],
        validation_endpoint="https://api.canada.ca/cannabis/validate",
    ),
    "CA_GPP": InternationalStandard(
        standard_id="CA_GPP_2024",
        name="Good Production Practices (GPP) for Cannabis",
        country="CA",
        description="Buenas prácticas de producción para cannabis en Canadá",
        requirements=[
            "Standard operating procedures (SOPs)",
            "Quality assurance program",
            "Sanitation and hygiene protocols",
            "Record keeping for 2 years",
            "Recall procedures",
        ],
        applicable_to=["cannabis"],
    ),
    "CA_Organic": InternationalStandard(
        standard_id="CA_Organic_2024",
        name="Canada Organic Regime",
        country="CA",
        description="Certificación orgánica para productos agrícolas en Canadá",
        requirements=[
            "No synthetic pesticides or fertilizers",
            "Soil building and crop rotation practices",
            "Buffer zones to prevent contamination",
            "Annual inspections by certified bodies",
        ],
        applicable_to=["microgreens", "cannabis"],
    ),
    "CA_SFCR": InternationalStandard(
        standard_id="CA_SFCR_2023",
        name="Safe Food for Canadians Regulations",
        country="CA",
        description="Normativas de seguridad alimentaria para microgreens",
        requirements=[
            "Preventive control plan (PCP)",
            "Microbiological testing",
            "Traceability records",
            "Sanitation and hygiene programs",
        ],
        applicable_to=["microgreens"],
    ),
}

# Registrar reglas para Canadá
country_rules_db["CA"] = CountrySpecificRules(
    country_code="CA",
    language="en",
    currency="CAD",
    time_zone="America/Toronto",
    cannabis_standards=[CANADA_STANDARDS["CA_HealthCanada"], CANADA_STANDARDS["CA_GPP"]],
    microgreens_standards=[CANADA_STANDARDS["CA_Organic"], CANADA_STANDARDS["CA_SFCR"]],
    tax_rules={
        "gst": 5.0,
        "pst": 0.0,
        "excise_tax": 0.10,
    },
    import_restrictions=[
        "Health Canada import permit required for cannabis",
        "Phytosanitary certificate required for microgreens",
        "Customs broker recommended for commercial shipments",
    ],
    labeling_requirements=[
        "Bilingual labels (English and French)",
        "THC/CBD content clearly stated",
        "Health warnings for cannabis products",
        "Allergen information for microgreens",
        "Net weight in metric units",
    ],
)
