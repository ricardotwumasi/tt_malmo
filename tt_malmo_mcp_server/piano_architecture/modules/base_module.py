"""
Base Module - Abstract base class for all PIANO modules.

All 10 concurrent modules inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio

from ..agent_state import AgentState


class Module(ABC):
    """
    Abstract base class for PIANO modules.

    Each module runs concurrently and processes specific aspects of
    agent cognition.
    """

    def __init__(self, name: str, update_interval: float = 1.0):
        """
        Initialize module.

        Args:
            name: Module name
            update_interval: Time between module updates in seconds
        """
        self.name = name
        self.update_interval = update_interval
        self.running = False

    @abstractmethod
    async def process(self, agent_state: AgentState) -> Dict[str, Any]:
        """
        Process module logic.

        Args:
            agent_state: Current agent state

        Returns:
            Module output dictionary
        """
        pass

    async def run(self, agent_state: AgentState):
        """
        Run module processing loop.

        Args:
            agent_state: Agent state to monitor and update
        """
        self.running = True
        while self.running:
            try:
                # Process module logic
                output = await self.process(agent_state)

                # Store output in agent state
                agent_state.set_module_output(self.name, output)

                # Wait for next update
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                print(f"Error in {self.name} module: {e}")
                await asyncio.sleep(1.0)

    def stop(self):
        """Stop module processing loop."""
        self.running = False
