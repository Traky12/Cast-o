"""Regression: models must tolerate being imported through both `models.*` and `api.models.*`.

pytest.ini puts both `.` and `api` on sys.path, and the codebase uses a
`try: from models.X / except: from api.models.X` pattern. Loading
EducationalResource through both paths used to raise
`InvalidRequestError: Table 'educational_resources' is already defined` at
collection time (CI-DEBT-003).
"""
import importlib


def test_educational_resource_importable_via_both_paths():
    bare = importlib.import_module("models.educational_resource")
    pkg = importlib.import_module("api.models.educational_resource")
    assert bare.EducationalResource.__tablename__ == "educational_resources"
    assert pkg.EducationalResource.__tablename__ == "educational_resources"
