"""Tests for Health Check API Endpoints."""

from datetime import datetime
from typing import AsyncIterator

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


class TestHealthEndpoints:
    """Health endpoint test suite."""

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_health_check_endpoint_returns_200(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_health_check_response_structure(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        data = response.json()
        assert {"status", "timestamp", "version", "environment"}.issubset(data)

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_health_check_status_is_healthy(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_health_check_version(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        data = response.json()
        assert data["version"] == "1.0.0"

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_health_check_environment(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        data = response.json()
        assert data["environment"] == "development"

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_health_check_timestamp_format(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        data = response.json()
        try:
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_detailed_health_check_endpoint_returns_200(self, async_client: AsyncClient):
        response = await async_client.get("/health/detailed")
        assert response.status_code == 200

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_detailed_health_check_response_structure(self, async_client: AsyncClient):
        response = await async_client.get("/health/detailed")
        data = response.json()
        assert {"status", "timestamp", "version", "environment", "debug", "system", "services"}.issubset(data)

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_detailed_health_check_system_info(self, async_client: AsyncClient):
        response = await async_client.get("/health/detailed")
        system = response.json()["system"]
        assert system["project_name"] == "Focus Tracker"
        assert "api_version" in system

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_detailed_health_check_services_info(self, async_client: AsyncClient):
        response = await async_client.get("/health/detailed")
        services = response.json()["services"]
        assert services["database"] == "not_configured"
        assert services["authentication"] == "not_configured"

    @pytest.mark.health
    @pytest.mark.anyio
    async def test_health_endpoints_are_accessible_without_auth(self, async_client: AsyncClient):
        health_response = await async_client.get("/health")
        detailed_response = await async_client.get("/health/detailed")
        assert health_response.status_code == 200
        assert detailed_response.status_code == 200
