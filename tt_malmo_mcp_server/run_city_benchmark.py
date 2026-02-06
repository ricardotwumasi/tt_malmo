#!/usr/bin/env python3
"""
City Building Benchmark - 3 Qwen Agents Building a City

This script:
1. Creates 3 Qwen coder agents via MCP API
2. Sets their goal to "Build a city together"
3. Starts an accelerated mission with spectator mode
4. You can watch from Minecraft or dashboard

Usage:
    python run_city_benchmark.py [options]

Options:
    --speed 2x|5x|10x   Game speed multiplier (default: 2x)
    --agents N          Number of builder agents (default: 3)
    --no-spectator      Disable spectator agent
    --server URL        MCP server URL (default: http://localhost:8080)
    --base-port PORT    Starting Malmo port (default: 9000)
"""

import asyncio
import argparse
import requests
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from malmo_integration.mission_builder import MissionBuilder


# Speed presets (MsPerTick values)
SPEED_PRESETS = {
    "1x": 50,   # Normal Minecraft speed
    "2x": 25,   # Double speed
    "5x": 10,   # 5x speed
    "10x": 5,   # 10x speed (may be unstable)
}

# City building goal prompt
CITY_BUILDING_GOAL = """
Build a city together with your fellow agents. Coordinate to create:
- Houses and buildings with doors and windows
- Roads connecting buildings
- A central town square
- Decorative elements (gardens, fences, lights)

Work together, communicate via chat, and avoid building on top of each other.
Start from the gold block in the center and expand outward.
"""


class CityBenchmark:
    """Manages the city building benchmark."""

    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url.rstrip('/')
        self.agent_ids = []

    def check_server(self) -> bool:
        """Check if MCP server is running."""
        try:
            r = requests.get(f"{self.server_url}/health", timeout=5)
            return r.status_code == 200
        except:
            return False

    def check_ollama(self) -> bool:
        """Check if Ollama is running with Qwen model."""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            if r.status_code == 200:
                models = r.json().get('models', [])
                qwen_models = [m for m in models if 'qwen' in m.get('name', '').lower()]
                if qwen_models:
                    print(f"   Found Qwen models: {[m['name'] for m in qwen_models]}")
                    return True
                print("   No Qwen models found. Run: ollama pull qwen2.5-coder:32b")
        except:
            pass
        return False

    def check_minecraft_port(self, port: int) -> bool:
        """Check if a Minecraft instance is listening on the given port."""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except:
            return False

    def create_agents(self, num_agents: int = 3) -> list:
        """Create Qwen builder agents."""
        agent_names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        builder_traits = [
            ["architect", "creative", "organized"],
            ["builder", "efficient", "cooperative"],
            ["designer", "detail-oriented", "helpful"],
            ["engineer", "strategic", "methodical"],
            ["craftsman", "resourceful", "patient"],
        ]

        created = []

        for i in range(num_agents):
            name = agent_names[i % len(agent_names)]
            traits = builder_traits[i % len(builder_traits)]

            try:
                r = requests.post(
                    f"{self.server_url}/agents",
                    json={
                        "name": name,
                        "llm_type": "ollama",
                        "role": i,
                        "traits": traits
                    },
                    timeout=30
                )

                if r.status_code == 200:
                    data = r.json()
                    agent_id = data['agent_id']
                    self.agent_ids.append(agent_id)
                    created.append({
                        'agent_id': agent_id,
                        'name': name,
                        'role': i
                    })
                    print(f"   [OK] Created {name} (ID: {agent_id[:8]}...)")
                else:
                    print(f"   [FAIL] Failed to create {name}: {r.text}")

            except Exception as e:
                print(f"   [FAIL] Error creating agent: {e}")

        return created

    def start_agents(self) -> int:
        """Start all created agents' PIANO architecture."""
        started = 0
        for agent_id in self.agent_ids:
            try:
                r = requests.post(
                    f"{self.server_url}/agents/{agent_id}/start",
                    timeout=10
                )
                if r.status_code == 200:
                    started += 1
            except Exception as e:
                print(f"   [WARN] Error starting agent {agent_id[:8]}: {e}")

        return started

    def set_goal(self, goal: str):
        """Set the building goal for all agents."""
        try:
            r = requests.post(
                f"{self.server_url}/agents/broadcast-goal",
                json={"description": goal, "priority": 10},
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                print(f"   [OK] Goal set for {len(data.get('affected_agents', []))} agents")
                return True
        except Exception as e:
            print(f"   [WARN] Error setting goal: {e}")
        return False

    def start_mission(self, speed: str = "2x", include_spectator: bool = True,
                      base_port: int = 9000, time_limit_hours: float = 60.0) -> bool:
        """Start the Minecraft mission with configured speed."""
        try:
            # Start mission via API with city_building type
            r = requests.post(
                f"{self.server_url}/mission/start",
                params={
                    "base_port": base_port,
                    "mission_type": "city_building",
                    "speed": speed,
                    "include_spectator": include_spectator,
                    "time_limit_hours": time_limit_hours
                },
                timeout=60
            )

            if r.status_code == 200:
                data = r.json()
                print(f"   [OK] Mission started: {data.get('message', '')}")
                return True
            else:
                error = r.json().get('detail', r.text)
                print(f"   [FAIL] Mission start failed: {error}")

        except Exception as e:
            print(f"   [FAIL] Error starting mission: {e}")

        return False

    def get_status(self) -> dict:
        """Get current benchmark status."""
        try:
            # Get agent statuses
            agents_r = requests.get(f"{self.server_url}/agents", timeout=5)
            agents = agents_r.json() if agents_r.status_code == 200 else []

            # Get mission status
            mission_r = requests.get(f"{self.server_url}/mission/status", timeout=5)
            mission = mission_r.json() if mission_r.status_code == 200 else {}

            return {
                "agents": agents,
                "mission": mission
            }
        except:
            return {"agents": [], "mission": {}}

    def cleanup(self):
        """Stop and delete all created agents."""
        for agent_id in self.agent_ids:
            try:
                requests.post(f"{self.server_url}/mission/stop", timeout=10)
                requests.delete(f"{self.server_url}/agents/{agent_id}", timeout=10)
            except:
                pass


def print_banner():
    """Print startup banner."""
    print("""
============================================================
     CITY BUILDING BENCHMARK - PIANO AGENTS
============================================================
  Watch AI agents collaborate to build a city in Minecraft!
============================================================
""")


def main():
    parser = argparse.ArgumentParser(
        description="Run city building benchmark with Qwen agents"
    )
    parser.add_argument(
        "--speed", choices=["1x", "2x", "5x", "10x"], default="2x",
        help="Game speed multiplier (default: 2x)"
    )
    parser.add_argument(
        "--agents", type=int, default=3,
        help="Number of builder agents (default: 3)"
    )
    parser.add_argument(
        "--no-spectator", action="store_true",
        help="Disable spectator agent"
    )
    parser.add_argument(
        "--server", default="http://localhost:8080",
        help="MCP server URL"
    )
    parser.add_argument(
        "--base-port", type=int, default=9000,
        help="Starting Malmo port (default: 9000)"
    )
    parser.add_argument(
        "--time-limit", type=float, default=60.0,
        help="Mission time limit in hours (default: 60 for weekend run)"
    )
    parser.add_argument(
        "--goal", default=CITY_BUILDING_GOAL,
        help="Custom building goal"
    )

    args = parser.parse_args()

    print_banner()

    benchmark = CityBenchmark(server_url=args.server)

    # Step 1: Check prerequisites
    print("[PREREQ] Checking prerequisites...")

    print("\n[1/6] Checking MCP Server...")
    if not benchmark.check_server():
        print("   [FAIL] MCP Server not running!")
        print("   Run: start_server.bat")
        sys.exit(1)
    print("   [OK] MCP Server running")

    print("\n[2/6] Checking Ollama + Qwen...")
    if not benchmark.check_ollama():
        print("   [FAIL] Ollama not running or Qwen not available!")
        print("   Run: start_ollama.bat")
        print("   Then: ollama pull qwen2.5-coder:32b")
        sys.exit(1)
    print("   [OK] Ollama ready with Qwen")

    print(f"\n[3/6] Checking Minecraft/Malmo instances...")
    print(f"   MalmoEnv multi-agent requires ONE Minecraft instance PER agent.")
    print(f"   You need {args.agents} Minecraft clients running on these ports:")
    print()

    missing_ports = []
    for i in range(args.agents):
        port = args.base_port + i
        if benchmark.check_minecraft_port(port):
            print(f"   [OK] Port {port} (Agent {i}, role={i}) - Minecraft detected")
        else:
            print(f"   [--] Port {port} (Agent {i}, role={i}) - NOT detected")
            missing_ports.append(port)

    if missing_ports:
        print(f"\n   [WARN] {len(missing_ports)} Minecraft instance(s) not detected.")
        print(f"   Launch each one in a separate terminal:")
        for port in missing_ports:
            print(f"     cd malmo\\Minecraft && launchClient.bat -port {port} -env")
        print()
        try:
            input("   Press Enter when all Minecraft instances are ready...")
        except EOFError:
            print("   (Non-interactive mode, continuing after 15s wait...)")
            time.sleep(15)

        # Re-check
        still_missing = []
        for port in missing_ports:
            if not benchmark.check_minecraft_port(port):
                still_missing.append(port)
        if still_missing:
            print(f"   [WARN] Ports still not detected: {still_missing}")
            print(f"   Continuing anyway (connections may fail)...")

    # Step 2: Create agents
    print(f"\n[4/6] Creating {args.agents} Qwen builder agents...")
    agents = benchmark.create_agents(num_agents=args.agents)

    if not agents:
        print("   [FAIL] No agents created!")
        sys.exit(1)

    # Step 3: Start agents
    print("\n[5/6] Starting PIANO architecture for agents...")
    started = benchmark.start_agents()
    print(f"   [OK] Started {started}/{len(agents)} agents")

    # Give agents time to initialize
    print("   Waiting for agents to initialize...")
    time.sleep(3)

    # Set the building goal
    print("\n   Setting city building goal...")
    benchmark.set_goal(args.goal)

    # Step 4: Start mission
    print(f"\n[6/6] Starting Minecraft mission (speed: {args.speed})...")
    print(f"   MsPerTick: {SPEED_PRESETS[args.speed]}ms")
    print(f"   Time limit: {args.time_limit} hours")
    print(f"   Spectator: {'Enabled' if not args.no_spectator else 'Disabled'}")

    if not benchmark.start_mission(
        speed=args.speed,
        include_spectator=not args.no_spectator,
        base_port=args.base_port,
        time_limit_hours=args.time_limit
    ):
        print("   [FAIL] Failed to start mission")
        print("   Make sure all Minecraft instances are in a world and ready")
        sys.exit(1)

    # Success!
    print("\n" + "="*60)
    print("[OK] BENCHMARK STARTED!")
    print("="*60)
    print(f"""
How to watch:

   Option 1: Minecraft Window
   - Each Minecraft window shows one agent's view
   - The role=0 window is the primary coordinator
   - Press F5 to toggle third-person view

   Option 2: Dashboard
   - Open: http://localhost:8501
   - See agent thoughts and decisions in real-time

   Option 3: API
   - Agent states: {args.server}/agents
   - Mission status: {args.server}/mission/status

To stop:
   - Press Ctrl+C here
   - Or run: stop_mission.bat
   - Or: curl -X POST {args.server}/mission/stop

Speed: {args.speed} ({SPEED_PRESETS[args.speed]}ms/tick)
   - 1x = normal, 2x = double, 5x = fast, 10x = very fast

""")

    # Monitor loop
    try:
        print("Monitoring... (Ctrl+C to stop)\n")
        while True:
            status = benchmark.get_status()
            mission = status.get('mission', {})

            if mission.get('mission_active'):
                connected = mission.get('connected_agents', 0)
                print(f"\r[BUILDING] {connected} agents connected    ", end='')
            else:
                print("\r[PAUSED] Mission not active                 ", end='')

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n[STOP] Stopping benchmark...")
        benchmark.cleanup()
        print("[OK] Benchmark stopped")


if __name__ == "__main__":
    main()
