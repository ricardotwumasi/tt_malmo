"""
Social Awareness Module - Tracks other agents and social relationships.

This module maintains social models of other agents and tracks
relationships, roles, and social dynamics.
"""

from typing import Dict, Any, List
from datetime import datetime
from .base_module import Module
from ..agent_state import AgentState


class SocialAwarenessModule(Module):
    """
    Social Awareness Module - Social cognition and relationships.

    Tracks:
    - Nearby agents and their activities
    - Relationship strengths
    - Perceived roles of other agents
    - Social interactions and patterns
    """

    def __init__(self, update_interval: float = 2.0):
        """
        Initialize Social Awareness module.

        Args:
            update_interval: Time between social awareness updates
        """
        super().__init__(name='social_awareness', update_interval=update_interval)

        # Track agent interaction history
        self.interaction_history: Dict[str, List[Dict[str, Any]]] = {}

        # Track observed activities of other agents
        self.agent_activities: Dict[str, List[str]] = {}

    async def process(self, agent_state: AgentState) -> Dict[str, Any]:
        """
        Process social information and update relationships.

        Args:
            agent_state: Current agent state

        Returns:
            Social awareness output
        """
        nearby_agents = agent_state.nearby_agents

        if not nearby_agents:
            return {
                'social_summary': 'No agents nearby',
                'interactions': [],
                'relationship_updates': []
            }

        # Process nearby agents
        interactions = []
        relationship_updates = []

        for other_agent in nearby_agents:
            agent_name = other_agent.get('name', 'Unknown')
            distance = other_agent.get('distance', 999)

            # Determine interaction type based on distance
            interaction_type = self._classify_interaction(distance)

            if interaction_type != 'none':
                interaction = {
                    'agent': agent_name,
                    'type': interaction_type,
                    'distance': distance,
                    'timestamp': datetime.now().isoformat()
                }
                interactions.append(interaction)

                # Update interaction history
                if agent_name not in self.interaction_history:
                    self.interaction_history[agent_name] = []
                self.interaction_history[agent_name].append(interaction)

                # Keep only recent history (last 20 interactions)
                if len(self.interaction_history[agent_name]) > 20:
                    self.interaction_history[agent_name].pop(0)

            # Update relationship based on interaction frequency
            relationship_change = self._compute_relationship_change(
                agent_name,
                interaction_type,
                distance
            )

            if relationship_change != 0:
                current_relationship = agent_state.relationships.get(agent_name, 0.0)
                new_relationship = max(-1.0, min(1.0, current_relationship + relationship_change))

                # Update relationship in agent state
                relationships = agent_state.relationships.copy()
                relationships[agent_name] = new_relationship
                agent_state.update_safely('relationships', relationships)

                relationship_updates.append({
                    'agent': agent_name,
                    'old_value': current_relationship,
                    'new_value': new_relationship,
                    'change': relationship_change
                })

            # Infer role of other agent
            self._infer_agent_role(agent_name, other_agent, agent_state)

        # Create social summary
        social_summary = self._create_social_summary(nearby_agents, agent_state)

        return {
            'social_summary': social_summary,
            'interactions': interactions,
            'relationship_updates': relationship_updates,
            'nearby_agent_count': len(nearby_agents)
        }

    def _classify_interaction(self, distance: float) -> str:
        """
        Classify interaction type based on distance.

        Args:
            distance: Distance to other agent

        Returns:
            Interaction type: 'close', 'nearby', 'distant', or 'none'
        """
        if distance < 3:
            return 'close'  # Close interaction (can collaborate)
        elif distance < 10:
            return 'nearby'  # Nearby (aware of each other)
        elif distance < 20:
            return 'distant'  # Distant (visible but far)
        else:
            return 'none'  # Too far

    def _compute_relationship_change(self, agent_name: str,
                                    interaction_type: str,
                                    distance: float) -> float:
        """
        Compute relationship change based on interaction.

        Args:
            agent_name: Name of other agent
            interaction_type: Type of interaction
            distance: Distance to other agent

        Returns:
            Relationship change (positive or negative)
        """
        if interaction_type == 'close':
            # Close interactions strengthen relationship
            return 0.02
        elif interaction_type == 'nearby':
            # Nearby interactions slightly strengthen relationship
            return 0.01
        elif interaction_type == 'distant':
            # Distant interactions have minimal effect
            return 0.005
        else:
            # No interaction - relationship slowly decays
            return -0.001

    def _infer_agent_role(self, agent_name: str,
                         agent_data: Dict[str, Any],
                         agent_state: AgentState) -> None:
        """
        Infer the role of another agent based on observations.

        This is a simple heuristic system. In full PIANO, this would use
        LLM inference over observed activities.

        Args:
            agent_name: Name of other agent
            agent_data: Observation data about agent
            agent_state: Current agent state
        """
        # Track activities we observe
        if agent_name not in self.agent_activities:
            self.agent_activities[agent_name] = []

        # Simple heuristic: infer role from location patterns
        # In full implementation, would track inventory, movement patterns, etc.

        # For now, just track that we've seen this agent
        perceived_role = "unknown"  # Default role

        # Update perceived roles in agent state
        perceived_roles = agent_state.perceived_roles.copy()
        perceived_roles[agent_name] = perceived_role
        agent_state.update_safely('perceived_roles', perceived_roles)

    def _create_social_summary(self, nearby_agents: List[Dict[str, Any]],
                              agent_state: AgentState) -> str:
        """
        Create human-readable social summary.

        Args:
            nearby_agents: List of nearby agents
            agent_state: Current agent state

        Returns:
            Social summary string
        """
        if not nearby_agents:
            return "No agents nearby"

        count = len(nearby_agents)
        closest = nearby_agents[0] if nearby_agents else None
        closest_name = closest.get('name', 'Unknown') if closest else 'Unknown'
        closest_distance = closest.get('distance', 999) if closest else 999

        # Count friendly relationships
        friendly_count = sum(1 for v in agent_state.relationships.values() if v > 0.5)

        summary = f"{count} agents nearby. Closest: {closest_name} ({closest_distance:.1f}m)"

        if friendly_count > 0:
            summary += f". {friendly_count} friendly relationships"

        return summary
