{
    "name": "CASTUO Invoicing - Facturae SII",
    "version": "1.0.0",
    "summary": "Facturación electrónica Facturae 3.2.1 e integración con Agencia Tributaria (SII)",
    "description": """
        Facturas de materiales compuestos con generación de XML Facturae 3.2.1,
        envío al SII y registro en blockchain BioCoin Castúo.
    """,
    "category": "Accounting",
    "depends": ["base", "account", "mail", "castu_materials"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/invoice_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
