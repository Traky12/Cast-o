{
    "name": "CASTUO Alert - Alertas Predictivas",
    "version": "1.0.0",
    "summary": "Reglas de alertas y notificaciones Slack/Telegram",
    "description": "Reglas por umbral (stock, energía, demanda), ejecución de acciones y notificaciones.",
    "category": "Inventory",
    "depends": ["base", "castu_materials"],
    "data": [
        "security/ir.model.access.csv",
        "views/alert_rule_views.xml",
        "views/alert_views.xml",
    ],
    "installable": True,
    "application": False,
}
