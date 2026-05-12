{
    "name": "CASTUO Demand - Predicción de Demanda IA",
    "version": "1.0.0",
    "summary": "Predicción de demanda de materiales con IA y alertas de stock",
    "description": "Genera predicciones de demanda (Mistral/fallback), alertas por stock insuficiente e integración con API /ia/predict_demand.",
    "category": "Inventory",
    "depends": ["base", "castu_materials"],
    "data": [
        "security/ir.model.access.csv",
        "data/server_actions.xml",
        "views/demand_prediction_views.xml",
        "views/demand_alert_views.xml",
    ],
    "installable": True,
    "application": False,
}
