"""
Multi-Agent Launcher - Spawns PIANO agents in Minecraft via MalmoEnv.

This script:
1. Fetches running agents from MCP server
2. Generates multi-agent mission XML via MissionBuilder
3. Connects each agent to Malmo on sequential ports (9000, 9001, 9002, ...)
4. Bridges agent decisions to Malmo commands
5. Feeds Minecraft observations back to agent state

Usage:
    python launch_multi_agent.py [--server-url http://localhost:8080] [--base-port 9000]
"""

import asyncio
import argparse
import sys
import requests
import time
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, '.')

from malmo_integration.environment_manager import MalmoEnvironmentManager
from malmo_integration.mission_builder import MissionBuilder


class MultiAgentLauncher:
    """
    Launches multiple agents from MCP server into Minecraft world.
    """

    def __init__(self, server_url: str = "http://localhost:8080", base_port: int = 9000):
        """
        Initialize Multi-Agent Launcher.

        Args:
            server_url: URL of the MCP server
            base_port: Starting port for Malmo connections
        """
        self.server_url = server_url.rstrip('/')
        self.base_port = base_port
        self.env_managers: Dict[str, MalmoEnvironmentManager] = {}
        self.mission_xml = None

    def check_server_health(self) -> bool:
        """
        Check if MCP server is running and healthy.

        Returns:
            True if server is healthy
        """
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ MCP Server healthy")
                print(f"   Active agents: {data.get('active_agents', 0)}")
                print(f"   WebSocket connections: {data.get('connected_websockets', 0)}")
                return True
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to MCP server at {self.server_url}")
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
        return False

    def get_running_agents(self) -> List[Dict[str, Any]]:
        """
        Fetch list of running agents from MCP server.

        Returns:
            List of running agent data
        """
        try:
            response = requests.get(f"{self.server_url}/agents", timeout=5)
            if response.status_code == 200:
                agents = response.json()
                running = [a for a in agents if a.get('status') == 'running']
                print(f"\n📋 Found {len(running)} running agents:")
                for agent in running:
                    print(f"   - {agent['name']} (ID: {agent['agent_id'][:8]}...)")
                return running
        except Exception as e:
            print(f"❌ Failed to fetch agents: {e}")
        return []

    def start_mission_via_api(self) -> bool:
        """
        Start mission using MCP server API endpoint.

        This is the preferred method as it keeps everything coordinated
        through the MCP server.

        Returns:
            True if mission started successfully
        """
        try:
            print(f"\n🚀 Starting mission via API...")
            response = requests.post(
                f"{self.server_url}/mission/start",
                params={"base_port": self.base_port},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ {data.get('message', 'Mission started')}")

                if data.get('connected_agents', 0) > 0:
                    print(f"\n🎮 Agents now active in Minecraft:")
                    for agent in data.get('agents', []):
                        print(f"   - {agent['name']} on port {agent['port']}")
                    return True
                else:
                    print("⚠️  No agents connected")
                    return False
            else:
                error = response.json().get('detail', 'Unknown error')
                print(f"❌ Failed to start mission: {error}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to MCP server")
        except Exception as e:
            print(f"❌ Error starting mission: {e}")
        return False

    def stop_mission_via_api(self) -> bool:
        """
        Stop mission using MCP server API endpoint.

        Returns:
            True if mission stopped successfully
        """
        try:
            print(f"\n🛑 Stopping mission via API...")
            response = requests.post(f"{self.server_url}/mission/stop", timeout=10)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ {data.get('message', 'Mission stopped')}")
                return True
            else:
                error = response.json().get('detail', 'Unknown error')
                print(f"⚠️  {error}")
                return False

        except Exception as e:
            print(f"❌ Error stopping mission: {e}")
        return False

    def get_mission_status(self) -> Dict[str, Any]:
        """
        Get current mission status from MCP server.

        Returns:
            Mission status dictionary
        """
        try:
            response = requests.get(f"{self.server_url}/mission/status", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"⚠️  Could not get mission status: {e}")
        return {"mission_active": False, "connected_agents": 0}


def main():
    """Main entry point for multi-agent launcher."""
    parser = argparse.ArgumentParser(
        description="Launch PIANO agents into Minecraft via MalmoEnv"
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:8080",
        help="MCP server URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--base-port",
        type=int,
        default=9000,
        help="Starting Malmo port (default: 9000)"
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop current mission instead of starting"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show mission status and exit"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🎮 PIANO Multi-Agent Minecraft Launcher")
    print("=" * 60)

    launcher = MultiAgentLauncher(
        server_url=args.server_url,
        base_port=args.base_port
    )

    # Check server health first
    if not launcher.check_server_health():
        print("\n❌ Please ensure MCP server is running:")
        print("   python -m mcp_server.server")
        sys.exit(1)

    # Handle status request
    if args.status:
        status = launcher.get_mission_status()
        print(f"\n📊 Mission Status:")
        print(f"   Active: {status.get('mission_active', False)}")
        print(f"   Connected agents: {status.get('connected_agents', 0)}")

        for agent in status.get('agents', []):
            running = "🟢" if agent.get('running') else "🔴"
            print(f"   {running} {agent['name']} (port {agent['port']})")
        sys.exit(0)

    # Handle stop request
    if args.stop:
        launcher.stop_mission_via_api()
        sys.exit(0)

    # Start mission
    agents = launcher.get_running_agents()
    if not agents:
        print("\n❌ No running agents found.")
        print("   Start agents first via dashboard or API:")
        print("   curl -X POST http://localhost:8080/agents/{id}/start")
        sys.exit(1)

    # Verify Minecraft is running
    print(f"\n⚠️  Ensure Minecraft is running with Malmo mod:")
    print(f"   cd malmo\\Minecraft && .\\launchClient.bat -port {args.base_port} -env")
    print()

    # Give user a moment to verify
    input("Press Enter when Minecraft is ready...")

    # Start mission via API
    if launcher.start_mission_via_api():
        print("\n" + "=" * 60)
        print("✅ Mission launched successfully!")
        print("=" * 60)
        print("\n📺 Monitor agents:")
        print(f"   - Dashboard: http://localhost:8501")
        print(f"   - API: {args.server_url}/mission/status")
        print("\n🛑 To stop mission:")
        print(f"   python launch_multi_agent.py --stop")
        print("   or: curl -X POST http://localhost:8080/mission/stop")
    else:
        print("\n❌ Mission launch failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
