"""Sabionda IA Connector for crop prediction and optimization."""
import importlib
import logging
from typing import Any, Dict, Protocol

logger = logging.getLogger(__name__)


class SabiondaClient:
    """Mock Sabionda client for development & testing."""
    
    def __init__(self, api_key: str):
        """Initialize Sabionda client."""
        self.api_key = api_key
    
    def analyze_crop_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze crop data and return predictions."""
        # This is a placeholder for the actual SDK
        raise NotImplementedError(
            "Install sabionda-sdk: pip install sabionda-sdk"
        )


class SupportsSabiondaAnalysis(Protocol):
    def analyze_crop_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ...


class SabiondaConnector:
    """Connector for Sabionda IA API for crop yield prediction and optimization."""

    def __init__(self, api_key: str):
        """
        Initialize Sabionda connector.

        Args:
            api_key: Sabionda API key (preferably from environment)
        """
        self.client: SupportsSabiondaAnalysis

        # Import here to make it optional
        try:
            module = importlib.import_module("sabionda_sdk")
            RealSabiondaClient = getattr(module, "SabiondaClient")
            self.client = RealSabiondaClient(api_key=api_key)
        except ImportError:
            logger.warning(
                "sabionda-sdk not installed, using mock client. "
                "Install with: pip install sabionda-sdk"
            )
            self.client = SabiondaClient(api_key=api_key)
        
        self.api_key = api_key

    def predict_crop_yield(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict crop yield using Sabionda IA machine learning models.

        Args:
            data: Dictionary containing agricultural data:
                - humidity: Soil/air humidity percentage
                - temperature: Temperature in Celsius
                - soil_ph: Soil pH level
                - historical_yield: List of previous yields (kg/ha)
                - crop: Crop type (optional)
                - region: Geographic region (optional)
                - planting_date: Date of planting (optional)

        Returns:
            Prediction dictionary with:
                - predicted_yield: Predicted harvest in kg/ha
                - confidence: Confidence level (0-1)
                - recommendation: Text recommendation
                - risk_factors: List of identified risks
                - optimal_harvest_date: Recommended harvest date

        Raises:
            Exception: If API call fails or data is invalid
        """
        if not self._validate_data(data):
            raise ValueError("Missing required crop data fields")

        logger.info("Predicting crop yield with Sabionda: %s", data.get("crop", "unknown"))

        try:
            result = self.client.analyze_crop_data(data)
            return self._enrich_prediction(result, data)
        except AttributeError:
            # If using mock client
            logger.error(
                "Sabionda SDK not properly installed. "
                "Install with: pip install sabionda-sdk"
            )
            raise

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate that required fields are present."""
        required_fields = ["humidity", "temperature", "soil_ph", "historical_yield"]
        return all(field in data for field in required_fields)

    def _enrich_prediction(
        self, prediction: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich prediction with additional context.

        Args:
            prediction: Raw prediction from Sabionda
            data: Original input data

        Returns:
            Enhanced prediction with metadata
        """
        enriched = prediction.copy()
        
        # Add metadata
        enriched["crop"] = data.get("crop", "unknown")
        enriched["region"] = data.get("region", "unknown")
        enriched["input_conditions"] = {
            "humidity": data["humidity"],
            "temperature": data["temperature"],
            "soil_ph": data["soil_ph"]
        }
        
        # Calculate variance from historical
        if data.get("historical_yield"):
            avg_historical = sum(data["historical_yield"]) / len(data["historical_yield"])
            variance = (
                (enriched.get("predicted_yield", 0) - avg_historical) / avg_historical * 100
                if avg_historical > 0 else 0
            )
            enriched["yield_variance_percent"] = round(variance, 2)
        
        return enriched

    def get_risk_assessment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get risk assessment for given conditions.

        Args:
            data: Agricultural data

        Returns:
            Risk assessment with critical factors
        """
        prediction = self.predict_crop_yield(data)
        
        risks: list[str] = []
        
        # Analyze conditions for risks
        if data["humidity"] < 30:
            risks.append("Déficit de humedad severo")
        elif data["humidity"] > 85:
            risks.append("Exceso de humedad - riesgo de plagas/enfermedades")
        
        if data["temperature"] < 10 or data["temperature"] > 35:
            risks.append("Temperatura fuera de rango óptimo")
        
        if data["soil_ph"] < 5.5 or data["soil_ph"] > 8.5:
            risks.append("pH del suelo desfavorable")
        
        return {
            "predicted_yield": prediction.get("predicted_yield"),
            "risk_factors": risks,
            "recommendation": self._build_recommendation(risks, prediction),
            "severity": len(risks)
        }

    def _build_recommendation(
        self, risks: list[str], prediction: Dict[str, Any]
    ) -> str:
        """Build text recommendation based on risks."""
        if not risks:
            return "Condiciones óptimas. Mantener monitoreo regular."
        
        if len(risks) > 2:
            return (
                "Múltiples riesgos identificados. Implementar acción correctiva "
                "inmediata y aumentar frecuencia de monitoreo."
            )
        
        return f"Se han identificado riesgos. Primero, {risks[0].lower()}. Recomendar aplicar medidas preventivas."

    def get_fertilizer_recommendation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get fertilizer recommendations based on crop data.

        Args:
            data: Agricultural data

        Returns:
            Fertilizer recommendations
        """
        prediction = self.predict_crop_yield(data)
        
        return {
            "crop": data.get("crop"),
            "ph_based": self._recommend_by_ph(data["soil_ph"]),
            "yield_based": self._recommend_by_yield(prediction.get("predicted_yield", 0)),
            "schedule": self._get_fertilizer_schedule(data)
        }

    def _recommend_by_ph(self, ph: float) -> str:
        """Recommend fertilizer based on soil pH."""
        if ph < 6.0:
            return "Aplicar cal para elevar pH. Usar fertilizantes amoniácales."
        elif ph > 7.5:
            return "Suelo alcalino. Usar fertilizantes con azufre. Micronutrientes."
        else:
            return "pH óptimo. Fertilizantes estándar recomendados."

    def _recommend_by_yield(self, yield_val: float) -> str:
        """Recommend fertilizer intensity based on expected yield."""
        if yield_val > 2000:
            return "Producción alta. Aumentar dosis de fertilizante."
        elif yield_val < 1000:
            return "Producción baja. Diagnosticar deficiencias nutricionales."
        else:
            return "Dosis estándar de fertilizante recomendada."

    def _get_fertilizer_schedule(self, data: Dict[str, Any]) -> list[Dict[str, str]]:
        """Get fertilizer application schedule."""
        return [
            {"stage": "Plantación", "npk": "10-52-10", "dosis": "500 kg/ha"},
            {"stage": "Desarrollo vegetativo", "npk": "20-20-20", "dosis": "300 kg/ha"},
            {"stage": "Floración", "npk": "10-30-20", "dosis": "200 kg/ha"},
            {"stage": "Llenado de grano", "npk": "5-10-40", "dosis": "150 kg/ha"}
        ]
