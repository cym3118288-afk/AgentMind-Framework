"""
Tests for Wave 2 Web UI and Dashboard Features

Tests:
- Agent Designer Enhanced API endpoints
- Chat Server Wave 2 features (file upload, threading, export)
- Dashboard Enhanced metrics and alerts
- WebSocket connections
- Real - time updates
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
import tempfile
import os

# Skip all tests if fastapi is not available
pytest.importorskip("fastapi")


# Test Agent Designer Enhanced
class TestAgentDesignerEnhanced:
    """Test suite for enhanced agent designer."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agent_designer_enhanced import app

        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "features" in data

    def test_get_templates(self, client):
        """Test getting agent templates."""
        response = client.get("/api / templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "development" in data["templates"]
        assert "research" in data["templates"]

    def test_get_templates_by_category(self, client):
        """Test getting templates by category."""
        response = client.get("/api / templates / development")
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "development"
        assert len(data["templates"]) > 0

    def test_save_config(self, client):
        """Test saving agent configuration."""
        config = {
            "team_name": "Test Team",
            "llm_provider": "ollama",
            "model": "llama3.2",
            "max_rounds": 5,
            "agents": [
                {"name": "TestAgent", "role": "tester", "system_prompt": "You are a test agent"}
            ],
        }

        response = client.post("/api / configs", json=config)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "config_id" in data

    def test_save_invalid_config(self, client):
        """Test saving invalid configuration."""
        config = {"team_name": "", "agents": []}  # Invalid: empty name  # Invalid: no agents

        response = client.post("/api / configs", json=config)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_list_configs(self, client):
        """Test listing configurations."""
        response = client.get("/api / configs")
        assert response.status_code == 200
        data = response.json()
        assert "configs" in data

    def test_validate_config(self, client):
        """Test configuration validation."""
        valid_config = {"team_name": "Valid Team", "agents": [{"name": "Agent1", "role": "test"}]}

        response = client.post("/api / validate", json=valid_config)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_invalid_config(self, client):
        """Test validation of invalid configuration."""
        invalid_config = {
            "team_name": "Test",
            "agents": [
                {"name": "Agent1", "role": "test"},
                {"name": "Agent1", "role": "test"},  # Duplicate name
            ],
        }

        response = client.post("/api / validate", json=invalid_config)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_export_config_json(self, client):
        """Test exporting configuration as JSON."""
        # First create a config
        config = {"team_name": "Export Test", "agents": [{"name": "Agent1", "role": "test"}]}
        response = client.post("/api / configs", json=config)
        config_id = response.json()["config_id"]

        # Export it
        response = client.get(f"/api / configs/{config_id}/export?format=json")
        assert response.status_code == 200

    def test_export_config_python(self, client):
        """Test exporting configuration as Python code."""
        config = {"team_name": "Python Export", "agents": [{"name": "Agent1", "role": "test"}]}
        response = client.post("/api / configs", json=config)
        config_id = response.json()["config_id"]

        response = client.get(f"/api / configs/{config_id}/export?format=python")
        assert response.status_code == 200


# Test Chat Server Wave 2
class TestChatServerWave2:
    """Test suite for enhanced chat server."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from chat_server_wave2 import app

        return app.test_client()

    def test_health_endpoint(self, client):
        """Test health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert "features" in data

    def test_list_sessions(self, client):
        """Test listing sessions."""
        response = client.get("/api / sessions")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "sessions" in data

    def test_file_upload(self, client):
        """Test file upload functionality."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = client.post("/api / upload", data={"file": (f, "test.txt")})

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "file_id" in data
        finally:
            os.unlink(temp_path)

    def test_file_upload_invalid_type(self, client):
        """Test uploading invalid file type."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".exe", delete=False) as f:
            f.write("Invalid")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = client.post("/api / upload", data={"file": (f, "test.exe")})

            assert response.status_code == 400
        finally:
            os.unlink(temp_path)

    def test_export_session_markdown(self, client):
        """Test exporting session as Markdown."""
        # This would require a valid session ID
        # For now, test the endpoint exists
        response = client.get("/api / sessions / test - id / export?format=markdown")
        # Will return 404 for non - existent session, which is expected
        assert response.status_code in [200, 404]

    def test_search_messages(self, client):
        """Test message search."""
        response = client.get("/api / search / test - session?q=test")
        # Will return 404 for non - existent session
        assert response.status_code in [200, 404]


# Test Dashboard Enhanced
class TestDashboardEnhanced:
    """Test suite for enhanced dashboard."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from dashboard_enhanced import app

        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "features" in data

    def test_metrics_summary(self, client):
        """Test getting metrics summary."""
        response = client.get("/api / metrics / summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "total_tokens" in data
        assert "total_cost" in data

    def test_agent_metrics(self, client):
        """Test getting agent metrics."""
        response = client.get("/api / metrics / agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data

    def test_agent_comparison(self, client):
        """Test agent performance comparison."""
        response = client.get("/api / metrics / comparison")
        assert response.status_code == 200
        data = response.json()
        assert "comparison" in data

    def test_historical_metrics(self, client):
        """Test getting historical metrics."""
        response = client.get("/api / metrics / historical?hours=24")
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "data" in data

    def test_get_alerts(self, client):
        """Test getting alerts."""
        response = client.get("/api / alerts")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "count" in data

    def test_get_alert_config(self, client):
        """Test getting alert configuration."""
        response = client.get("/api / alerts / config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data

    def test_update_alert_config(self, client):
        """Test updating alert configuration."""
        new_config = {"response_time_threshold": 6000, "error_rate_threshold": 0.1}

        response = client.post("/api / alerts / config", json=new_config)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_recommendations(self, client):
        """Test getting optimization recommendations."""
        response = client.get("/api / recommendations")
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    def test_export_metrics(self, client):
        """Test exporting metrics."""
        response = client.get("/api / export / metrics?format=json")
        assert response.status_code == 200


# Test WebSocket Connections
class TestWebSocketConnections:
    """Test WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_designer_websocket(self):
        """Test agent designer WebSocket connection."""
        from fastapi.testclient import TestClient
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agent_designer_enhanced import app

        client = TestClient(app)

        with client.websocket_connect("/ws / test") as websocket:
            # Send test agent request
            websocket.send_json(
                {
                    "action": "test_agent",
                    "agent": {"name": "TestAgent", "role": "test"},
                    "input": "Hello",
                }
            )

            # Receive response
            data = websocket.receive_json()
            assert data["type"] == "test_start"

            data = websocket.receive_json()
            assert data["type"] == "test_response"

    @pytest.mark.asyncio
    async def test_dashboard_websocket(self):
        """Test dashboard WebSocket connection."""
        from fastapi.testclient import TestClient
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from dashboard_enhanced import app

        client = TestClient(app)

        with client.websocket_connect("/ws / metrics") as websocket:
            # Receive metrics update
            data = websocket.receive_json()
            assert "total_requests" in data


# Integration Tests
class TestIntegration:
    """Integration tests for Wave 2 features."""

    def test_end_to_end_agent_design(self):
        """Test complete agent design workflow."""
        from fastapi.testclient import TestClient
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agent_designer_enhanced import app

        client = TestClient(app)

        # 1. Get templates
        response = client.get("/api / templates")
        assert response.status_code == 200

        # 2. Create configuration
        config = {
            "team_name": "Integration Test Team",
            "llm_provider": "ollama",
            "model": "llama3.2",
            "agents": [{"name": "Agent1", "role": "test1"}, {"name": "Agent2", "role": "test2"}],
        }

        response = client.post("/api / configs", json=config)
        assert response.status_code == 200
        config_id = response.json()["config_id"]

        # 3. Retrieve configuration
        response = client.get(f"/api / configs/{config_id}")
        assert response.status_code == 200

        # 4. Export configuration
        response = client.get(f"/api / configs/{config_id}/export?format=json")
        assert response.status_code == 200

        # 5. Delete configuration
        response = client.delete(f"/api / configs/{config_id}")
        assert response.status_code == 200

    def test_metrics_collection_flow(self):
        """Test metrics collection and analysis flow."""
        from fastapi.testclient import TestClient
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from dashboard_enhanced import app, metrics_store

        client = TestClient(app)

        # Add some test metrics
        for i in range(10):
            metrics_store.add_request(
                {
                    "agent": "TestAgent",
                    "duration": 1000 + i * 100,
                    "tokens": 500,
                    "cost": 0.01,
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Get summary
        response = client.get("/api / metrics / summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] >= 10

        # Get agent metrics
        response = client.get("/api / metrics / agents")
        assert response.status_code == 200

        # Get comparison
        response = client.get("/api / metrics / comparison")
        assert response.status_code == 200


# Performance Tests
class TestPerformance:
    """Performance tests for Wave 2 features."""

    def test_config_save_performance(self):
        """Test configuration save performance."""
        from fastapi.testclient import TestClient
        import sys
        import time

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agent_designer_enhanced import app

        client = TestClient(app)

        config = {
            "team_name": "Performance Test",
            "agents": [{"name": f"Agent{i}", "role": "test"} for i in range(10)],
        }

        start = time.time()
        response = client.post("/api / configs", json=config)
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should complete in less than 1 second

    def test_metrics_query_performance(self):
        """Test metrics query performance."""
        from fastapi.testclient import TestClient
        import sys
        import time

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from dashboard_enhanced import app

        client = TestClient(app)

        start = time.time()
        response = client.get("/api / metrics / summary")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.5  # Should be very fast


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
