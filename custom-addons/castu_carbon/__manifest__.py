{
    "name": "CASTUO Carbon - Créditos de Carbono",
    "version": "1.0.0",
    "summary": "Créditos de carbono por producción de materiales ecológicos",
    "description": "Cálculo de ahorro CO₂, registro en blockchain y reportes de créditos.",
    "category": "Sustainability",
    "depends": ["base", "castu_materials"],
    "data": [
        "security/ir.model.access.csv",
        "views/carbon_credit_views.xml",
        "views/carbon_report_views.xml",
    ],
    "installable": True,
    "application": False,
}
