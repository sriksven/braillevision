import importlib.util
from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / "app" / "app.py"
SPEC = importlib.util.spec_from_file_location("braillevision_flask_app", APP_PATH)
app_module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(app_module)
app = app_module.app


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
