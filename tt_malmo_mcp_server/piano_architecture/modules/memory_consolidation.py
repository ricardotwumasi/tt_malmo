"""
Memory Consolidation Module - Manages multi-timescale memory systems.

This module handles:
- Working memory (seconds) -> Short-term memory (minutes)
- Short-term memory -> Long-term memory (persistent)
- Memory retrieval and importance scoring
- Forgetting of low-importance memories
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base_module import Module
from ..agent_state import AgentState


class MemoryConsolidationModule(Module):
    """
    Memory Consolidation Module - Multi-timescale memory management.

    Implements brain-like memory consolidation:
    - Working memory: Last 5-10 seconds (5 items max)
    - Short-term memory: Last few minutes (50 items max)
    - Long-term memory: Persistent (important experiences)
    """

    def __init__(self, update_interval: float = 10.0):
        """
        Initialize Memory Consolidation module.

        Args:
            update_interval: Time between consolidation cycles
        """
        super().__init__(name='memory_consolidation', update_interval=update_interval)

        # Consolidation thresholds
        self.working_to_short_term_threshold = 0.3  # Minimum importance to move to short-term
        self.short_term_to_long_term_threshold = 0.6  # Minimum importance to move to long-term

        # Time thresholds
        self.working_memory_decay_seconds = 30  # Working memories decay after 30s
        self.short_term_decay_minutes = 10  # Short-term memories decay after 10 min

    async def process(self, agent_state: AgentState) -> Dict[str, Any]:
        """
        Consolidate memories across timescales.

        Args:
            agent_state: Current agent state

        Returns:
            Consolidation output with statistics
        """
        # Consolidate working -> short-term
        working_consolidated = self._consolidate_working_to_short_term(agent_state)

        # Consolidate short-term -> long-term
        short_term_consolidated = self._consolidate_short_term_to_long_term(agent_state)

        # Decay old memories
        working_decayed = self._decay_working_memory(agent_state)
        short_term_decayed = self._decay_short_term_memory(agent_state)

        # Find most important recent memory
        key_memory = self._extract_key_memory(agent_state)

        return {
            'working_consolidated': working_consolidated,
            'short_term_consolidated': short_term_consolidated,
            'working_decayed': working_decayed,
            'short_term_decayed': short_term_decayed,
            'key_memory': key_memory,
            'memory_stats': {
                'working': len(agent_state.working_memory),
                'short_term': len(agent_state.short_term_memory),
                'long_term': len(agent_state.long_term_memory)
            }
        }

    def _consolidate_working_to_short_term(self, agent_state: AgentState) -> int:
        """
        Move important working memories to short-term memory.

        Args:
            agent_state: Current agent state

        Returns:
            Number of memories consolidated
        """
        consolidated_count = 0

        with agent_state.lock:
            for memory in agent_state.working_memory:
                importance = self._compute_importance(memory, agent_state)

                if importance >= self.working_to_short_term_threshold:
                    # Add to short-term memory
                    memory['importance'] = importance
                    agent_state.short_term_memory.append(memory)
                    consolidated_count += 1

            # Keep only last 50 items in short-term memory
            if len(agent_state.short_term_memory) > 50:
                # Remove least important memories
                agent_state.short_term_memory.sort(
                    key=lambda m: m.get('importance', 0),
                    reverse=True
                )
                agent_state.short_term_memory = agent_state.short_term_memory[:50]

        return consolidated_count

    def _consolidate_short_term_to_long_term(self, agent_state: AgentState) -> int:
        """
        Move highly important short-term memories to long-term memory.

        Args:
            agent_state: Current agent state

        Returns:
            Number of memories consolidated
        """
        consolidated_count = 0

        with agent_state.lock:
            for memory in agent_state.short_term_memory:
                importance = memory.get('importance', 0)

                if importance >= self.short_term_to_long_term_threshold:
                    # Check if not already in long-term memory (avoid duplicates)
                    if not self._is_in_long_term(memory, agent_state):
                        agent_state.long_term_memory.append(memory)
                        consolidated_count += 1

        return consolidated_count

    def _decay_working_memory(self, agent_state: AgentState) -> int:
        """
        Remove old working memories.

        Args:
            agent_state: Current agent state

        Returns:
            Number of memories removed
        """
        now = datetime.now()
        decay_threshold = now - timedelta(seconds=self.working_memory_decay_seconds)

        with agent_state.lock:
            original_count = len(agent_state.working_memory)

            agent_state.working_memory = [
                m for m in agent_state.working_memory
                if self._parse_timestamp(m.get('timestamp', '')) > decay_threshold
            ]

            decayed_count = original_count - len(agent_state.working_memory)

        return decayed_count

    def _decay_short_term_memory(self, agent_state: AgentState) -> int:
        """
        Remove old short-term memories.

        Args:
            agent_state: Current agent state

        Returns:
            Number of memories removed
        """
        now = datetime.now()
        decay_threshold = now - timedelta(minutes=self.short_term_decay_minutes)

        with agent_state.lock:
            original_count = len(agent_state.short_term_memory)

            agent_state.short_term_memory = [
                m for m in agent_state.short_term_memory
                if self._parse_timestamp(m.get('timestamp', '')) > decay_threshold
            ]

            decayed_count = original_count - len(agent_state.short_term_memory)

        return decayed_count

    def _compute_importance(self, memory: Dict[str, Any], agent_state: AgentState) -> float:
        """
        Compute importance score for a memory.

        Importance factors:
        - Emotional salience (danger, achievement, social)
        - Relevance to current goals
        - Novelty (how different from recent memories)

        Args:
            memory: Memory dictionary
            agent_state: Current agent state

        Returns:
            Importance score (0.0 to 1.0)
        """
        importance = 0.0

        memory_type = memory.get('type', 'unknown')

        # High importance for survival events
        if memory_type in ['damage_taken', 'near_death', 'action_failure']:
            importance += 0.8

        # Medium importance for achievements
        if memory_type in ['item_acquired', 'goal_completed', 'new_agent_met']:
            importance += 0.5

        # Low importance for routine events
        if memory_type in ['movement', 'observation', 'routine']:
            importance += 0.2

        # Boost importance if related to current goals
        if agent_state.current_goals:
            for goal in agent_state.current_goals:
                goal_desc = goal.get('description', '').lower()
                memory_event = memory.get('event', '').lower()

                # Simple keyword overlap check
                goal_words = set(goal_desc.split())
                memory_words = set(memory_event.split())
                overlap = len(goal_words & memory_words)

                if overlap > 0:
                    importance += 0.2 * min(overlap, 2)  # Max +0.4 boost

        # Cap at 1.0
        return min(1.0, importance)

    def _is_in_long_term(self, memory: Dict[str, Any], agent_state: AgentState) -> bool:
        """
        Check if memory is already in long-term memory.

        Args:
            memory: Memory to check
            agent_state: Current agent state

        Returns:
            True if already in long-term memory
        """
        memory_event = memory.get('event', '')
        memory_timestamp = memory.get('timestamp', '')

        for ltm in agent_state.long_term_memory:
            if (ltm.get('event') == memory_event and
                ltm.get('timestamp') == memory_timestamp):
                return True

        return False

    def _extract_key_memory(self, agent_state: AgentState) -> str:
        """
        Extract the most important recent memory.

        Args:
            agent_state: Current agent state

        Returns:
            Description of key memory
        """
        # Check short-term memory for highest importance
        if agent_state.short_term_memory:
            # Sort by importance
            sorted_memories = sorted(
                agent_state.short_term_memory,
                key=lambda m: m.get('importance', 0),
                reverse=True
            )

            if sorted_memories:
                key_mem = sorted_memories[0]
                return key_mem.get('event', 'No significant event')

        # Fallback to working memory
        if agent_state.working_memory:
            return agent_state.working_memory[-1].get('event', 'Recent observation')

        return "No recent memories"

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO timestamp string.

        Args:
            timestamp_str: ISO format timestamp

        Returns:
            datetime object
        """
        try:
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            # Return very old time if parsing fails
            return datetime(2000, 1, 1)
