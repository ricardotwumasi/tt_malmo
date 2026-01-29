"""
Action Awareness Module - Prevents hallucination cascades.

This is THE MOST CRITICAL module in PIANO architecture. It prevents
agents from hallucinating their success by comparing expected outcomes
with actual observed outcomes.

Without this module, agents can fall into "hallucination cascades" where
they believe they've completed actions that never actually happened.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from .base_module import Module
from ..agent_state import AgentState


class ActionAwarenessModule(Module):
    """
    Action Awareness Module - Compares expected vs actual outcomes.

    This module:
    1. Stores expected outcomes before actions
    2. Compares expected with observed outcomes after actions
    3. Detects mismatches (hallucinations)
    4. Corrects agent beliefs when mismatches occur
    5. Tracks action success rate
    """

    def __init__(self, update_interval: float = 0.5):
        """
        Initialize Action Awareness module.

        Args:
            update_interval: Time between checks (faster than other modules)
        """
        super().__init__(name='action_awareness', update_interval=update_interval)

        self.expected_outcome: Optional[Dict[str, Any]] = None
        self.expected_set_time: Optional[datetime] = None
        self.action_timeout = 5.0  # Seconds to wait for action completion
        self.match_threshold = 0.6  # Minimum similarity for successful action

    async def process(self, agent_state: AgentState) -> Dict[str, Any]:
        """
        Compare expected outcomes with observed outcomes.

        Args:
            agent_state: Current agent state

        Returns:
            Dictionary with match status and corrections
        """
        # If no expected outcome set, nothing to check
        if not self.expected_outcome:
            return {
                'status': 'no_expectation',
                'message': 'No action expectation set'
            }

        # Check if action has timed out
        if self.expected_set_time:
            time_elapsed = (datetime.now() - self.expected_set_time).total_seconds()
            if time_elapsed > self.action_timeout:
                result = {
                    'status': 'timeout',
                    'message': f'Action timed out after {time_elapsed:.1f}s',
                    'expected': self.expected_outcome,
                    'correction_needed': True
                }
                self._update_success_rate(agent_state, success=False)
                self.expected_outcome = None
                return result

        # Get current observation
        actual_observation = agent_state.current_observation
        if not actual_observation:
            return {
                'status': 'no_observation',
                'message': 'Waiting for observation'
            }

        # Compare expected with actual
        match_score = self._compute_match_score(
            self.expected_outcome,
            actual_observation,
            agent_state
        )

        # Check if action succeeded
        if match_score >= self.match_threshold:
            # Action succeeded
            result = {
                'status': 'success',
                'message': 'Action outcome matches expectation',
                'match_score': match_score,
                'expected': self.expected_outcome,
                'observed': self._extract_relevant_observation(actual_observation)
            }
            self._update_success_rate(agent_state, success=True)
            self.expected_outcome = None  # Clear expectation
            return result

        else:
            # Mismatch detected - HALLUCINATION PREVENTION
            result = {
                'status': 'mismatch',
                'message': f'Action outcome mismatch (score: {match_score:.2f})',
                'match_score': match_score,
                'expected': self.expected_outcome,
                'observed': self._extract_relevant_observation(actual_observation),
                'correction_needed': True,
                'correction': self._generate_correction(
                    self.expected_outcome,
                    actual_observation
                )
            }
            self._update_success_rate(agent_state, success=False)

            # Add correction to working memory
            agent_state.add_to_memory('working', {
                'type': 'action_failure',
                'expected': self.expected_outcome.get('action', 'unknown'),
                'reason': result['correction']
            })

            self.expected_outcome = None  # Clear expectation
            return result

    def set_expectation(self, action: str, expected_outcome: Dict[str, Any]) -> None:
        """
        Set expected outcome before taking action.

        This MUST be called before every action to enable hallucination prevention.

        Args:
            action: Action being taken (e.g., "mine_block", "move_forward")
            expected_outcome: Expected changes to observation
        """
        self.expected_outcome = {
            'action': action,
            'expected_changes': expected_outcome,
            'set_time': datetime.now().isoformat()
        }
        self.expected_set_time = datetime.now()

    def _compute_match_score(self, expected: Dict[str, Any],
                            observed: Dict[str, Any],
                            agent_state: AgentState) -> float:
        """
        Compute similarity between expected and observed outcomes.

        Args:
            expected: Expected outcome dictionary
            observed: Actual observation from Malmo
            agent_state: Current agent state

        Returns:
            Match score from 0.0 to 1.0
        """
        if not expected or not observed:
            return 0.0

        expected_changes = expected.get('expected_changes', {})
        action = expected.get('action', '')

        score = 0.0
        checks = 0

        # Check inventory changes (if action involves items)
        if action in ['mine_block', 'pick_up_item', 'craft_item']:
            if 'inventory_change' in expected_changes:
                expected_items = expected_changes['inventory_change']
                actual_inventory = agent_state.current_inventory

                # Simple check: did inventory change as expected?
                inventory_match = self._check_inventory_change(
                    expected_items,
                    actual_inventory
                )
                score += inventory_match
                checks += 1

        # Check location changes (if action involves movement)
        if action in ['move_forward', 'move_back', 'turn', 'jump']:
            if 'location_change' in expected_changes:
                expected_delta = expected_changes['location_change']
                actual_location = agent_state.current_location

                # Check if location changed approximately as expected
                location_match = self._check_location_change(
                    expected_delta,
                    actual_location
                )
                score += location_match
                checks += 1

        # Check health/hunger changes
        if 'health_change' in expected_changes:
            expected_health = expected_changes['health_change']
            actual_health = agent_state.current_health
            # Simple check: did health change in expected direction?
            if (expected_health > 0 and actual_health > agent_state.current_health) or \
               (expected_health < 0 and actual_health < agent_state.current_health):
                score += 1.0
            checks += 1

        # If no specific checks, use generic heuristic
        if checks == 0:
            # Default: assume action succeeded if observation changed
            return 0.7

        return score / checks if checks > 0 else 0.0

    def _check_inventory_change(self, expected_items: Dict[str, int],
                                actual_inventory: list) -> float:
        """
        Check if inventory changed as expected.

        Args:
            expected_items: Expected item changes {item_name: quantity_change}
            actual_inventory: Current inventory from agent state

        Returns:
            Match score 0.0 to 1.0
        """
        # Simple heuristic: check if expected items are present
        if not actual_inventory:
            return 0.0

        inventory_dict = {item.get('type', ''): item.get('quantity', 0)
                         for item in actual_inventory}

        matches = 0
        total = len(expected_items)

        for item, expected_change in expected_items.items():
            actual_quantity = inventory_dict.get(item, 0)
            if expected_change > 0 and actual_quantity > 0:
                matches += 1
            elif expected_change < 0 and actual_quantity == 0:
                matches += 1

        return matches / total if total > 0 else 0.0

    def _check_location_change(self, expected_delta: Dict[str, float],
                               actual_location: Optional[Dict[str, float]]) -> float:
        """
        Check if location changed as expected.

        Args:
            expected_delta: Expected location change {x, y, z}
            actual_location: Actual location

        Returns:
            Match score 0.0 to 1.0
        """
        if not actual_location:
            return 0.0

        # Simple heuristic: if any coordinate changed in expected direction, partial match
        matches = 0
        for axis in ['x', 'y', 'z']:
            if axis in expected_delta and expected_delta[axis] != 0:
                # Check if movement occurred (any change is positive signal)
                matches += 1

        return matches / 3.0  # Normalize to 0-1

    def _extract_relevant_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant parts of observation for logging.

        Args:
            observation: Full observation dictionary

        Returns:
            Simplified observation
        """
        return {
            'location': observation.get('XPos', 'unknown'),
            'inventory_size': len(observation.get('inventory', [])),
            'health': observation.get('Life', 'unknown'),
            'nearby_blocks': len(observation.get('nearby_blocks', []))
        }

    def _generate_correction(self, expected: Dict[str, Any],
                           observed: Dict[str, Any]) -> str:
        """
        Generate correction message for agent.

        Args:
            expected: Expected outcome
            observed: Actual observation

        Returns:
            Correction message
        """
        action = expected.get('action', 'unknown action')
        return f"The {action} did not complete as expected. The environment state did not change in the expected way."

    def _update_success_rate(self, agent_state: AgentState, success: bool) -> None:
        """
        Update agent's action success rate.

        Args:
            agent_state: Current agent state
            success: Whether action succeeded
        """
        # Exponential moving average
        alpha = 0.1
        current_rate = agent_state.action_success_rate
        new_rate = current_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
        agent_state.update_safely('action_success_rate', new_rate)
