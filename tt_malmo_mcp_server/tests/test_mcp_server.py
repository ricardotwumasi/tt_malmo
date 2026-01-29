"""
Tests for MCP Server endpoints.

Tests cover:
- REST API endpoints
- Agent lifecycle management
- WebSocket connections
- Error handling
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self, test_client):
        """Test root endpoint returns server info."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Malmo MCP Server"
        assert "version" in data
        assert data["status"] == "running"


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, test_client):
        """Test health check returns status."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_agents" in data
        assert "connected_websockets" in data


class TestAgentEndpoints:
    """Test agent management endpoints."""

    def test_list_agents_empty(self, test_client):
        """Test listing agents when none exist."""
        response = test_client.get("/agents")

        assert response.status_code == 200
        # Note: May have agents from other tests, so just check it's a list
        assert isinstance(response.json(), list)

    @patch('mcp_server.agent_manager.create_adapter')
    def test_create_agent(self, mock_create_adapter, test_client):
        """Test agent creation."""
        # Setup mock
        mock_adapter = MagicMock()
        mock_adapter.generate = AsyncMock(return_value="ACTION: explore\nREASONING: test\nTARGET: none")
        mock_create_adapter.return_value = mock_adapter

        response = test_client.post(
            "/agents",
            json={
                "name": "TestAgent",
                "llm_type": "gemini",
                "role": 0,
                "traits": ["curious"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert data["name"] == "TestAgent"
        assert data["status"] == "created"

    @patch('mcp_server.agent_manager.create_adapter')
    def test_get_agent(self, mock_create_adapter, test_client):
        """Test getting a specific agent."""
        # Setup mock
        mock_adapter = MagicMock()
        mock_create_adapter.return_value = mock_adapter

        # Create agent first
        create_response = test_client.post(
            "/agents",
            json={
                "name": "GetTestAgent",
                "llm_type": "gemini",
                "role": 0
            }
        )
        agent_id = create_response.json()["agent_id"]

        # Get the agent
        response = test_client.get(f"/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert data["name"] == "GetTestAgent"

    def test_get_agent_not_found(self, test_client):
        """Test getting non-existent agent."""
        response = test_client.get("/agents/non-existent-id")

        assert response.status_code == 404

    @patch('mcp_server.agent_manager.create_adapter')
    def test_delete_agent(self, mock_create_adapter, test_client):
        """Test agent deletion."""
        # Setup mock
        mock_adapter = MagicMock()
        mock_create_adapter.return_value = mock_adapter

        # Create agent first
        create_response = test_client.post(
            "/agents",
            json={
                "name": "DeleteTestAgent",
                "llm_type": "gemini",
                "role": 0
            }
        )
        agent_id = create_response.json()["agent_id"]

        # Delete the agent
        response = test_client.delete(f"/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"

        # Verify it's gone
        get_response = test_client.get(f"/agents/{agent_id}")
        assert get_response.status_code == 404

    def test_delete_agent_not_found(self, test_client):
        """Test deleting non-existent agent."""
        response = test_client.delete("/agents/non-existent-id")

        assert response.status_code == 404


class TestAgentLifecycle:
    """Test agent start/stop endpoints."""

    @patch('mcp_server.agent_manager.create_adapter')
    def test_start_agent(self, mock_create_adapter, test_client):
        """Test starting an agent."""
        # Setup mock
        mock_adapter = MagicMock()
        mock_adapter.generate = AsyncMock(return_value="ACTION: explore\nREASONING: test\nTARGET: none")
        mock_create_adapter.return_value = mock_adapter

        # Create agent
        create_response = test_client.post(
            "/agents",
            json={
                "name": "StartTestAgent",
                "llm_type": "gemini",
                "role": 0
            }
        )
        agent_id = create_response.json()["agent_id"]

        # Start the agent
        response = test_client.post(f"/agents/{agent_id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"

        # Note: Cleanup happens automatically when test client disconnects

    @patch('mcp_server.agent_manager.create_adapter')
    def test_stop_agent(self, mock_create_adapter, test_client):
        """Test stopping an agent."""
        # Setup mock
        mock_adapter = MagicMock()
        mock_adapter.generate = AsyncMock(return_value="ACTION: explore\nREASONING: test\nTARGET: none")
        mock_create_adapter.return_value = mock_adapter

        # Create agent (don't start it for simpler test)
        create_response = test_client.post(
            "/agents",
            json={
                "name": "StopTestAgent",
                "llm_type": "gemini",
                "role": 0
            }
        )
        agent_id = create_response.json()["agent_id"]

        # Stop the agent (even if not started, should return success)
        response = test_client.post(f"/agents/{agent_id}/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"

    def test_start_agent_not_found(self, test_client):
        """Test starting non-existent agent."""
        response = test_client.post("/agents/non-existent-id/start")

        assert response.status_code == 404

    def test_stop_agent_not_found(self, test_client):
        """Test stopping non-existent agent."""
        response = test_client.post("/agents/non-existent-id/stop")

        assert response.status_code == 404


class TestInvalidRequests:
    """Test handling of invalid requests."""

    def test_create_agent_missing_name(self, test_client):
        """Test creating agent without name."""
        response = test_client.post(
            "/agents",
            json={
                "llm_type": "gemini",
                "role": 0
            }
        )

        assert response.status_code == 422  # Validation error

    def test_create_agent_invalid_llm_type(self, test_client):
        """Test creating agent with invalid LLM type."""
        response = test_client.post(
            "/agents",
            json={
                "name": "TestAgent",
                "llm_type": "invalid_provider",
                "role": 0
            }
        )

        assert response.status_code == 500  # Internal error from validation


class TestWebSocket:
    """Test WebSocket endpoints."""

    @patch('mcp_server.agent_manager.create_adapter')
    def test_websocket_connection(self, mock_create_adapter, test_client):
        """Test WebSocket connection for agent."""
        # Setup mock
        mock_adapter = MagicMock()
        mock_create_adapter.return_value = mock_adapter

        # Create agent
        create_response = test_client.post(
            "/agents",
            json={
                "name": "WSTestAgent",
                "llm_type": "gemini",
                "role": 0
            }
        )
        agent_id = create_response.json()["agent_id"]

        # Test WebSocket connection
        with test_client.websocket_connect(f"/ws/agent/{agent_id}") as websocket:
            # Connection should be accepted
            assert websocket is not None

            # Send an observation message
            websocket.send_json({
                "type": "observation",
                "observation": {
                    "XPos": 0.0,
                    "YPos": 64.0,
                    "ZPos": 0.0
                }
            })

    def test_websocket_agent_not_found(self, test_client):
        """Test WebSocket connection for non-existent agent."""
        with pytest.raises(Exception):
            with test_client.websocket_connect("/ws/agent/non-existent-id"):
                pass  # Should fail before reaching here
