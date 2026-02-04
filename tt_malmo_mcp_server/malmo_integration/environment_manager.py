"""
Environment Manager - Connects agents to Malmo/Minecraft.

This bridges the PIANO architecture with the Malmo environment,
enabling agents to observe and act in Minecraft.
"""

import malmoenv
from malmoenv.core import StringActionSpace
import asyncio
from typing import Dict, Any, Optional
import numpy as np


class MalmoEnvironmentManager:
    """
    Manages connection between agents and Malmo environment.

    Handles:
    - Connecting to Malmo on specified port
    - Sending observations to agents
    - Receiving actions from agents
    - Executing actions in Minecraft
    """

    def __init__(self, mission_xml: str, port: int = 9000):
        """
        Initialize Environment Manager.

        Args:
            mission_xml: Mission XML string
            port: Malmo port number
        """
        self.mission_xml = mission_xml
        self.port = port
        self.env = None
        self.running = False

    def connect(self):
        """Connect to Malmo environment."""
        print(f"Connecting to Malmo on port {self.port}...")

        # Create MalmoEnv environment
        self.env = malmoenv.make()

        # Initialize with mission XML, using StringActionSpace for string commands
        self.env.init(
            self.mission_xml,
            self.port,
            server='127.0.0.1',
            role=0,
            action_space=StringActionSpace()  # Allows string commands like "move 1"
        )

        print("✅ Connected to Malmo!")
        return True

    def reset(self) -> Dict[str, Any]:
        """
        Reset environment and get initial observation.

        Returns:
            Initial observation dictionary
        """
        if not self.env:
            raise RuntimeError("Environment not connected. Call connect() first.")

        print("Resetting Malmo environment...")
        obs = self.env.reset()

        # Convert observation to dictionary format
        return self._process_observation(obs)

    def step(self, action: str) -> tuple[Dict[str, Any], float, bool]:
        """
        Execute action in Malmo and get result.

        Args:
            action: Action string (e.g., "move 1", "turn 1", "attack 1")

        Returns:
            (observation, reward, done) tuple
        """
        if not self.env:
            raise RuntimeError("Environment not connected.")

        # Execute action
        obs, reward, done, info = self.env.step(action)

        # Process observation
        processed_obs = self._process_observation(obs)

        return processed_obs, reward, done

    def _process_observation(self, obs) -> Dict[str, Any]:
        """
        Process raw Malmo observation into structured format.

        Args:
            obs: Raw observation from MalmoEnv (usually pixel array)

        Returns:
            Structured observation dictionary
        """
        # MalmoEnv typically returns pixel observations
        # For now, we'll create a basic structure

        if isinstance(obs, np.ndarray):
            observation = {
                'type': 'video',
                'pixels': obs,
                'shape': obs.shape,
                'mean_pixel': float(np.mean(obs)),
                # These would normally come from ObservationFromFullStats
                'XPos': 0.0,
                'YPos': 4.0,
                'ZPos': 0.0,
                'Life': 20.0,
                'Food': 20.0,
                'inventory': [],
                'entities': []
            }
        else:
            observation = {
                'type': 'unknown',
                'data': str(obs)
            }

        return observation

    def close(self):
        """Close Malmo connection."""
        if self.env:
            print("Closing Malmo environment...")
            self.env.close()
            self.env = None
            print("✅ Malmo connection closed")

    async def run_agent_loop(self, agent_state, agent_manager, agent_id: str,
                            max_steps: int = 1000):
        """
        Run the agent control loop.

        This is the main loop that:
        1. Gets observations from Malmo
        2. Sends to agent's PIANO architecture
        3. Gets decisions from Cognitive Controller
        4. Executes actions in Malmo

        Args:
            agent_state: Agent's state object
            agent_manager: Agent manager instance
            agent_id: Agent ID
            max_steps: Maximum steps to run
        """
        print(f"\n{'='*60}")
        print(f"🎮 Starting agent control loop for {agent_state.name}")
        print(f"{'='*60}\n")

        self.running = True
        step_count = 0

        try:
            # Reset environment and get initial observation
            obs = self.reset()

            # Send initial observation to agent
            agent_state.update_observation(obs)

            print(f"Step {step_count}: Initial observation received")
            print(f"  Location: ({obs.get('XPos', 0):.1f}, {obs.get('YPos', 0):.1f}, {obs.get('ZPos', 0):.1f})")
            print(f"  Health: {obs.get('Life', 20):.1f}/20")
            print()

            while self.running and step_count < max_steps:
                # Wait for agent to make a decision
                await asyncio.sleep(1.0)  # Give agent time to process

                # Get decision from Cognitive Controller
                decision = agent_state.bottleneck_decision

                if decision:
                    action_type = decision.get('action', 'explore')
                    reasoning = decision.get('reasoning', 'No reasoning')

                    print(f"Step {step_count + 1}:")
                    print(f"  🤖 Agent decision: {action_type}")
                    print(f"  💭 Reasoning: {reasoning}")

                    # Convert high-level action to Malmo command
                    malmo_action = self._action_to_malmo_command(action_type)
                    print(f"  ⚙️  Malmo command: {malmo_action}")

                    # Execute action
                    obs, reward, done = self.step(malmo_action)

                    # Update agent observation
                    agent_state.update_observation(obs)

                    print(f"  ✅ Reward: {reward:.1f}")
                    print(f"  📍 Location: ({obs.get('XPos', 0):.1f}, {obs.get('YPos', 0):.1f}, {obs.get('ZPos', 0):.1f})")
                    print()

                    if done:
                        print("Mission completed!")
                        break

                step_count += 1

        except KeyboardInterrupt:
            print("\n⚠️  Control loop interrupted by user")
        except Exception as e:
            print(f"\n❌ Error in control loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            print(f"\n{'='*60}")
            print(f"Control loop finished. Total steps: {step_count}")
            print(f"{'='*60}\n")

    def _action_to_malmo_command(self, action: str) -> str:
        """
        Convert high-level action to Malmo command.

        Args:
            action: High-level action from Cognitive Controller

        Returns:
            Malmo action command
        """
        action_lower = action.lower()

        # Movement commands
        if 'forward' in action_lower or 'explore' in action_lower:
            return 'move 1'
        elif 'back' in action_lower or 'retreat' in action_lower:
            return 'move -1'
        elif 'left' in action_lower:
            return 'turn -1'
        elif 'right' in action_lower:
            return 'turn 1'
        elif 'jump' in action_lower:
            return 'jump 1'
        elif 'crouch' in action_lower or 'sneak' in action_lower:
            return 'crouch 1'

        # Building actions
        elif 'place' in action_lower or 'build' in action_lower:
            return 'use 1'
        elif 'mine' in action_lower or 'break' in action_lower or 'dig' in action_lower:
            return 'attack 1'

        # Hotbar/inventory slot selection
        elif 'select' in action_lower or 'slot' in action_lower or 'hotbar' in action_lower:
            # Extract slot number: "select_slot_3" or "hotbar 3" → "hotbar.3 1"
            slot = ''.join(filter(str.isdigit, action_lower)) or '1'
            slot = min(int(slot), 9)  # Clamp to valid hotbar range 1-9
            return f'hotbar.{slot} 1'

        # Crafting commands
        elif 'craft' in action_lower:
            # Extract item name if present: "craft_planks" → "craft planks"
            parts = action_lower.replace('_', ' ').split()
            if len(parts) > 1:
                item = parts[1]
                return f'craft {item}'
            return 'craft planks'  # Default craft

        # Combat actions
        elif 'attack' in action_lower:
            return 'attack 1'

        # Interaction
        elif 'use' in action_lower or 'interact' in action_lower:
            return 'use 1'

        # Look commands (pitch = up/down, yaw = left/right)
        elif 'look_up' in action_lower:
            return 'pitch -0.5'
        elif 'look_down' in action_lower:
            return 'pitch 0.5'

        # Stop commands
        elif 'stop' in action_lower or 'wait' in action_lower:
            return 'move 0'

        else:
            # Default: move forward
            return 'move 1'

    def execute_action_sequence(self, actions: list) -> list:
        """
        Execute a sequence of actions in order.

        Args:
            actions: List of high-level action strings

        Returns:
            List of (observation, reward, done) tuples for each action
        """
        results = []
        for action in actions:
            malmo_cmd = self._action_to_malmo_command(action)
            obs, reward, done = self.step(malmo_cmd)
            results.append((obs, reward, done))
            if done:
                break
        return results

    def stop(self):
        """Stop the agent control loop."""
        self.running = False
