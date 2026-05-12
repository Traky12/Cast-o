# tests/test_opa_integration.py — Pruebas de integración con OPA

from unittest.mock import MagicMock, patch

from backend.compliance.opa_client import OPAClient


def test_opa_evaluate_allows():
    with patch("backend.compliance.opa_client._REQUESTS", True), patch(
        "backend.compliance.opa_client.requests"
    ) as mock_requests:
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"allow": True}}
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        client = OPAClient(opa_url="http://opa:8181")
        result = client.evaluate(
            {
                "action": {"type": "deployment", "environment": "staging"},
                "metadata": {"normative": "ISO_27001:A.12.5.1", "timestamp": "2024-01-01T00:00:00"},
            }
        )
        assert result is True
        mock_requests.post.assert_called_once()


def test_opa_evaluate_denies():
    with patch("backend.compliance.opa_client._REQUESTS", True), patch(
        "backend.compliance.opa_client.requests"
    ) as mock_requests:
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"allow": False}}
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        client = OPAClient(opa_url="http://opa:8181")
        result = client.evaluate({"action": {"type": "unknown"}, "metadata": {}})
        assert result is False


def test_opa_evaluate_request_error():
    with patch("backend.compliance.opa_client._REQUESTS", True), patch(
        "backend.compliance.opa_client.requests"
    ) as mock_requests:
        mock_requests.post.side_effect = Exception("Timeout")

        client = OPAClient(opa_url="http://opa:8181")
        result = client.evaluate({"action": {}, "metadata": {}})
        assert result is False


def test_opa_evaluate_and_register():
    with patch("backend.compliance.opa_client._REQUESTS", True), patch(
        "backend.compliance.opa_client.requests"
    ) as mock_req, patch(
        "backend.security.pq_crypto.PostQuantumCrypto", MagicMock()
    ), patch("os.path.isfile", return_value=False):
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"allow": True}}
        mock_response.status_code = 200
        mock_req.post.return_value = mock_response

        client = OPAClient(opa_url="http://opa:8181")
        result = client.evaluate_and_register(
            {
                "action": {"type": "self_healing", "severity": "critical"},
                "metadata": {"normative": "ISO_27001:A.16.1.1", "timestamp": "2024-01-01T00:00:00"},
            }
        )
        assert result["compliant"] is True
        assert result["policy"] == "castuo/compliance"
