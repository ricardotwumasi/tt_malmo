"""
Pytest fixtures and configuration for the test suite.

Provides common fixtures for:
- Mock LLM adapters
- Test agent states
- Mock Malmo environment
- Test database setup
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Async test support
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock LLM Adapter
class MockLLMAdapter:
    """Mock LLM adapter for testing without API calls."""

    def __init__(self, model: str = "mock-model", responses: Optional[Dict[str, str]] = None):
        self.model = model
        self.responses = responses or {}
        self.call_count = 0
        self.last_prompt = None

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate mock response."""
        self.call_count += 1
        self.last_prompt = prompt

        # Check for specific responses
        for key, response in self.responses.items():
            if key in prompt:
                return response

        # Default response for agent decisions
        return """ACTION: explore
REASONING: Looking for resources and learning about the environment.
TARGET: none"""

    async def generate_streaming(self, prompt: str, system_prompt: Optional[str] = None):
        """Generate mock streaming response."""
        response = await self.generate(prompt, system_prompt)
        for word in response.split():
            yield word + " "

    def count_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text) // 4

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model


@pytest.fixture
def mock_llm_adapter():
    """Provide a mock LLM adapter."""
    return MockLLMAdapter()


@pytest.fixture
def mock_llm_adapter_with_responses():
    """Factory fixture for mock adapter with custom responses."""
    def _create_adapter(responses: Dict[str, str]) -> MockLLMAdapter:
        return MockLLMAdapter(responses=responses)
    return _create_adapter


# Agent State fixtures
@pytest.fixture
def sample_agent_state():
    """Create a sample agent state for testing."""
    from piano_architecture.agent_state import AgentState

    return AgentState(
        agent_id="test-agent-001",
        name="TestAgent",
        role=0,
        traits=["curious", "cooperative"]
    )


@pytest.fixture
def sample_observation():
    """Sample Malmo observation data."""
    return {
        'XPos': 10.5,
        'YPos': 64.0,
        'ZPos': -5.2,
        'Life': 18.0,
        'Food': 15.0,
        'inventory': [
            {'type': 'wooden_pickaxe', 'quantity': 1},
            {'type': 'dirt', 'quantity': 10}
        ],
        'entities': [
            {'name': 'Agent1', 'x': 12.0, 'y': 64.0, 'z': -3.0, 'distance': 2.5},
            {'name': 'Pig', 'x': 15.0, 'y': 64.0, 'z': 0.0, 'distance': 5.0}
        ]
    }


# Mission Builder fixtures
@pytest.fixture
def mission_builder():
    """Create a MissionBuilder instance."""
    from malmo_integration.mission_builder import MissionBuilder
    return MissionBuilder()


# Metrics Store fixtures
@pytest.fixture
def memory_metrics_store():
    """Create an in-memory metrics store for testing."""
    from benchmarking.metrics_store import MetricsStore
    return MetricsStore(use_memory=True)


# Test client fixtures
@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    from mcp_server.server import app
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """Create async FastAPI test client."""
    from httpx import AsyncClient, ASGITransport
    from mcp_server.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# Environment Manager fixtures
@pytest.fixture
def mock_malmo_env():
    """Create a mock MalmoEnv for testing."""
    mock = MagicMock()
    mock.reset.return_value = {
        'type': 'video',
        'pixels': None,
        'XPos': 0.0,
        'YPos': 4.0,
        'ZPos': 0.0,
        'Life': 20.0,
        'Food': 20.0
    }
    mock.step.return_value = (
        {'XPos': 1.0, 'YPos': 4.0, 'ZPos': 0.0, 'Life': 20.0, 'Food': 20.0},
        0.0,
        False,
        {}
    )
    return mock


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Any cleanup code goes here


# Skip markers
skip_requires_api_key = pytest.mark.skipif(
    not os.getenv('GOOGLE_API_KEY'),
    reason="Requires GOOGLE_API_KEY environment variable"
)

skip_requires_malmo = pytest.mark.skipif(
    True,  # Skip by default as Malmo may not be running
    reason="Requires Malmo server to be running"
)
