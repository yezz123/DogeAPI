"""Smoke tests for the bootstrap (P0)."""

from __future__ import annotations

from httpx import AsyncClient


class TestHealthz:
    """Liveness probe must always be on, regardless of feature flags."""

    async def test_returns_200_with_status_ok(self, client: AsyncClient) -> None:
        response = await client.get("/healthz")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "version" in body

    async def test_reports_env_from_settings(self, client: AsyncClient) -> None:
        response = await client.get("/healthz")
        assert response.json()["env"] == "test"


class TestRoot:
    """Service identity endpoint."""

    async def test_returns_app_name_and_version(self, client: AsyncClient) -> None:
        response = await client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "AI Template"
        assert "version" in body


class TestOpenAPI:
    """OpenAPI is published for the docs UI to work."""

    async def test_openapi_schema_is_generated(self, client: AsyncClient) -> None:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "AI Template"
