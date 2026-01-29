"""
Tests for Environment Manager.

Tests cover:
- Connection to Malmo (mocked)
- Observation processing
- Action translation
- Agent control loop
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEnvironmentManagerInit:
    """Test Environment Manager initialization."""

    def test_init(self):
        """Test initialization with mission XML."""
        from malmo_integration.environment_manager import MalmoEnvironmentManager

        manager = MalmoEnvironmentManager(
            mission_xml="<Mission></Mission>",
            port=9000
        )

        assert manager.mission_xml == "<Mission></Mission>"
        assert manager.port == 9000
        assert manager.env is None


class TestObservationProcessing:
    """Test observation processing."""

    @pytest.fixture
    def env_manager(self):
        """Create environment manager."""
        from malmo_integration.environment_manager import MalmoEnvironmentManager
        return MalmoEnvironmentManager(
            mission_xml="<Mission></Mission>",
            port=9000
        )

    def test_process_pixel_observation(self, env_manager):
        """Test processing pixel-based observation."""
        # Create mock pixel observation
        pixels = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)

        result = env_manager._process_observation(pixels)

        assert result['type'] == 'video'
        assert 'shape' in result
        assert result['shape'] == (240, 320, 3)

    def test_process_unknown_observation(self, env_manager):
        """Test processing unknown observation type."""
        result = env_manager._process_observation("unknown data")

        assert result['type'] == 'unknown'
        assert 'data' in result


class TestActionTranslation:
    """Test action translation to Malmo commands."""

    @pytest.fixture
    def env_manager(self):
        """Create environment manager."""
        from malmo_integration.environment_manager import MalmoEnvironmentManager
        return MalmoEnvironmentManager(
            mission_xml="<Mission></Mission>",
            port=9000
        )

    def test_translate_explore(self, env_manager):
        """Test translating explore action."""
        result = env_manager._action_to_malmo_command("explore")
        assert result == "move 1"

    def test_translate_forward(self, env_manager):
        """Test translating forward action."""
        result = env_manager._action_to_malmo_command("move forward")
        assert result == "move 1"

    def test_translate_back(self, env_manager):
        """Test translating back action."""
        result = env_manager._action_to_malmo_command("retreat")
        assert result == "move -1"

    def test_translate_turn_left(self, env_manager):
        """Test translating turn left action."""
        result = env_manager._action_to_malmo_command("turn left")
        assert result == "turn -1"

    def test_translate_turn_right(self, env_manager):
        """Test translating turn right action."""
        result = env_manager._action_to_malmo_command("turn right")
        assert result == "turn 1"

    def test_translate_jump(self, env_manager):
        """Test translating jump action."""
        result = env_manager._action_to_malmo_command("jump over obstacle")
        assert result == "jump 1"

    def test_translate_attack(self, env_manager):
        """Test translating attack action."""
        result = env_manager._action_to_malmo_command("attack enemy")
        assert result == "attack 1"

    def test_translate_use(self, env_manager):
        """Test translating use/interact action."""
        result = env_manager._action_to_malmo_command("use item")
        assert result == "use 1"

        result = env_manager._action_to_malmo_command("interact with door")
        assert result == "use 1"

    def test_translate_unknown_defaults_to_forward(self, env_manager):
        """Test that unknown actions default to moving forward."""
        result = env_manager._action_to_malmo_command("do something weird")
        assert result == "move 1"


class TestMalmoConnection:
    """Test Malmo connection (mocked)."""

    @pytest.fixture
    def env_manager_with_mock(self, mock_malmo_env):
        """Create environment manager with mocked Malmo."""
        from malmo_integration.environment_manager import MalmoEnvironmentManager

        manager = MalmoEnvironmentManager(
            mission_xml="<Mission></Mission>",
            port=9000
        )
        manager.env = mock_malmo_env
        return manager

    def test_reset(self, env_manager_with_mock):
        """Test environment reset."""
        result = env_manager_with_mock.reset()

        env_manager_with_mock.env.reset.assert_called_once()
        assert 'XPos' in result or 'type' in result

    def test_step(self, env_manager_with_mock):
        """Test environment step."""
        obs, reward, done = env_manager_with_mock.step("move 1")

        env_manager_with_mock.env.step.assert_called_once_with("move 1")
        assert isinstance(reward, float)
        assert isinstance(done, bool)

    def test_close(self, env_manager_with_mock, mock_malmo_env):
        """Test environment close."""
        # Store reference before close sets it to None
        env_ref = env_manager_with_mock.env
        env_manager_with_mock.close()

        env_ref.close.assert_called_once()
        assert env_manager_with_mock.env is None


class TestEnvironmentManagerErrors:
    """Test error handling."""

    def test_reset_without_connection(self):
        """Test reset fails without connection."""
        from malmo_integration.environment_manager import MalmoEnvironmentManager

        manager = MalmoEnvironmentManager(
            mission_xml="<Mission></Mission>",
            port=9000
        )

        with pytest.raises(RuntimeError) as exc_info:
            manager.reset()

        assert "not connected" in str(exc_info.value).lower()

    def test_step_without_connection(self):
        """Test step fails without connection."""
        from malmo_integration.environment_manager import MalmoEnvironmentManager

        manager = MalmoEnvironmentManager(
            mission_xml="<Mission></Mission>",
            port=9000
        )

        with pytest.raises(RuntimeError) as exc_info:
            manager.step("move 1")

        assert "not connected" in str(exc_info.value).lower()


class TestAgentControlLoop:
    """Test agent control loop (with mocks)."""

    @pytest.mark.asyncio
    async def test_control_loop_short_run(self, sample_agent_state, mock_malmo_env):
        """Test control loop runs for a few steps."""
        from malmo_integration.environment_manager import MalmoEnvironmentManager
        from unittest.mock import MagicMock

        manager = MalmoEnvironmentManager(
            mission_xml="<Mission></Mission>",
            port=9000
        )
        manager.env = mock_malmo_env

        # Set up a decision for the agent
        sample_agent_state.bottleneck_decision = {
            'action': 'explore',
            'reasoning': 'Looking around',
            'target': 'none'
        }

        # Create mock agent manager
        mock_agent_manager = MagicMock()

        # Run for just a couple steps
        manager.running = True

        # Use a short timeout to test a few iterations
        async def stop_after_delay():
            await asyncio.sleep(0.5)
            manager.stop()

        # Run both concurrently
        await asyncio.gather(
            manager.run_agent_loop(
                sample_agent_state,
                mock_agent_manager,
                "test-agent-001",
                max_steps=3
            ),
            stop_after_delay()
        )

        # Verify it ran
        assert not manager.running
