import os
import time
import json

import pytest
import requests

pytest.importorskip(
    "selenium",
    reason="E2E: pip install -r tests/requirements.txt",
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:3000")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_TOKEN_ID = os.getenv("TEST_TOKEN_ID", "1")
TEST_WALLET_ADDRESS = os.getenv(
    "TEST_WALLET_ADDRESS",
    "0x7A1234567890abcdef1234567890abcdef12345678",
)
TEST_EMAIL = os.getenv("TEST_EMAIL", "propietario@test.com")


@pytest.fixture(scope="module")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def test_privacy_module_flow(driver):
    """Flujo completo del módulo de privacidad: dashboard → derecho al olvido → certificado."""
    driver.get(f"{DASHBOARD_URL}/#/privacidad")

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".privacy-module h2"))
    )

    token_input = driver.find_element(By.CSS_SELECTOR, ".token-selector input")
    token_input.clear()
    token_input.send_keys(TEST_TOKEN_ID)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".property-preview h3"))
    )

    erasure_button = driver.find_element(By.CSS_SELECTOR, ".erasure-button")
    erasure_button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".confirmation-modal"))
    )
    confirm_button = driver.find_element(
        By.CSS_SELECTOR, ".confirmation-modal .confirm-button"
    )
    confirm_button.click()

    WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
    )

    response = requests.get(
        f"{API_BASE_URL}/api/privacy/requests/{TEST_TOKEN_ID}", timeout=20
    )
    assert response.status_code == 200
    request_data = response.json()
    assert request_data.get("status") == "completed"
    assert str(request_data.get("token_id")) == str(TEST_TOKEN_ID)

    download_button = driver.find_element(By.CSS_SELECTOR, ".download-button")
    download_button.click()

    time.sleep(2)


def test_backend_erasure_endpoint():
    """Prueba directa del endpoint de borrado en el backend (sin navegador)."""
    response = requests.post(
        f"{API_BASE_URL}/api/privacy/request-erasure",
        json={
            "token_id": int(TEST_TOKEN_ID),
            "wallet_address": TEST_WALLET_ADDRESS,
            "email": TEST_EMAIL,
        },
        timeout=30,
    )

    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert "request_id" in data
    assert "transaction_hash" in data
    assert "certificate_url" in data

    property_response = requests.get(
        f"{API_BASE_URL}/api/property/{TEST_TOKEN_ID}", timeout=20
    )
    assert property_response.status_code == 200
    property_data = property_response.json()
    assert "ipfsHash" in property_data
    assert property_data["ipfsHash"] == data.get("new_ipfs_hash")


def test_certificate_generation_tmpdir(tmp_path):
    """Valida la generación de certificados PDF en el servicio de privacidad."""
    from api.services.privacy_service import generate_erasure_certificate

    cert_data = {
        "token_id": int(TEST_TOKEN_ID),
        "old_hash": "QmOldHash123",
        "new_hash": "QmNewHash456",
        "redacted_fields": ["Propietario", "DNI", "Email"],
        "tx_hash": "0x789abc123",
    }

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        certificate = generate_erasure_certificate(**cert_data)
    finally:
        os.chdir(original_dir)

    assert "id" in certificate
    assert "path" in certificate
    cert_path = certificate["path"]
    assert cert_path == "" or os.path.exists(cert_path)

