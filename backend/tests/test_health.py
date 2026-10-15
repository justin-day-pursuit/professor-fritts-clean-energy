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


def test_cors_preflight_vercel_origin(api_client):
    """OPTIONS /api/health with Vercel origin should return 200 with CORS headers."""
    response = api_client.options(
        "/api/health",
        headers={
            "Origin": "https://professor-fritts-clean-energy.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "https://professor-fritts-clean-energy.vercel.app"
    )

