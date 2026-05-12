# -*- coding: utf-8 -*-
"""Estándares y reglas de cumplimiento para mercados asiáticos (Japón, Corea, Tailandia)."""
from __future__ import annotations

from backend.models.international_compliance import (
    CountrySpecificRules,
    InternationalStandard,
    country_rules_db,
)

ASIA_STANDARDS: dict[str, InternationalStandard] = {
    "JP_JAS_Organic": InternationalStandard(
        standard_id="JP_JAS_2024",
        name="Japanese Agricultural Standard (JAS) Organic",
        country="JP",
        description="Certificación orgánica para productos agrícolas en Japón",
        requirements=[
            "No synthetic pesticides",
            "No chemical fertilizers",
            "Soil management plan",
            "Annual inspections",
        ],
        applicable_to=["microgreens"],
        validation_endpoint="https://www.maff.go.jp/jas/api/validate",
    ),
    "JP_GMP": InternationalStandard(
        standard_id="JP_GMP_2023",
        name="Japanese GMP for Cannabis",
        country="JP",
        description="Good Manufacturing Practice para cannabis medicinal en Japón",
        requirements=[
            "THC < 0.0%",
            "CBD only",
            "Kanpo medicine compliance",
            "Traceability from seed to patient",
        ],
        applicable_to=["cannabis"],
        validation_endpoint="https://www.pmda.go.jp/gmp/api",
    ),
    "KR_KFDA": InternationalStandard(
        standard_id="KR_KFDA_2024",
        name="Korea Food & Drug Administration Standards",
        country="KR",
        description="Normativas del KFDA para cannabis medicinal y alimentos",
        requirements=[
            "THC < 0.3%",
            "Heavy metal testing",
            "Microbiological analysis",
            "KFDA import permit",
        ],
        applicable_to=["cannabis", "microgreens"],
    ),
    "TH_ThaiFDA": InternationalStandard(
        standard_id="TH_ThaiFDA_2023",
        name="Thai FDA Standards for Cannabis",
        country="TH",
        description="Regulaciones de la Thai FDA para cannabis y productos derivados",
        requirements=[
            "THC < 0.2%",
            "Registered in Plaook Gan system",
            "GAP certification for cultivation",
            "Lab testing for contaminants",
        ],
        applicable_to=["cannabis"],
    ),
    "TH_Organic": InternationalStandard(
        standard_id="TH_Organic_2024",
        name="Thai Organic Standard",
        country="TH",
        description="Certificación orgánica para productos agrícolas en Tailandia",
        requirements=[
            "No synthetic inputs",
            "Soil and water conservation",
            "Biodiversity preservation",
            "Annual organic inspections",
        ],
        applicable_to=["microgreens"],
    ),
}

# Registrar reglas por país para Asia
country_rules_db.update({
    "JP": CountrySpecificRules(
        country_code="JP",
        language="ja",
        currency="JPY",
        time_zone="Asia/Tokyo",
        cannabis_standards=[ASIA_STANDARDS["JP_GMP"]],
        microgreens_standards=[ASIA_STANDARDS["JP_JAS_Organic"]],
        tax_rules={"consumption_tax": 10.0, "import_tax": 5.0},
        import_restrictions=[
            "Phytosanitary certificate required",
            "Radiation inspection for food products",
            "Pre-registration with MAFF",
        ],
        labeling_requirements=[
            "Japanese language labels",
            "Allergen information",
            "Nutritional facts (per 100g)",
            "Expiration date in YYYY/MM/DD format",
        ],
    ),
    "KR": CountrySpecificRules(
        country_code="KR",
        language="ko",
        currency="KRW",
        time_zone="Asia/Seoul",
        cannabis_standards=[ASIA_STANDARDS["KR_KFDA"]],
        microgreens_standards=[ASIA_STANDARDS["KR_KFDA"]],
        tax_rules={"vat": 10.0, "special_tax": 30.0},
        import_restrictions=[
            "KFDA import permit required",
            "Quarantine inspection",
            "Fumigation certificate",
        ],
        labeling_requirements=[
            "Korean language labels",
            "THC/CBD content (if applicable)",
            "Manufacturer and importer details",
            "Storage instructions",
        ],
    ),
    "TH": CountrySpecificRules(
        country_code="TH",
        language="th",
        currency="THB",
        time_zone="Asia/Bangkok",
        cannabis_standards=[ASIA_STANDARDS["TH_ThaiFDA"]],
        microgreens_standards=[ASIA_STANDARDS["TH_Organic"]],
        tax_rules={"vat": 7.0, "excise_tax": 0.0},
        import_restrictions=[
            "Phytosanitary certificate",
            "Fumigation treatment",
            "Pre-shipment inspection",
        ],
        labeling_requirements=[
            "Thai language labels",
            "Organic certification logo",
            "Cultivation date and harvest date",
            "Storage temperature requirements",
        ],
    ),
})
