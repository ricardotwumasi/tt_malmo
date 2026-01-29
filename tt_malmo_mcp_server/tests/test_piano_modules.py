"""
Tests for PIANO Architecture modules.

Tests cover:
- AgentState operations
- CognitiveController bottleneck
- Individual module processing
- Module coordination
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAgentState:
    """Test AgentState operations."""

    def test_init(self, sample_agent_state):
        """Test AgentState initialization."""
        state = sample_agent_state

        assert state.agent_id == "test-agent-001"
        assert state.name == "TestAgent"
        assert state.role == 0
        assert "curious" in state.traits
        assert state.current_health == 20.0

    def test_update_safely(self, sample_agent_state):
        """Test thread-safe single value update."""
        state = sample_agent_state

        state.update_safely('current_health', 15.0)

        assert state.current_health == 15.0

    def test_update_multiple_safely(self, sample_agent_state):
        """Test thread-safe multiple value update."""
        state = sample_agent_state

        state.update_multiple_safely({
            'current_health': 12.0,
            'current_hunger': 8.0
        })

        assert state.current_health == 12.0
        assert state.current_hunger == 8.0

    def test_add_to_working_memory(self, sample_agent_state):
        """Test adding items to working memory."""
        state = sample_agent_state

        state.add_to_memory('working', {'event': 'Saw a tree'})
        state.add_to_memory('working', {'event': 'Found water'})

        assert len(state.working_memory) == 2
        assert 'timestamp' in state.working_memory[0]

    def test_working_memory_limit(self, sample_agent_state):
        """Test that working memory respects size limit."""
        state = sample_agent_state

        # Add more than limit (5)
        for i in range(10):
            state.add_to_memory('working', {'event': f'Event {i}'})

        assert len(state.working_memory) == 5
        # Should have most recent events
        assert state.working_memory[-1]['event'] == 'Event 9'

    def test_update_observation(self, sample_agent_state, sample_observation):
        """Test observation update extracts relevant data."""
        state = sample_agent_state

        state.update_observation(sample_observation)

        assert state.current_location == {'x': 10.5, 'y': 64.0, 'z': -5.2}
        assert state.current_health == 18.0
        assert state.current_hunger == 15.0
        assert len(state.current_inventory) == 2
        assert len(state.nearby_agents) == 1  # Only Agent1, not Pig

    def test_set_bottleneck_decision(self, sample_agent_state):
        """Test setting bottleneck decision."""
        state = sample_agent_state

        decision = {
            'action': 'explore',
            'reasoning': 'Looking for resources',
            'target': 'none'
        }

        state.set_bottleneck_decision(decision)

        assert state.bottleneck_decision == decision
        assert state.last_bottleneck_update is not None

    def test_to_dict(self, sample_agent_state):
        """Test serialization to dictionary."""
        state = sample_agent_state

        data = state.to_dict()

        assert data['agent_id'] == "test-agent-001"
        assert data['name'] == "TestAgent"
        assert 'current_health' in data


class TestCognitiveController:
    """Test CognitiveController bottleneck operations."""

    @pytest.fixture
    def controller(self, mock_llm_adapter):
        """Create CognitiveController with mock LLM."""
        from piano_architecture.cognitive_controller import CognitiveController
        return CognitiveController(mock_llm_adapter, decision_interval=1.0)

    @pytest.mark.asyncio
    async def test_make_decision(self, controller, sample_agent_state):
        """Test decision making."""
        decision = await controller.make_decision(sample_agent_state)

        assert 'action' in decision
        assert 'reasoning' in decision
        assert 'target' in decision
        assert 'timestamp' in decision
        assert decision['agent_id'] == sample_agent_state.agent_id

    def test_apply_bottleneck(self, controller, sample_agent_state, sample_observation):
        """Test information bottleneck filtering."""
        sample_agent_state.update_observation(sample_observation)

        filtered = controller._apply_bottleneck(sample_agent_state)

        assert 'agent_identity' in filtered
        assert 'current_state' in filtered
        assert filtered['agent_identity']['name'] == 'TestAgent'
        assert filtered['current_state']['health'] == 18.0

    def test_parse_decision_success(self, controller, sample_agent_state):
        """Test successful decision parsing."""
        decision_text = """ACTION: gather
REASONING: Need resources to survive
TARGET: nearby_tree"""

        decision = controller._parse_decision(decision_text, sample_agent_state)

        assert decision['action'] == 'gather'
        assert 'resources' in decision['reasoning']
        assert decision['target'] == 'nearby_tree'

    def test_parse_decision_fallback(self, controller, sample_agent_state):
        """Test decision parsing fallback for malformed input."""
        decision_text = "Just some random text without proper format"

        decision = controller._parse_decision(decision_text, sample_agent_state)

        # Should use defaults
        assert decision['action'] == 'explore'


class TestPerceptionModule:
    """Test Perception module."""

    @pytest.fixture
    def perception_module(self):
        """Create Perception module."""
        from piano_architecture.modules import PerceptionModule
        return PerceptionModule(update_interval=0.1)

    @pytest.mark.asyncio
    async def test_process(self, perception_module, sample_agent_state, sample_observation):
        """Test perception processing."""
        sample_agent_state.update_observation(sample_observation)

        output = await perception_module.process(sample_agent_state)

        assert 'salient_feature' in output or output is not None


class TestSocialAwarenessModule:
    """Test Social Awareness module."""

    @pytest.fixture
    def social_module(self):
        """Create Social Awareness module."""
        from piano_architecture.modules import SocialAwarenessModule
        return SocialAwarenessModule(update_interval=0.1)

    @pytest.mark.asyncio
    async def test_process_with_agents(self, social_module, sample_agent_state, sample_observation):
        """Test social awareness with nearby agents."""
        sample_agent_state.update_observation(sample_observation)

        output = await social_module.process(sample_agent_state)

        assert output is not None


class TestGoalGenerationModule:
    """Test Goal Generation module."""

    @pytest.fixture
    def goal_module(self, mock_llm_adapter):
        """Create Goal Generation module."""
        from piano_architecture.modules import GoalGenerationModule
        return GoalGenerationModule(mock_llm_adapter, update_interval=0.1)

    @pytest.mark.asyncio
    async def test_process(self, goal_module, sample_agent_state):
        """Test goal generation."""
        output = await goal_module.process(sample_agent_state)

        assert output is not None


class TestActionAwarenessModule:
    """Test Action Awareness module."""

    @pytest.fixture
    def action_module(self):
        """Create Action Awareness module."""
        from piano_architecture.modules import ActionAwarenessModule
        return ActionAwarenessModule(update_interval=0.1)

    @pytest.mark.asyncio
    async def test_process(self, action_module, sample_agent_state):
        """Test action awareness processing."""
        # Set a last action
        sample_agent_state.last_action = {
            'action': 'move forward',
            'success': True
        }

        output = await action_module.process(sample_agent_state)

        assert output is not None


class TestMemoryConsolidationModule:
    """Test Memory Consolidation module."""

    @pytest.fixture
    def memory_module(self):
        """Create Memory Consolidation module."""
        from piano_architecture.modules import MemoryConsolidationModule
        return MemoryConsolidationModule(update_interval=0.1)

    @pytest.mark.asyncio
    async def test_process(self, memory_module, sample_agent_state):
        """Test memory consolidation."""
        # Add some memories
        for i in range(3):
            sample_agent_state.add_to_memory('working', {'event': f'Event {i}'})

        output = await memory_module.process(sample_agent_state)

        assert output is not None


class TestModuleIntegration:
    """Test module integration."""

    @pytest.mark.asyncio
    async def test_module_output_flow(self, sample_agent_state, mock_llm_adapter):
        """Test that modules can share output through agent state."""
        from piano_architecture.modules import PerceptionModule

        module = PerceptionModule(update_interval=0.1)

        output = await module.process(sample_agent_state)
        sample_agent_state.set_module_output('perception', output)

        retrieved = sample_agent_state.get_module_output('perception')

        assert retrieved is not None
        assert 'timestamp' in retrieved
