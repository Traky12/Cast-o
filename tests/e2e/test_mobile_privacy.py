import os
import time

import pytest

pytest.importorskip(
    "selenium",
    reason="E2E: pip install -r tests/requirements.txt",
)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:3000")

MOBILE_DEVICES = [
    {"name": "iPhone SE", "width": 320, "height": 568, "pixel_ratio": 2},
    {"name": "iPhone 12", "width": 390, "height": 844, "pixel_ratio": 3},
    {"name": "Galaxy S20", "width": 360, "height": 800, "pixel_ratio": 3},
    {"name": "iPad Mini", "width": 768, "height": 1024, "pixel_ratio": 2},
]


@pytest.fixture(scope="module", params=MOBILE_DEVICES)
def mobile_driver(request):
    """Configura un driver de Chrome emulando un dispositivo móvil."""
    device = request.param
    options = Options()
    mobile_emulation = {
        "deviceMetrics": {
            "width": device["width"],
            "height": device["height"],
            "pixelRatio": device["pixel_ratio"],
        },
        "userAgent": (
            f"Mozilla/5.0 (Linux; Android 10; {device['name']}) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.210 Mobile Safari/537.36"
        ),
    }
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    yield driver, device
    driver.quit()


def test_mobile_privacy_flow(mobile_driver):
    """Flujo de privacidad en resoluciones móviles (320px–768px)."""
    driver, device = mobile_driver
    print(f"\n📱 Probando en {device['name']} ({device['width']}x{device['height']})")

    driver.get(f"{DASHBOARD_URL}/#/privacidad")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".privacy-module h2"))
    )

    privacy_module = driver.find_element(By.CSS_SELECTOR, ".privacy-module")
    module_width = privacy_module.size["width"]
    assert module_width <= device["width"], f"El módulo no cabe en {device['name']}"

    token_input = driver.find_element(By.CSS_SELECTOR, ".token-selector input")
    token_input.clear()
    token_input.send_keys("1")

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".property-preview h3"))
    )
    property_preview = driver.find_element(By.CSS_SELECTOR, ".property-preview")
    preview_top = property_preview.location["y"]
    preview_bottom = preview_top + property_preview.size["height"]
    erasure_button = driver.find_element(By.CSS_SELECTOR, ".erasure-button")
    button_top = erasure_button.location["y"]
    assert (
        button_top > preview_bottom
    ), "El botón se solapa con la vista previa en móviles"

    erasure_button.click()

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".confirmation-modal"))
    )
    modal = driver.find_element(By.CSS_SELECTOR, ".confirmation-modal")
    modal_width = modal.size["width"]
    assert (
        modal_width <= device["width"] * 0.9
    ), "El modal es demasiado ancho para móviles"

    confirm_button = driver.find_element(
        By.CSS_SELECTOR, ".confirmation-modal .confirm-button"
    )
    confirm_button.click()

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
    )

    print(f"✅ Flujo de privacidad validado en {device['name']}.")


def test_mobile_menu_accessibility(mobile_driver):
    """Accesibilidad del menú y acceso a Privacidad en móviles."""
    driver, device = mobile_driver
    driver.get(DASHBOARD_URL)

    menu_button = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".mobile-menu-button"))
    )
    menu_button.click()

    privacy_link = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".mobile-menu a[href*='/privacidad']")
        )
    )
    privacy_link.click()

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".privacy-module h2"))
    )

    print(f"✅ Menú móvil validado en {device['name']}.")


def test_touch_targets_size(mobile_driver):
    """Verifica que los elementos táctiles cumplan tamaño mínimo recomendado (48x48px)."""
    driver, device = mobile_driver
    driver.get(f"{DASHBOARD_URL}/#/privacidad")

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".privacy-module h2"))
    )

    erasure_button = driver.find_element(By.CSS_SELECTOR, ".erasure-button")
    button_width = erasure_button.size["width"]
    button_height = erasure_button.size["height"]
    assert (
        button_width >= 48 and button_height >= 48
    ), "El botón 'Ejercer Derecho al Olvido' es demasiado pequeño para touch"

    token_input = driver.find_element(By.CSS_SELECTOR, ".token-selector input")
    input_height = token_input.size["height"]
    assert input_height >= 48, "El campo de token es demasiado pequeño para touch"

    time.sleep(1)

