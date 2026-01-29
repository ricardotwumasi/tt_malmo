"""
Perception Module - Processes sensory input from Minecraft world.

This module processes raw observations from Malmo and extracts
salient features for the Cognitive Controller.
"""

from typing import Dict, Any, List, Optional
from .base_module import Module
from ..agent_state import AgentState


class PerceptionModule(Module):
    """
    Perception Module - Sensory processing.

    Processes raw Malmo observations and identifies:
    - Nearby entities (agents, mobs, items)
    - Environmental features (blocks, terrain)
    - Threats and opportunities
    - Salient changes in the environment
    """

    def __init__(self, update_interval: float = 0.5):
        """
        Initialize Perception module.

        Args:
            update_interval: Time between perception updates
        """
        super().__init__(name='perception', update_interval=update_interval)
        self.last_observation = None

    async def process(self, agent_state: AgentState) -> Dict[str, Any]:
        """
        Process current observation and extract salient features.

        Args:
            agent_state: Current agent state

        Returns:
            Perception output with salient features
        """
        observation = agent_state.current_observation

        if not observation:
            return {
                'salient_feature': 'No observation available',
                'entities': [],
                'threats': [],
                'opportunities': []
            }

        # Detect salient changes
        salient_feature = self._detect_salient_change(observation, self.last_observation)

        # Identify nearby entities
        entities = self._process_entities(observation.get('entities', []))

        # Detect threats (damage sources, hostile mobs)
        threats = self._detect_threats(entities, agent_state)

        # Detect opportunities (resources, items, agents)
        opportunities = self._detect_opportunities(observation, entities)

        # Update last observation
        self.last_observation = observation

        return {
            'salient_feature': salient_feature,
            'entities': entities,
            'threats': threats,
            'opportunities': opportunities,
            'environment_summary': self._summarize_environment(observation)
        }

    def _detect_salient_change(self, current: Dict[str, Any],
                               previous: Optional[Dict[str, Any]]) -> str:
        """
        Detect the most salient change in observations.

        Args:
            current: Current observation
            previous: Previous observation

        Returns:
            Description of salient change
        """
        if not previous:
            return "Environment initialized"

        # Check for health change
        current_health = current.get('Life', 20)
        previous_health = previous.get('Life', 20)
        if current_health < previous_health:
            return f"Taking damage! Health: {current_health:.1f}"
        elif current_health > previous_health:
            return f"Healing! Health: {current_health:.1f}"

        # Check for new nearby agents
        current_agents = len([e for e in current.get('entities', [])
                             if e.get('name', '').startswith('Agent')])
        previous_agents = len([e for e in previous.get('entities', [])
                              if e.get('name', '').startswith('Agent')])
        if current_agents > previous_agents:
            return "New agent nearby"
        elif current_agents < previous_agents:
            return "Agent left area"

        # Check for inventory changes
        current_inv_size = len(current.get('inventory', []))
        previous_inv_size = len(previous.get('inventory', []))
        if current_inv_size > previous_inv_size:
            return "Acquired new item"
        elif current_inv_size < previous_inv_size:
            return "Used/dropped item"

        return "Environment stable"

    def _process_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process entity list and categorize.

        Args:
            entities: Raw entity list from observation

        Returns:
            Processed entity list with categories
        """
        processed = []

        for entity in entities:
            entity_data = {
                'name': entity.get('name', 'Unknown'),
                'distance': entity.get('distance', 999),
                'type': self._categorize_entity(entity.get('name', ''))
            }
            processed.append(entity_data)

        # Sort by distance (closest first)
        processed.sort(key=lambda e: e['distance'])

        return processed

    def _categorize_entity(self, name: str) -> str:
        """
        Categorize entity by name.

        Args:
            name: Entity name

        Returns:
            Entity category
        """
        name_lower = name.lower()

        if 'agent' in name_lower:
            return 'agent'
        elif any(mob in name_lower for mob in ['zombie', 'skeleton', 'creeper', 'spider']):
            return 'hostile_mob'
        elif any(mob in name_lower for mob in ['cow', 'pig', 'sheep', 'chicken']):
            return 'passive_mob'
        elif 'item' in name_lower:
            return 'item'
        else:
            return 'unknown'

    def _detect_threats(self, entities: List[Dict[str, Any]],
                       agent_state: AgentState) -> List[Dict[str, Any]]:
        """
        Detect threats in environment.

        Args:
            entities: Processed entity list
            agent_state: Current agent state

        Returns:
            List of threats
        """
        threats = []

        # Hostile mobs within 10 blocks are threats
        for entity in entities:
            if entity['type'] == 'hostile_mob' and entity['distance'] < 10:
                threats.append({
                    'type': 'hostile_mob',
                    'name': entity['name'],
                    'distance': entity['distance']
                })

        # Low health is a threat
        if agent_state.current_health < 10:
            threats.append({
                'type': 'low_health',
                'value': agent_state.current_health
            })

        # Low hunger is a threat
        if agent_state.current_hunger < 6:
            threats.append({
                'type': 'low_hunger',
                'value': agent_state.current_hunger
            })

        return threats

    def _detect_opportunities(self, observation: Dict[str, Any],
                             entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect opportunities in environment.

        Args:
            observation: Raw observation
            entities: Processed entity list

        Returns:
            List of opportunities
        """
        opportunities = []

        # Nearby items are opportunities
        for entity in entities:
            if entity['type'] == 'item' and entity['distance'] < 5:
                opportunities.append({
                    'type': 'item_pickup',
                    'name': entity['name'],
                    'distance': entity['distance']
                })

        # Nearby passive mobs are food opportunities
        for entity in entities:
            if entity['type'] == 'passive_mob' and entity['distance'] < 8:
                opportunities.append({
                    'type': 'food_source',
                    'name': entity['name'],
                    'distance': entity['distance']
                })

        # Nearby agents are social opportunities
        for entity in entities:
            if entity['type'] == 'agent' and entity['distance'] < 15:
                opportunities.append({
                    'type': 'social_interaction',
                    'name': entity['name'],
                    'distance': entity['distance']
                })

        return opportunities

    def _summarize_environment(self, observation: Dict[str, Any]) -> str:
        """
        Create brief environment summary.

        Args:
            observation: Current observation

        Returns:
            Environment summary string
        """
        entities = observation.get('entities', [])
        agent_count = len([e for e in entities if e.get('name', '').startswith('Agent')])
        mob_count = len([e for e in entities if 'mob' in e.get('name', '').lower()])

        return f"{agent_count} agents, {mob_count} mobs nearby"
