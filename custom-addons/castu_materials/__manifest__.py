{
    "name": "CASTUO Materials - Gestión de Materiales Compuestos",
    "version": "1.0.0",
    "summary": "Producción, ventas y certificación de materiales ecológicos",
    "description": """
        Producción, inventario y ventas de materiales compuestos ecológicos,
        con trazabilidad blockchain y certificación. Integración con extrusora vía MQTT.
    """,
    "category": "Manufacturing",
    "depends": ["base", "sale", "stock", "account"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "views/material_views.xml",
        "views/production_views.xml",
        "views/sale_views.xml",
        "views/certification_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
