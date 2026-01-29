#!/usr/bin/env python3
"""
Malmo Integration Test - End-to-end test of AI agents in Minecraft.

This script tests the full pipeline:
1. Connect to Malmo Minecraft server
2. Create AI agent with PIANO architecture
3. Start agent and observe decisions
4. Execute actions in Minecraft
5. Collect and display metrics

Prerequisites:
- Malmo Minecraft must be running: ./launch_malmo.sh 9000
- Environment variables set (GOOGLE_API_KEY or OPENROUTER_API_KEY)

Usage:
    python test_malmo_integration.py [--port 9000] [--steps 50] [--llm gemini]
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


async def test_without_malmo():
    """Test the agent decision loop without actual Malmo connection."""
    print("\n" + "=" * 60)
    print("  TEST MODE: Agent Decision Loop (No Malmo)")
    print("=" * 60 + "\n")

    from mcp_server.agent_manager import AgentManager
    from malmo_integration.mission_builder import MissionBuilder

    # Create agent manager
    manager = AgentManager()

    # Create agent
    print("Creating test agent...")
    agent_id = await manager.create_agent(
        name="TestExplorer",
        llm_type="gemini",
        role=0,
        traits=["curious", "adventurous"]
    )
    print(f"  Agent ID: {agent_id}")

    # Get agent state
    agent_state = manager.agent_states[agent_id]

    # Simulate observations
    test_observations = [
        {
            'XPos': 10.0, 'YPos': 64.0, 'ZPos': 5.0,
            'Life': 20.0, 'Food': 20.0,
            'inventory': [],
            'entities': []
        },
        {
            'XPos': 12.0, 'YPos': 64.0, 'ZPos': 5.0,
            'Life': 18.0, 'Food': 19.0,
            'inventory': [{'type': 'dirt', 'quantity': 3}],
            'entities': [{'name': 'Agent1', 'distance': 10.0}]
        },
        {
            'XPos': 15.0, 'YPos': 64.0, 'ZPos': 8.0,
            'Life': 16.0, 'Food': 17.0,
            'inventory': [{'type': 'dirt', 'quantity': 5}, {'type': 'wood', 'quantity': 2}],
            'entities': [{'name': 'Agent1', 'distance': 5.0}]
        }
    ]

    # Start agent
    print("\nStarting agent PIANO architecture...")
    await manager.start_agent(agent_id)

    print("\nSimulating environment observations...")
    print("-" * 60)

    for i, obs in enumerate(test_observations):
        print(f"\n[Step {i + 1}] Observation:")
        print(f"  Location: ({obs['XPos']}, {obs['YPos']}, {obs['ZPos']})")
        print(f"  Health: {obs['Life']}/20, Food: {obs['Food']}/20")
        print(f"  Inventory: {len(obs['inventory'])} items")
        print(f"  Nearby entities: {len(obs['entities'])}")

        # Update agent with observation
        await manager.process_observation(agent_id, obs)

        # Wait for decision
        await asyncio.sleep(3)

        # Get and display decision
        decision = await manager.get_agent_decision(agent_id)
        if decision:
            print(f"\n  Decision: {decision.get('action', 'unknown')}")
            print(f"  Reasoning: {decision.get('reasoning', 'none')}")
            print(f"  Target: {decision.get('target', 'none')}")

    # Stop agent
    print("\n" + "-" * 60)
    print("\nStopping agent...")
    await manager.stop_agent(agent_id)

    # Show summary
    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)

    state_summary = manager.get_agent_state_summary(agent_id)
    print(f"\nFinal agent state:")
    print(f"  Name: {state_summary['name']}")
    print(f"  Goals generated: {len(state_summary.get('current_goals', []))}")
    print(f"  Action success rate: {state_summary.get('action_success_rate', 1.0):.2%}")

    # Cleanup
    await manager.delete_agent(agent_id)
    print("\nAgent deleted. Test passed!")


async def test_with_malmo(port: int, max_steps: int, llm_type: str):
    """Test with actual Malmo connection."""
    print("\n" + "=" * 60)
    print("  LIVE TEST: Agent + Malmo Minecraft")
    print("=" * 60 + "\n")

    try:
        import malmoenv
    except ImportError:
        print("Error: malmoenv not installed.")
        print("Run: pip install malmoenv")
        print("Or: cd ../malmo/MalmoEnv && pip install -e .")
        return False

    from mcp_server.agent_manager import AgentManager
    from malmo_integration.environment_manager import MalmoEnvironmentManager
    from malmo_integration.mission_builder import MissionBuilder

    # Create mission XML
    print("Creating mission...")
    builder = MissionBuilder()
    mission_xml = builder.create_simple_test_mission(num_agents=1)
    print(f"  Mission created with 1 agent")

    # Create agent manager
    manager = AgentManager()

    # Create agent
    print(f"\nCreating agent with {llm_type}...")
    agent_id = await manager.create_agent(
        name="MalmoExplorer",
        llm_type=llm_type,
        role=0,
        traits=["curious", "brave", "resourceful"]
    )
    print(f"  Agent ID: {agent_id}")

    # Get agent state
    agent_state = manager.agent_states[agent_id]

    # Start PIANO architecture
    print("\nStarting PIANO architecture...")
    await manager.start_agent(agent_id)

    # Create environment manager
    print(f"\nConnecting to Malmo on port {port}...")
    env_manager = MalmoEnvironmentManager(mission_xml, port=port)

    try:
        env_manager.connect()
        print("  Connected!")

        # Run agent loop
        print(f"\nRunning agent for {max_steps} steps...")
        print("Press Ctrl+C to stop early.")
        print("-" * 60)

        await env_manager.run_agent_loop(
            agent_state,
            manager,
            agent_id,
            max_steps=max_steps
        )

    except ConnectionRefusedError:
        print(f"\nError: Could not connect to Malmo on port {port}")
        print("Make sure Minecraft is running:")
        print(f"  ./launch_malmo.sh {port}")
        return False

    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        env_manager.close()
        await manager.stop_agent(agent_id)
        await manager.delete_agent(agent_id)

    print("\n" + "=" * 60)
    print("  LIVE TEST COMPLETE")
    print("=" * 60)
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Test AI agents with Malmo Minecraft'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=9000,
        help='Malmo port (default: 9000)'
    )
    parser.add_argument(
        '--steps', '-s',
        type=int,
        default=50,
        help='Maximum steps to run (default: 50)'
    )
    parser.add_argument(
        '--llm', '-l',
        type=str,
        default='gemini',
        choices=['gemini', 'openrouter', 'cerebras', 'cloudflare'],
        help='LLM provider (default: gemini)'
    )
    parser.add_argument(
        '--no-malmo',
        action='store_true',
        help='Run test without Malmo (decision loop only)'
    )

    args = parser.parse_args()

    # Check for API keys
    if args.llm == 'gemini' and not os.getenv('GOOGLE_API_KEY'):
        print("Error: GOOGLE_API_KEY not set")
        print("Run: export GOOGLE_API_KEY=your_key")
        sys.exit(1)
    elif args.llm == 'openrouter' and not os.getenv('OPENROUTER_API_KEY'):
        print("Error: OPENROUTER_API_KEY not set")
        print("Run: export OPENROUTER_API_KEY=your_key")
        sys.exit(1)

    print("=" * 60)
    print("  MALMO INTEGRATION TEST")
    print("=" * 60)
    print(f"\n  Port: {args.port}")
    print(f"  Max Steps: {args.steps}")
    print(f"  LLM: {args.llm}")
    print(f"  Mode: {'Decision Loop Only' if args.no_malmo else 'Full Malmo Integration'}")

    if args.no_malmo:
        asyncio.run(test_without_malmo())
    else:
        success = asyncio.run(test_with_malmo(args.port, args.steps, args.llm))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
