"""
Launch Agent in Minecraft - Connect PIANO agent to Malmo.

This script:
1. Gets the agent from MCP server
2. Loads a mission
3. Connects to Minecraft
4. Starts the agent control loop
5. You watch the agent play!
"""

import asyncio
import sys
from malmo_integration.environment_manager import MalmoEnvironmentManager
from malmo_integration.mission_builder import MissionBuilder
from mcp_server.agent_manager import AgentManager


async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  Malmo MCP Server - Launch Agent in Minecraft               ║
║  Watch your AI agent play Minecraft!                        ║
╚══════════════════════════════════════════════════════════════╝
""")

    # Configuration
    AGENT_ID = "90034310-9331-4600-ae82-972d59e79db0"  # Your Explorer_Gemini
    MALMO_PORT = 9000
    MAX_STEPS = 100  # Run for 100 steps (about 2 minutes)

    print(f"Agent ID: {AGENT_ID}")
    print(f"Malmo Port: {MALMO_PORT}")
    print(f"Max Steps: {MAX_STEPS}")
    print()

    # Import agent manager components
    from piano_architecture.agent_state import AgentState
    import os
    from dotenv import load_dotenv
    from llm_adapters import GeminiAdapter

    load_dotenv()

    # Get API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in .env")
        return

    print("✅ API key loaded")

    # Create simple agent state (simulating what agent_manager does)
    print("Creating agent state...")
    agent_state = AgentState(
        agent_id=AGENT_ID,
        name="Explorer_Gemini",
        role=0,
        traits=["curious", "adventurous", "resourceful"]
    )

    # Create LLM adapter
    print("Initializing Gemini 2.5 Flash...")
    llm_adapter = GeminiAdapter(api_key=api_key)

    # Create Cognitive Controller
    from piano_architecture.cognitive_controller import CognitiveController
    controller = CognitiveController(llm_adapter, decision_interval=5.0)

    print("✅ Agent components ready")
    print()

    # Generate mission XML
    print("Generating Minecraft mission...")
    builder = MissionBuilder()
    mission_xml = builder.create_simple_test_mission(num_agents=1)
    print("✅ Mission generated")
    print()

    # Create Environment Manager
    print("Creating Environment Manager...")
    env_manager = MalmoEnvironmentManager(mission_xml, port=MALMO_PORT)

    try:
        # Connect to Malmo
        print("Connecting to Minecraft...")
        env_manager.connect()
        print()

        # Start decision loop in background
        print("Starting Cognitive Controller...")
        decision_task = asyncio.create_task(controller.run_decision_loop(agent_state))

        # Start agent control loop
        print("🎮 Starting agent control loop...")
        print("Watch your Minecraft window!")
        print()

        await env_manager.run_agent_loop(
            agent_state=agent_state,
            agent_manager=None,
            agent_id=AGENT_ID,
            max_steps=MAX_STEPS
        )

        # Stop decision loop
        decision_task.cancel()
        try:
            await decision_task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        env_manager.close()
        print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
