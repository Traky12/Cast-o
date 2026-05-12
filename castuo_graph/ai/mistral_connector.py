"""Mistral AI Connector for agricultural data analysis."""
import requests
from typing import Dict, Any
import logging
import time

logger = logging.getLogger(__name__)


class MistralConnector:
    """Connector for Mistral AI API to analyze agricultural data."""

    def __init__(self, api_key: str):
        """
        Initialize Mistral connector.

        Args:
            api_key: Mistral API key (preferably from environment)
        """
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1/chat"
        self.model = "mistral-small"
        self.request_timeout = 30
        self.max_retries = 2
        self.retry_backoff_seconds = 0.4

    def analyze_agricultural_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send agricultural data to Mistral AI for analysis.

        Args:
            data: Dictionary containing agricultural measurements:
                - humidity: Soil/air humidity percentage
                - temperature: Temperature in Celsius
                - soil_ph: Soil pH level
                - crop: Crop type (optional)
                - location: Field location (optional)
                - timestamp: ISO format timestamp (optional)

        Returns:
            API response with analysis and recommendations

        Raises:
            requests.RequestException: If API call fails
            ValueError: If required fields are missing
        """
        if not self._validate_data(data):
            raise ValueError("Missing required agricultural data fields")

        prompt = self._build_prompt(data)
        headers = self._build_headers()
        payload = self._build_payload(prompt)

        logger.info("Sending agricultural data to Mistral AI: %s", data.get("crop", "unknown"))

        return self._post_with_retry(headers=headers, payload=payload)

    def _post_with_retry(self, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST con reintento para fallos transitorios de red o 5xx."""
        last_error: Exception | None = None
        total_attempts = self.max_retries + 1

        for attempt in range(1, total_attempts + 1):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.request_timeout,
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= total_attempts:
                    raise

                # Reintenta en errores típicamente transitorios.
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                if status_code is not None and status_code < 500 and status_code not in (408, 429):
                    raise

                sleep_for = self.retry_backoff_seconds * attempt
                logger.warning(
                    "Mistral request failed (attempt %s/%s): %s. Retrying in %.1fs",
                    attempt,
                    total_attempts,
                    exc,
                    sleep_for,
                )
                time.sleep(sleep_for)

        # Salvaguarda defensiva (no debería alcanzarse por el raise anterior).
        if last_error is not None:
            raise last_error
        raise RuntimeError("Unexpected error during Mistral API request")

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate that required fields are present."""
        required_fields = ["humidity", "temperature", "soil_ph"]
        return all(field in data for field in required_fields)

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """Build analysis prompt from agricultural data."""
        crop = data.get("crop", "desconocido")
        location = data.get("location", "sin especificar")
        
        prompt = f"""
        Realiza un análisis técnico detallado de los siguientes datos agrícolas:
        
        Ubicación: {location}
        Cultivo: {crop}
        Humedad del suelo: {data['humidity']}%
        Temperatura: {data['temperature']}°C
        pH del suelo: {data['soil_ph']}
        Fecha/Hora: {data.get('timestamp', 'sin especificar')}
        
        Por favor proporciona:
        1. Diagnóstico del estado actual del cultivo
        2. Riesgos identificados
        3. Recomendaciones de acción inmediata
        4. Predicción de rendimiento
        5. Necesidades de riego/nutrientes
        """
        return prompt

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with authorization."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _build_payload(self, prompt: str) -> Dict[str, Any]:
        """Build API request payload."""
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }

    def get_available_models(self) -> list[str]:
        """Get list of available Mistral models."""
        return ["mistral-tiny", "mistral-small", "mistral-medium"]

    def set_model(self, model: str) -> None:
        """Set which Mistral model to use."""
        available = self.get_available_models()
        if model in available:
            self.model = model
            logger.info(f"Switched to Mistral model: {model}")
        else:
            raise ValueError(f"Model {model} not available. Choose from {available}")
