"""
Simple launch - Use MalmoEnv's existing mission files.

This uses the tested missions from MalmoEnv/missions.
"""

import asyncio
import sys
import os

# Add MalmoEnv to path
import config
sys.path.insert(0, config.MALMOENV_DIR)

import malmoenv
from dotenv import load_dotenv
load_dotenv()

# Import our components
from piano_architecture.agent_state import AgentState
from piano_architecture.cognitive_controller import CognitiveController
from llm_adapters import GeminiAdapter


async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🎮 Watch Gemini 2.5 Flash Play Minecraft!                  ║
╚══════════════════════════════════════════════════════════════╝
""")

    # Setup
    api_key = config.GOOGLE_API_KEY

    # Create agent components
    print("Setting up AI agent...")
    agent_state = AgentState(
        agent_id="test-agent",
        name="Explorer_Gemini",
        role=0,
        traits=["curious", "adventurous"]
    )

    llm = GeminiAdapter(api_key=api_key)
    controller = CognitiveController(llm, decision_interval=5.0)

    print("✅ Agent ready")
    print()

    # Connect to Malmo
    print("Connecting to Minecraft...")
    env = malmoenv.make()
    print("✅ Connected!")
    print()

    try:
        # Start decision loop
        print("Starting AI brain...")
        decision_task = asyncio.create_task(controller.run_decision_loop(agent_state))
        print("✅ AI is thinking...")
        print()

        print("="*60)
        print("🎮 AGENT IS NOW PLAYING MINECRAFT!")
        print("Watch your Minecraft window!")
        print("="*60)
        print()

        # Run for 50 steps
        for step in range(50):
            # Reset if first step
            if step == 0:
                obs = env.reset()
                print(f"Step {step}: Mission started")

            # Get agent's decision
            await asyncio.sleep(1.0)  # Give agent time to decide
            decision = agent_state.bottleneck_decision

            if decision:
                action = decision.get('action', 'explore')
                reasoning = decision.get('reasoning', '')

                print(f"\nStep {step + 1}:")
                print(f"  🤖 Action: {action}")
                print(f"  💭 Thinking: {reasoning}")

                # Map to Malmo command
                if 'forward' in action.lower() or 'explore' in action.lower():
                    command = 'move 1'
                elif 'turn' in action.lower() or 'right' in action.lower():
                    command = 'turn 1'
                elif 'left' in action.lower():
                    command = 'turn -1'
                elif 'jump' in action.lower():
                    command = 'jump 1'
                else:
                    command = 'move 1'

                print(f"  ⚙️  Executing: {command}")

                # Execute in Minecraft
                obs, reward, done, info = env.step(command)

                # Update agent
                agent_state.update_observation({
                    'pixels': obs,
                    'step': step,
                    'reward': reward
                })

                print(f"  ✅ Reward: {reward}")

                if done:
                    print("\n🏁 Mission complete!")
                    break
            else:
                # Default action while AI is thinking
                obs, reward, done, info = env.step('move 1')
                print(f"Step {step + 1}: Moving forward (AI thinking...)")

        # Stop decision loop
        decision_task.cancel()
        try:
            await decision_task
        except asyncio.CancelledError:
            pass

    finally:
        env.close()
        print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
