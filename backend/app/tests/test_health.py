"""
Tests for Health Check API Endpoints

Tests the health check functionality following TDD principles.
These tests ensure the API provides proper health status information.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app

# Create test client
client = TestClient(app)

class TestHealthEndpoints:
    """
    Health endpoint test suite.
    
    Follows SOLID principles:
    - Single Responsibility: Tests only health endpoints
    - Interface Segregation: Tests specific health contract
    """

    @pytest.mark.health
    def test_health_check_endpoint_returns_200(self):
        """Test that health check endpoint returns 200 status"""
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.health  
    def test_health_check_response_structure(self):
        """Test that health check returns correct response structure"""
        response = client.get("/health")
        data = response.json()
        
        # Verify required fields exist
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data

    @pytest.mark.health
    def test_health_check_status_is_healthy(self):
        """Test that health check returns healthy status"""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.health
    def test_health_check_version(self):
        """Test that health check returns version information"""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == "1.0.0"

    @pytest.mark.health
    def test_health_check_environment(self):
        """Test that health check returns environment information"""
        response = client.get("/health")
        data = response.json()
        assert data["environment"] == "development"

    @pytest.mark.health
    def test_health_check_timestamp_format(self):
        """Test that health check returns valid timestamp"""
        response = client.get("/health")
        data = response.json()
        
        # Verify timestamp can be parsed
        timestamp_str = data["timestamp"]
        # Should be able to parse ISO format timestamp
        try:
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

    @pytest.mark.health
    def test_detailed_health_check_endpoint_returns_200(self):
        """Test that detailed health check endpoint returns 200 status"""
        response = client.get("/health/detailed")
        assert response.status_code == 200

    @pytest.mark.health
    def test_detailed_health_check_response_structure(self):
        """Test that detailed health check returns comprehensive information"""
        response = client.get("/health/detailed")
        data = response.json()
        
        # Verify required fields exist
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "debug" in data
        assert "system" in data
        assert "services" in data

    @pytest.mark.health
    def test_detailed_health_check_system_info(self):
        """Test that detailed health check returns system information"""
        response = client.get("/health/detailed")
        data = response.json()
        
        system = data["system"]
        assert "api_version" in system
        assert "project_name" in system
        assert system["project_name"] == "Focus Tracker"

    @pytest.mark.health
    def test_detailed_health_check_services_info(self):
        """Test that detailed health check returns services status"""
        response = client.get("/health/detailed")
        data = response.json()
        
        services = data["services"]
        assert "database" in services
        assert "authentication" in services
        # In Phase 1, these should be not_configured
        assert services["database"] == "not_configured"
        assert services["authentication"] == "not_configured"

    @pytest.mark.health
    def test_health_endpoints_are_accessible_without_auth(self):
        """Test that health endpoints don't require authentication"""
        # Health endpoints should be publicly accessible
        health_response = client.get("/health")
        detailed_response = client.get("/health/detailed")
        
        # Both should work without any auth headers
        assert health_response.status_code == 200
        assert detailed_response.status_code == 200
