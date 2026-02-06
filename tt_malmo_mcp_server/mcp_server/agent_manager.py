"""
Agent Manager - Manages agent lifecycle and PIANO architecture orchestration.

Responsible for:
- Creating and deleting agents
- Starting/stopping PIANO modules
- Coordinating observations and actions
- Managing agent state
"""

from typing import Dict, List, Optional, Any
import asyncio
import uuid
import os

from piano_architecture.agent_state import AgentState
from piano_architecture.cognitive_controller import CognitiveController
from piano_architecture.modules import (
    ActionAwarenessModule,
    PerceptionModule,
    SocialAwarenessModule,
    GoalGenerationModule,
    MemoryConsolidationModule
)
from llm_adapters import create_adapter, SUPPORTED_PROVIDERS


class AgentManager:
    """
    Manages all agents and their PIANO architectures.
    """

    def __init__(self):
        """Initialize Agent Manager."""
        self.agents: Dict[str, Dict[str, Any]] = {}  # agent_id -> agent data
        self.agent_states: Dict[str, AgentState] = {}  # agent_id -> AgentState
        self.agent_tasks: Dict[str, List[asyncio.Task]] = {}  # agent_id -> running tasks

        # Supported LLM providers
        self.supported_providers = SUPPORTED_PROVIDERS

    async def create_agent(self, name: str, llm_type: str = "gemini",
                          role: int = 0, traits: Optional[List[str]] = None,
                          model: Optional[str] = None) -> str:
        """
        Create a new agent with PIANO architecture.

        Args:
            name: Agent name
            llm_type: LLM provider type (gemini, claude, openrouter, cerebras, cloudflare)
            role: Malmo role number
            traits: Agent personality traits
            model: Optional specific model override

        Returns:
            Agent ID
        """
        # Generate agent ID
        agent_id = str(uuid.uuid4())

        # Validate LLM type
        if llm_type not in self.supported_providers:
            raise ValueError(
                f"Unknown LLM type: {llm_type}. "
                f"Supported types: {', '.join(self.supported_providers)}"
            )

        # Create LLM adapter using factory
        try:
            llm_adapter = create_adapter(
                llm_type=llm_type,
                model=model,
                max_tokens=512  # Shorter for faster agent responses
            )
        except ValueError as e:
            raise ValueError(f"Failed to create adapter for {llm_type}: {e}")

        # Create agent state
        if traits is None:
            traits = ["curious", "cooperative"]

        agent_state = AgentState(
            agent_id=agent_id,
            name=name,
            role=role,
            traits=traits
        )

        # Create PIANO modules
        perception = PerceptionModule(update_interval=0.5)
        social_awareness = SocialAwarenessModule(update_interval=2.0)
        goal_generation = GoalGenerationModule(llm_adapter, update_interval=7.0)
        action_awareness = ActionAwarenessModule(update_interval=0.5)
        memory_consolidation = MemoryConsolidationModule(update_interval=10.0)

        # Create Cognitive Controller
        cognitive_controller = CognitiveController(llm_adapter, decision_interval=5.0)

        # Give the cognitive controller access to all agent states
        # so it can include other agents' positions/actions in the prompt
        CognitiveController.set_agent_manager(self)

        # Store agent data
        self.agents[agent_id] = {
            'agent_id': agent_id,
            'name': name,
            'llm_type': llm_type,
            'role': role,
            'traits': traits,
            'status': 'created',
            'modules': {
                'perception': perception,
                'social_awareness': social_awareness,
                'goal_generation': goal_generation,
                'action_awareness': action_awareness,
                'memory_consolidation': memory_consolidation
            },
            'cognitive_controller': cognitive_controller,
            'llm_adapter': llm_adapter
        }

        self.agent_states[agent_id] = agent_state
        self.agent_tasks[agent_id] = []

        print(f"Created agent: {name} (ID: {agent_id}, LLM: {llm_type})")

        return agent_id

    async def start_agent(self, agent_id: str) -> bool:
        """
        Start agent's PIANO architecture.

        Args:
            agent_id: Agent ID

        Returns:
            True if started successfully
        """
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]
        agent_state = self.agent_states[agent_id]

        # Start all modules as concurrent tasks
        tasks = []

        for module_name, module in agent['modules'].items():
            task = asyncio.create_task(module.run(agent_state))
            tasks.append(task)

        # Start Cognitive Controller
        controller_task = asyncio.create_task(
            agent['cognitive_controller'].run_decision_loop(agent_state)
        )
        tasks.append(controller_task)

        # Store tasks
        self.agent_tasks[agent_id] = tasks

        # Update status
        agent['status'] = 'running'

        print(f"Started PIANO architecture for agent: {agent['name']}")

        return True

    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop agent's PIANO architecture.

        Args:
            agent_id: Agent ID

        Returns:
            True if stopped successfully
        """
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]

        # Stop all modules
        for module in agent['modules'].values():
            module.stop()

        # Cancel all tasks
        if agent_id in self.agent_tasks:
            for task in self.agent_tasks[agent_id]:
                task.cancel()

            # Wait for tasks to finish
            await asyncio.gather(*self.agent_tasks[agent_id], return_exceptions=True)

            self.agent_tasks[agent_id] = []

        # Update status
        agent['status'] = 'stopped'

        print(f"Stopped PIANO architecture for agent: {agent['name']}")

        return True

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: Agent ID

        Returns:
            True if deleted successfully
        """
        if agent_id not in self.agents:
            return False

        # Stop agent first
        await self.stop_agent(agent_id)

        # Remove from storage
        agent_name = self.agents[agent_id]['name']
        del self.agents[agent_id]
        del self.agent_states[agent_id]
        del self.agent_tasks[agent_id]

        print(f"Deleted agent: {agent_name}")

        return True

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent data.

        Args:
            agent_id: Agent ID

        Returns:
            Agent data dictionary or None
        """
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all agents.

        Returns:
            List of agent data dictionaries
        """
        return [
            {
                'agent_id': agent_id,
                'name': agent['name'],
                'llm_type': agent['llm_type'],
                'role': agent['role'],
                'status': agent['status']
            }
            for agent_id, agent in self.agents.items()
        ]

    async def process_observation(self, agent_id: str, observation: Dict[str, Any]) -> None:
        """
        Process observation from Malmo for an agent.

        Args:
            agent_id: Agent ID
            observation: Observation dictionary from Malmo
        """
        if agent_id not in self.agent_states:
            return

        agent_state = self.agent_states[agent_id]

        # Update agent state with observation
        agent_state.update_observation(observation)

        # Add to working memory
        agent_state.add_to_memory('working', {
            'type': 'observation',
            'event': 'Received environment observation'
        })

    async def process_action_result(self, agent_id: str, action: str, success: bool) -> None:
        """
        Process action result for an agent.

        Args:
            agent_id: Agent ID
            action: Action that was executed
            success: Whether action succeeded
        """
        if agent_id not in self.agent_states:
            return

        agent_state = self.agent_states[agent_id]

        # Update last action
        agent_state.update_safely('last_action', {
            'action': action,
            'success': success
        })

        # Add to working memory
        agent_state.add_to_memory('working', {
            'type': 'action_result',
            'event': f"Action '{action}' {'succeeded' if success else 'failed'}"
        })

    async def get_agent_decision(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get latest decision from agent's Cognitive Controller.

        Args:
            agent_id: Agent ID

        Returns:
            Decision dictionary or None
        """
        if agent_id not in self.agent_states:
            return None

        agent_state = self.agent_states[agent_id]
        return agent_state.bottleneck_decision

    def get_agent_state_summary(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary of agent state for monitoring.

        Args:
            agent_id: Agent ID

        Returns:
            Agent state summary or None
        """
        if agent_id not in self.agent_states:
            return None

        agent_state = self.agent_states[agent_id]
        return agent_state.to_dict()
