"""
Agent State - Shared state across all PIANO modules.

This is the brain-inspired shared state that all 10 concurrent modules
read from and write to. Thread-safe operations are critical.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from threading import Lock
from datetime import datetime
import json


@dataclass
class AgentState:
    """
    Shared state across all PIANO modules.

    This represents the agent's complete mental state including:
    - Identity (name, role, traits)
    - Multi-timescale memory systems
    - Current observations and world state
    - Social relationships and perceptions
    - Goals and intentions
    - Bottleneck decisions from Cognitive Controller
    """

    # Identity
    agent_id: str
    name: str
    role: int  # Malmo role number (0, 1, 2, ...)
    traits: List[str] = field(default_factory=list)

    # Memory systems (multi-timescale like human brain)
    working_memory: List[Dict[str, Any]] = field(default_factory=list)  # Last few seconds
    short_term_memory: List[Dict[str, Any]] = field(default_factory=list)  # Last few minutes
    long_term_memory: List[Dict[str, Any]] = field(default_factory=list)  # Persistent experiences

    # Current state
    current_observation: Optional[Dict[str, Any]] = None
    current_location: Optional[Dict[str, float]] = None  # {x, y, z}
    current_inventory: List[Dict[str, Any]] = field(default_factory=list)
    current_health: float = 20.0
    current_hunger: float = 20.0

    # Social state
    nearby_agents: List[Dict[str, Any]] = field(default_factory=list)
    relationships: Dict[str, float] = field(default_factory=dict)  # agent_id -> relationship score
    perceived_roles: Dict[str, str] = field(default_factory=dict)  # agent_id -> perceived role

    # Goals and intentions
    current_goals: List[Dict[str, Any]] = field(default_factory=list)
    goal_history: List[Dict[str, Any]] = field(default_factory=list)

    # Bottleneck decision (from Cognitive Controller)
    bottleneck_decision: Optional[Dict[str, Any]] = None
    last_bottleneck_update: Optional[datetime] = None

    # Module communication channels
    module_outputs: Dict[str, Any] = field(default_factory=dict)

    # Action tracking (for Action Awareness module)
    expected_outcome: Optional[Dict[str, Any]] = None
    last_action: Optional[Dict[str, Any]] = None
    action_success_rate: float = 1.0

    # Thread safety
    lock: Lock = field(default_factory=Lock, repr=False)

    def update_safely(self, key: str, value: Any) -> None:
        """
        Thread-safe update of a single attribute.

        Args:
            key: Attribute name to update
            value: New value
        """
        with self.lock:
            setattr(self, key, value)

    def update_multiple_safely(self, updates: Dict[str, Any]) -> None:
        """
        Thread-safe update of multiple attributes at once.

        Args:
            updates: Dictionary of {attribute_name: new_value}
        """
        with self.lock:
            for key, value in updates.items():
                setattr(self, key, value)

    def add_to_memory(self, memory_type: str, item: Dict[str, Any]) -> None:
        """
        Thread-safe addition to memory systems.

        Args:
            memory_type: One of 'working', 'short_term', 'long_term'
            item: Memory item with timestamp
        """
        item['timestamp'] = datetime.now().isoformat()

        with self.lock:
            if memory_type == 'working':
                self.working_memory.append(item)
                # Keep only last 5 items in working memory
                if len(self.working_memory) > 5:
                    self.working_memory.pop(0)
            elif memory_type == 'short_term':
                self.short_term_memory.append(item)
                # Keep only last 50 items in short-term memory
                if len(self.short_term_memory) > 50:
                    self.short_term_memory.pop(0)
            elif memory_type == 'long_term':
                self.long_term_memory.append(item)
                # Long-term memory has no size limit

    def update_observation(self, observation: Dict[str, Any]) -> None:
        """
        Update current observation and derived state.

        Args:
            observation: Raw observation from Malmo
        """
        with self.lock:
            self.current_observation = observation

            # Extract location if available
            if 'XPos' in observation and 'YPos' in observation and 'ZPos' in observation:
                self.current_location = {
                    'x': observation['XPos'],
                    'y': observation['YPos'],
                    'z': observation['ZPos']
                }

            # Extract health/hunger
            if 'Life' in observation:
                self.current_health = observation['Life']
            if 'Food' in observation:
                self.current_hunger = observation['Food']

            # Extract inventory
            if 'inventory' in observation:
                self.current_inventory = observation['inventory']

            # Extract nearby agents
            if 'entities' in observation:
                self.nearby_agents = [
                    e for e in observation['entities']
                    if e.get('name', '').startswith('Agent')
                ]

    def set_bottleneck_decision(self, decision: Dict[str, Any]) -> None:
        """
        Update the bottleneck decision from Cognitive Controller.

        Args:
            decision: Decision dictionary from Cognitive Controller
        """
        with self.lock:
            self.bottleneck_decision = decision
            self.last_bottleneck_update = datetime.now()

    def get_module_output(self, module_name: str) -> Optional[Any]:
        """
        Thread-safe retrieval of module output.

        Args:
            module_name: Name of the module

        Returns:
            Module output or None if not available
        """
        with self.lock:
            return self.module_outputs.get(module_name)

    def set_module_output(self, module_name: str, output: Any) -> None:
        """
        Thread-safe storage of module output.

        Args:
            module_name: Name of the module
            output: Output to store
        """
        with self.lock:
            self.module_outputs[module_name] = {
                'output': output,
                'timestamp': datetime.now().isoformat()
            }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert agent state to dictionary (for serialization).
        Thread-safe.

        Returns:
            Dictionary representation of agent state
        """
        with self.lock:
            return {
                'agent_id': self.agent_id,
                'name': self.name,
                'role': self.role,
                'traits': self.traits,
                'current_location': self.current_location,
                'current_health': self.current_health,
                'current_hunger': self.current_hunger,
                'current_goals': self.current_goals,
                'nearby_agents': [a.get('name', 'Unknown') for a in self.nearby_agents],
                'bottleneck_decision': self.bottleneck_decision,
                'action_success_rate': self.action_success_rate
            }

    def __repr__(self) -> str:
        """Human-readable representation."""
        return (
            f"AgentState(agent_id={self.agent_id}, name={self.name}, "
            f"role={self.role}, location={self.current_location}, "
            f"health={self.current_health:.1f}, goals={len(self.current_goals)})"
        )
