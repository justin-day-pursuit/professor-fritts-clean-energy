"""Smoke test for the public health endpoint."""


def test_health_returns_ok(api_client):
    """GET /api/health should report ok and echo configured tool/LLM modes."""
    response = api_client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "tool_mode" in body
    assert "llm_provider" in body
    assert "django_version" in body
    assert body["django_version"].startswith("5.")
