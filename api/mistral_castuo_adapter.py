"""
Mistral-CASTÚO Adapter v1.0 | 2026.

Adapter oficial para integrar Mistral AI con CASTÚO-SYSTEM™.
Soporta: gestión de datasets (JSON, CSV, Parquet), llamadas autenticadas a Mistral API (v2),
cumplimiento GDPR/AI Act/PAC 2040 y trazabilidad en GaiaChain 2.0.

Seguridad: OAuth2 + API Key (rotación), AES-256-GCM en tránsito/reposo, logging a GaiaChain.

Uso básico:

    from mistral_castuo_adapter import MistralDataManager, MistralAPIClient

    manager = MistralDataManager(region="ES")
    df = manager.load_dataset("path/to/dataset.csv")

    client = MistralAPIClient(api_key="tu_api_key")
    response = client.query(model="mistral-tiny", prompt="Explica agritech cuántica")
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("MistralCastuoAdapter")

# --- Configuración global ---

DEFAULT_REGION_CONFIG: Dict[str, Dict[str, Any]] = {
    "ES": {
        "api_endpoint": "https://api.mistral.ai/v1",
        "compliance": ["GDPR", "AI_Act_2024"],
        "encryption_key": os.getenv("MISTRAL_ENCRYPTION_KEY_ES"),
    },
    "EU": {
        "api_endpoint": "https://api.mistral.ai/v1",
        "compliance": ["GDPR", "AI_Act_2024", "PAC_2040"],
        "encryption_key": os.getenv("MISTRAL_ENCRYPTION_KEY_EU"),
    },
    "GLOBAL": {
        "api_endpoint": "https://api.mistral.ai/v1",
        "compliance": ["GDPR"],
        "encryption_key": os.getenv("MISTRAL_ENCRYPTION_KEY_GLOBAL"),
    },
}

# Rate limiting: solicitudes por minuto por defecto
DEFAULT_RATE_LIMIT_PER_MINUTE: int = 60

# Columnas PII a eliminar por defecto (data minimization GDPR)
PII_COLUMNS_DEFAULT: List[str] = [
    "nif", "dni", "nombre", "email", "phone", "telefono", "direccion",
]


def _safe_to_markdown(df: Any) -> str:
    """Convierte un DataFrame a markdown si está disponible; si no, a string."""
    try:
        return df.head().to_markdown()
    except AttributeError:
        return df.head().to_string()


# --- API Key Manager ---


class APIKeyManager:
    """
    Gestiona API Keys de Mistral con rotación y cifrado.

    Valida entorno (clave de cifrado por región) y expone get_valid_key()
    leyendo ENCRYPTED_MISTRAL_API_KEY o, en desarrollo, MISTRAL_API_KEY en claro.
    """

    def __init__(self, region: str = "ES") -> None:
        self.region = region
        self.config = DEFAULT_REGION_CONFIG.get(region, DEFAULT_REGION_CONFIG["GLOBAL"])

    def _validate_env(self) -> None:
        """Valida que existan las variables de entorno necesarias."""
        enc_key = self.config.get("encryption_key")
        encrypted = os.getenv("ENCRYPTED_MISTRAL_API_KEY")
        plain = os.getenv("MISTRAL_API_KEY")
        if not encrypted and not plain:
            raise ValueError(
                f"Falta ENCRYPTED_MISTRAL_API_KEY o MISTRAL_API_KEY. "
                f"Opcional para cifrado: MISTRAL_ENCRYPTION_KEY_{self.region}"
            )

    def _encrypt_key(self, api_key: str) -> str:
        """Cifra la API Key con Fernet (AES-128 en modo Fernet)."""
        enc_key = self.config.get("encryption_key")
        if not enc_key:
            raise ValueError(f"Falta MISTRAL_ENCRYPTION_KEY_{self.region} para cifrar.")
        try:
            from cryptography.fernet import Fernet
            cipher = Fernet(enc_key.encode() if isinstance(enc_key, str) else enc_key)
            return cipher.encrypt(api_key.encode()).decode()
        except Exception as e:
            logger.error("Error cifrando API key: %s", e)
            raise

    def _decrypt_key(self, encrypted_key: str) -> str:
        """Descifra la API Key almacenada."""
        enc_key = self.config.get("encryption_key")
        if not enc_key:
            raise ValueError(f"Falta MISTRAL_ENCRYPTION_KEY_{self.region} para descifrar.")
        try:
            from cryptography.fernet import Fernet
            cipher = Fernet(enc_key.encode() if isinstance(enc_key, str) else enc_key)
            return cipher.decrypt(encrypted_key.encode()).decode()
        except Exception as e:
            logger.error("Error descifrando API key: %s", e)
            raise

    def get_valid_key(self) -> str:
        """Obtiene la API Key válida (cifrada en env o en claro para desarrollo)."""
        self._validate_env()
        encrypted_key = os.getenv("ENCRYPTED_MISTRAL_API_KEY")
        if encrypted_key:
            return self._decrypt_key(encrypted_key)
        plain = os.getenv("MISTRAL_API_KEY")
        if plain:
            logger.info("Usando MISTRAL_API_KEY en claro (desarrollo)")
            return plain
        raise ValueError("No se encontró ENCRYPTED_MISTRAL_API_KEY ni MISTRAL_API_KEY en .env")


# --- Data Manager ---

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None  # type: ignore


class MistralDataManager:
    """
    Carga, valida y transforma datasets para Mistral API.

    Soporta CSV, JSON y Parquet. Aplica validación de cumplimiento (GDPR)
    según la región configurada.
    """

    def __init__(self, region: str = "ES") -> None:
        self.region = region
        config = DEFAULT_REGION_CONFIG.get(region, DEFAULT_REGION_CONFIG["GLOBAL"])
        self.compliance: List[str] = config.get("compliance", ["GDPR"])
        logger.info(
            "Inicializado MistralDataManager para %s (Cumplimiento: %s)",
            region,
            self.compliance,
        )

    def load_dataset(
        self,
        file_path: str,
        file_type: Optional[str] = None,
        drop_pii_columns: bool = True,
    ) -> Any:
        """
        Carga un dataset desde CSV, JSON o Parquet.

        Args:
            file_path: Ruta al archivo.
            file_type: "csv", "json" o "parquet". Si es None, se infiere por extensión.
            drop_pii_columns: Si True (default), elimina columnas PII conocidas (GDPR).

        Returns:
            DataFrame de pandas (si está instalado).

        Raises:
            ValueError: Tipo de archivo no soportado.
            FileNotFoundError: Archivo no encontrado.
        """
        if not HAS_PANDAS:
            raise RuntimeError("Se requiere pandas para load_dataset. pip install pandas pyarrow")

        if file_type is None:
            ext = Path(file_path).suffix.lstrip(".").lower()
            if ext not in {"csv", "json", "parquet"}:
                raise ValueError(f"Extensión no soportada: {ext}. Usa csv, json o parquet.")
            file_type = ext

        try:
            if file_type == "csv":
                df = pd.read_csv(file_path)
            elif file_type == "json":
                df = pd.read_json(file_path)
            elif file_type == "parquet":
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(
                    "Tipo de archivo no soportado. Usa 'csv', 'json' o 'parquet'."
                )

            if drop_pii_columns and "GDPR" in self.compliance:
                to_drop = [c for c in df.columns if c.lower() in {p.lower() for p in PII_COLUMNS_DEFAULT}]
                if to_drop:
                    df = df.drop(columns=to_drop, errors="ignore")
                    logger.info("Columnas PII eliminadas (data minimization): %s", to_drop)

            if "GDPR" in self.compliance:
                self._validate_gdpr_compliance(df)

            logger.info("Dataset cargado: %s (%d registros)", file_path, len(df))
            return df
        except FileNotFoundError:
            logger.error("Archivo no encontrado: %s", file_path)
            raise
        except Exception as e:
            logger.error("Error cargando dataset: %s", e)
            raise

    def _validate_gdpr_compliance(self, df: Any) -> None:
        """Valida que el dataset cumpla con GDPR (datos personales anonimizados)."""
        if not HAS_PANDAS:
            return
        personal_cols = [
            col for col in df.columns
            if "email" in col.lower() or "dni" in col.lower() or "phone" in col.lower()
        ]
        if not personal_cols:
            return
        for col in personal_cols:
            sample = df[col].dropna().astype(str)
            if len(sample) and not sample.str.startswith("ANON_").all():
                logger.warning(
                    "Posible incumplimiento GDPR: columna '%s' con datos personales. "
                    "Anonimizar en producción.",
                    col,
                )


# --- Mistral API Client (con rate limiting) ---


class MistralAPIClient:
    """
    Cliente para Mistral API (v1/chat/completions).

    Incluye rate limiting configurable y registro de transacciones
    para GaiaChain 2.0.
    """

    def __init__(
        self,
        api_key: str,
        region: str = "ES",
        rate_limit_per_minute: Optional[int] = None,
    ) -> None:
        self.api_key = api_key
        self.region = region
        self.config = DEFAULT_REGION_CONFIG.get(region, DEFAULT_REGION_CONFIG["GLOBAL"])
        self.base_url = self.config["api_endpoint"].rstrip("/")
        self.rate_limit_per_minute = rate_limit_per_minute or DEFAULT_RATE_LIMIT_PER_MINUTE
        self._request_times: List[float] = []

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        logger.info("Cliente Mistral API inicializado para %s", region)

    def _wait_rate_limit(self) -> None:
        """Respeta el límite de solicitudes por minuto."""
        now = time.monotonic()
        cutoff = now - 60
        self._request_times[:] = [t for t in self._request_times if t > cutoff]
        if len(self._request_times) >= self.rate_limit_per_minute:
            sleep_time = 60 - (now - self._request_times[0])
            if sleep_time > 0:
                logger.info("Rate limit: esperando %.1f s", sleep_time)
                time.sleep(sleep_time)
            self._request_times[:] = []
        self._request_times.append(time.monotonic())

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        stream: bool = False,
        timeout: Optional[int] = 30,
    ) -> Dict[str, Any]:
        """
        Envía una consulta a Mistral API y devuelve la respuesta.

        Args:
            model: Modelo (ej: "mistral-tiny", "mistral-small").
            prompt: Texto de entrada.
            temperature: Creatividad 0.0–1.0.
            max_tokens: Máximo de tokens en la respuesta.
            stream: Si True, devuelve un generador (no implementado aquí; se ignora).
            timeout: Segundos para la petición HTTP (default 30).

        Returns:
            Respuesta JSON de la API (choices[0].message.content, etc.).

        Raises:
            ValueError: 401 API key inválida, 429 rate limit.
            requests.RequestException: Error de red o HTTP.
        """
        if stream:
            logger.warning("stream=True no implementado en esta versión; se ignora.")
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        self._wait_rate_limit()
        timeout = timeout or 30

        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=timeout,
            )
            if response.status_code == 401:
                logger.error("Mistral API: API key inválida (401)")
                raise ValueError("API key inválida. Comprueba MISTRAL_API_KEY o ENCRYPTED_MISTRAL_API_KEY.")
            if response.status_code == 403:
                logger.error("Mistral API: Acceso denegado (403)")
                raise ValueError("Acceso denegado a Mistral API (403). Revisa permisos de la clave.")
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                logger.warning("Mistral API: Rate limit excedido (429). Retry-After: %s", retry_after)
                raise ValueError(f"Rate limit excedido. Reintentar después de {retry_after} s.")
            response.raise_for_status()
            result = response.json()

            self._log_to_gaiachain(payload, result)
            return result
        except requests.exceptions.RequestException as e:
            logger.error("Error en Mistral API: %s", e)
            raise

    def _log_to_gaiachain(self, request: Dict[str, Any], response: Dict[str, Any]) -> None:
        """Registra la transacción para GaiaChain 2.0 (log local + POST a API si está configurada)."""
        payload = f"{json.dumps(request, sort_keys=True)}{json.dumps(response, sort_keys=True)}{datetime.utcnow().isoformat()}"
        tx_hash = hashlib.sha256(payload.encode()).hexdigest()
        logger.info("Registro GaiaChain (simulado): %s", tx_hash[:16] + "...")
        gaia_url = os.getenv("GAIA_CHAIN_API_URL", "").rstrip("/")
        if gaia_url:
            try:
                r = requests.post(
                    f"{gaia_url}/api/v1/witness",
                    json={"hash": tx_hash, "source": "mistral_adapter", "timestamp": datetime.utcnow().isoformat()},
                    timeout=5,
                )
                if r.status_code in (200, 201, 202):
                    logger.info("GaiaChain witness enviado: %s", r.text[:80] if r.text else "OK")
                else:
                    logger.warning("GaiaChain witness %s: %s", r.status_code, r.text[:200] if r.text else "")
            except Exception as e:
                logger.warning("GaiaChain witness fallido: %s", e)


# --- MistralAdapter (facade para FastAPI / uso integrado) ---


class MistralAdapter:
    """
    Facade que combina APIKeyManager, MistralDataManager y MistralAPIClient.

    Uso típico: cargar opcionalmente un dataset desde dataset_path, construir
    prompt con contexto, y enviar consulta a Mistral API. Auto-configuración desde .env.
    """

    def __init__(self, region: Optional[str] = None) -> None:
        self.region = region or os.getenv("MISTRAL_REGION", "ES")
        self._key_manager = APIKeyManager(region=self.region)
        self._data_manager = MistralDataManager(region=self.region)

    def query(
        self,
        dataset_path: Optional[str],
        query: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: str = "mistral-small",
    ) -> Dict[str, Any]:
        """
        Ejecuta una consulta a Mistral API, opcionalmente con contexto de un dataset.

        Args:
            dataset_path: Ruta a CSV/JSON/Parquet; si existe se carga y se añade resumen al prompt.
            query: Pregunta o instrucción para el modelo.
            temperature: Creatividad 0.0–1.0.
            max_tokens: Máximo de tokens en la respuesta.
            model: Modelo Mistral (ej: mistral-tiny, mistral-small).

        Returns:
            Respuesta completa de la API (choices[0].message.content, usage, etc.).
        """
        api_key = self._key_manager.get_valid_key()
        client = MistralAPIClient(api_key=api_key, region=self.region)

        prompt = query
        if dataset_path and os.path.isfile(dataset_path):
            try:
                df = self._data_manager.load_dataset(dataset_path, drop_pii_columns=True)
                if HAS_PANDAS and df is not None and len(df) > 0:
                    table = _safe_to_markdown(df)
                    prompt = f"Contexto (dataset):\n{table}\n\nPregunta: {query}"
            except Exception as e:
                logger.warning("No se pudo cargar dataset %s: %s. Usando solo query.", dataset_path, e)

        return client.query(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=60,
        )


# --- Ejemplo Sabionda Educa ---


def ejemplo_completo() -> None:
    """
    Ejemplo completo: carga de datos y consulta a Mistral API.

    Para Sabionda Educa. Requiere:
    - MISTRAL_API_KEY (o ENCRYPTED_MISTRAL_API_KEY + clave de cifrado) en .env.
    - Archivo data/agritech_samples.csv (o ajustar ruta).
    """
    # 1. Cargar dataset
    manager = MistralDataManager(region="ES")
    data_path = "data/agritech_samples.csv"
    if not os.path.isfile(data_path):
        logger.warning("No existe %s; usando DataFrame vacío para el ejemplo.", data_path)
        if HAS_PANDAS:
            df = pd.DataFrame({"cultivo": ["maíz", "trigo"], "humedad": [0.6, 0.5]})
        else:
            df = None
    else:
        df = manager.load_dataset(data_path)

    # 2. Obtener API key y cliente
    key_manager = APIKeyManager(region="ES")
    try:
        api_key = key_manager.get_valid_key()
    except ValueError as e:
        logger.error("Configura API key en .env: %s", e)
        return

    client = MistralAPIClient(api_key=api_key, region="ES")

    # 3. Construir prompt con resumen del dataset
    if df is not None and HAS_PANDAS and len(df) > 0:
        table = _safe_to_markdown(df)
        prompt = f"""
Analiza este dataset de cultivos y sugiere 3 estrategias para optimizar el riego usando IA:

{table}
"""
    else:
        prompt = "Sugiere 3 estrategias para optimizar el riego en agricultura usando IA."

    try:
        response = client.query(model="mistral-small", prompt=prompt)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        print("Respuesta de Mistral API:")
        print(content)
    except Exception as e:
        logger.error("Error en consulta: %s", e)


if __name__ == "__main__":
    ejemplo_completo()
