"""
Goal Generation Module - Creates and manages agent goals.

This module generates new goals based on:
- Current needs (hunger, health)
- Opportunities in environment
- Social context
- Personality traits

Goals are generated every 5-10 seconds as per Project Sid methodology.
"""

from typing import Dict, Any, List
from datetime import datetime
from .base_module import Module
from ..agent_state import AgentState


class GoalGenerationModule(Module):
    """
    Goal Generation Module - Autonomous goal creation.

    Generates goals that drive agent behavior, enabling:
    - Role specialization (via goal patterns)
    - Autonomous exploration
    - Social coordination
    - Survival behavior
    """

    def __init__(self, llm_adapter, update_interval: float = 7.0):
        """
        Initialize Goal Generation module.

        Args:
            llm_adapter: LLM adapter for goal reasoning
            update_interval: Time between goal generation (5-10 seconds)
        """
        super().__init__(name='goal_generation', update_interval=update_interval)
        self.llm = llm_adapter

        # Track goal history for role analysis
        self.goal_history: List[Dict[str, Any]] = []

    async def process(self, agent_state: AgentState) -> Dict[str, Any]:
        """
        Generate new goals based on current state.

        Args:
            agent_state: Current agent state

        Returns:
            Goal generation output with proposed goals
        """
        # Generate new goal using LLM
        new_goal = await self._generate_goal_with_llm(agent_state)

        if new_goal:
            # Add goal to agent state
            goal_entry = {
                'description': new_goal,
                'generated_at': datetime.now().isoformat(),
                'status': 'active',
                'priority': self._compute_priority(new_goal, agent_state)
            }

            # Update current goals
            current_goals = agent_state.current_goals.copy()
            current_goals.append(goal_entry)

            # Keep only top 3 goals (by priority)
            current_goals.sort(key=lambda g: g.get('priority', 0), reverse=True)
            current_goals = current_goals[:3]

            agent_state.update_safely('current_goals', current_goals)

            # Track in history for role analysis
            self.goal_history.append(goal_entry)
            if len(self.goal_history) > 100:
                self.goal_history.pop(0)

            return {
                'proposed_goals': [new_goal],
                'current_goal_count': len(current_goals),
                'goal_added': True
            }
        else:
            return {
                'proposed_goals': [],
                'current_goal_count': len(agent_state.current_goals),
                'goal_added': False
            }

    async def _generate_goal_with_llm(self, agent_state: AgentState) -> str:
        """
        Generate a new goal using LLM reasoning.

        Args:
            agent_state: Current agent state

        Returns:
            Generated goal description
        """
        prompt = self._construct_goal_prompt(agent_state)

        try:
            goal_text = await self.llm.generate(prompt)
            return self._parse_goal(goal_text)
        except Exception as e:
            print(f"Error generating goal: {e}")
            return self._generate_fallback_goal(agent_state)

    def _construct_goal_prompt(self, agent_state: AgentState) -> str:
        """
        Construct prompt for goal generation.

        Args:
            agent_state: Current agent state

        Returns:
            Prompt string
        """
        prompt = f"""You are {agent_state.name}, an agent in a Minecraft world.

Your traits: {', '.join(agent_state.traits)}

## Current State
Health: {agent_state.current_health:.1f}/20
Hunger: {agent_state.current_hunger:.1f}/20
Inventory: {len(agent_state.current_inventory)} items
Location: {agent_state.current_location}

## Nearby
{len(agent_state.nearby_agents)} agents nearby
Recent memory: {self._format_recent_memory(agent_state.working_memory)}

## Current Goals
{self._format_goals(agent_state.current_goals)}

## Task
Generate ONE new goal for yourself. The goal should be:
1. Specific and actionable
2. Aligned with your survival needs and personality
3. Compatible with social context
4. Different from current goals

Respond with only the goal description (one sentence, no explanation).
Example: "Find wood to build shelter"
Example: "Trade resources with nearby agents"
Example: "Explore the area to find food"

Your goal:"""

        return prompt

    def _format_recent_memory(self, working_memory: List[Dict[str, Any]]) -> str:
        """Format recent memory for prompt."""
        if not working_memory:
            return "No recent memories"
        return ", ".join([m.get('event', 'Unknown') for m in working_memory[-3:]])

    def _format_goals(self, goals: List[Dict[str, Any]]) -> str:
        """Format current goals for prompt."""
        if not goals:
            return "No active goals"
        return "\n".join([f"- {g.get('description', 'Unknown')}" for g in goals])

    def _parse_goal(self, goal_text: str) -> str:
        """
        Parse LLM output to extract goal.

        Args:
            goal_text: Raw LLM output

        Returns:
            Cleaned goal description
        """
        # Remove any prefixes like "Goal:", "My goal:", etc.
        goal = goal_text.strip()
        prefixes = ["goal:", "my goal:", "new goal:", "i want to", "i will"]

        for prefix in prefixes:
            if goal.lower().startswith(prefix):
                goal = goal[len(prefix):].strip()

        # Capitalize first letter
        if goal:
            goal = goal[0].upper() + goal[1:]

        return goal

    def _generate_fallback_goal(self, agent_state: AgentState) -> str:
        """
        Generate a fallback goal if LLM fails.

        Args:
            agent_state: Current agent state

        Returns:
            Fallback goal description
        """
        # Priority 1: Survival needs
        if agent_state.current_health < 10:
            return "Find shelter to avoid danger"
        if agent_state.current_hunger < 6:
            return "Find food to restore hunger"

        # Priority 2: Basic resource gathering
        if len(agent_state.current_inventory) < 3:
            return "Gather basic resources (wood, stone)"

        # Priority 3: Exploration
        return "Explore the surrounding area"

    def _compute_priority(self, goal: str, agent_state: AgentState) -> float:
        """
        Compute priority score for a goal.

        Args:
            goal: Goal description
            agent_state: Current agent state

        Returns:
            Priority score (0.0 to 1.0)
        """
        goal_lower = goal.lower()

        # Survival goals have highest priority
        if agent_state.current_health < 10 and any(word in goal_lower
                                                    for word in ['health', 'heal', 'shelter', 'hide']):
            return 1.0

        if agent_state.current_hunger < 6 and any(word in goal_lower
                                                   for word in ['food', 'eat', 'hunt']):
            return 0.9

        # Resource gathering goals
        if any(word in goal_lower for word in ['gather', 'collect', 'mine', 'wood', 'stone']):
            return 0.7

        # Social goals
        if any(word in goal_lower for word in ['trade', 'help', 'cooperate', 'talk']):
            return 0.6

        # Exploration goals
        if any(word in goal_lower for word in ['explore', 'find', 'search']):
            return 0.5

        # Default priority
        return 0.5

    def get_goal_patterns(self) -> Dict[str, int]:
        """
        Analyze goal history to identify patterns (for role inference).

        Returns:
            Dictionary of goal categories and their frequencies
        """
        patterns = {
            'gathering': 0,
            'building': 0,
            'exploring': 0,
            'social': 0,
            'survival': 0
        }

        for goal_entry in self.goal_history:
            goal = goal_entry.get('description', '').lower()

            if any(word in goal for word in ['gather', 'collect', 'mine']):
                patterns['gathering'] += 1
            if any(word in goal for word in ['build', 'craft', 'create']):
                patterns['building'] += 1
            if any(word in goal for word in ['explore', 'find', 'search']):
                patterns['exploring'] += 1
            if any(word in goal for word in ['trade', 'help', 'cooperate']):
                patterns['social'] += 1
            if any(word in goal for word in ['food', 'heal', 'shelter']):
                patterns['survival'] += 1

        return patterns
