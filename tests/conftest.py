"""Configuración compartida de tests para resolver imports del proyecto desde raíz."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def app():
    from api.main import app as fastapi_app

    return fastapi_app
