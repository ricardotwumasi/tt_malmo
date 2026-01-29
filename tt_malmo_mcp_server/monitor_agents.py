#!/usr/bin/env python3
"""
Agent Monitor - Human oversight dashboard for AI agents.

Provides real-time monitoring of agent status, decisions, and metrics.
Run this alongside the MCP server to oversee agent behavior.

Usage:
    python monitor_agents.py [--interval 5] [--url http://localhost:8000]
"""

import argparse
import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def clear_screen():
    """Clear terminal screen."""
    print('\033[2J\033[H', end='')


def print_header():
    """Print dashboard header."""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  MALMO AI BENCHMARK - Agent Monitoring Dashboard")
    print("=" * 70)
    print(f"{Colors.ENDC}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_agent_status(agents: List[Dict[str, Any]]):
    """Print agent status table."""
    if not agents:
        print(f"  {Colors.YELLOW}No agents found. Create one with:{Colors.ENDC}")
        print("  curl -X POST http://localhost:8000/agents \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"name\":\"MyAgent\",\"llm_type\":\"gemini\",\"role\":0}'")
        return

    print(f"{Colors.BOLD}  AGENTS ({len(agents)} total){Colors.ENDC}")
    print("  " + "-" * 66)
    print(f"  {'Name':<20} {'LLM':<12} {'Role':<6} {'Status':<12}")
    print("  " + "-" * 66)

    for agent in agents:
        name = agent.get('name', 'Unknown')[:18]
        llm = agent.get('llm_type', 'unknown')
        role = str(agent.get('role', 0))
        status = agent.get('status', 'unknown')

        # Color status
        if status == 'running':
            status_str = f"{Colors.GREEN}{status}{Colors.ENDC}"
        elif status == 'created':
            status_str = f"{Colors.BLUE}{status}{Colors.ENDC}"
        elif status == 'stopped':
            status_str = f"{Colors.YELLOW}{status}{Colors.ENDC}"
        else:
            status_str = status

        print(f"  {name:<20} {llm:<12} {role:<6} {status_str:<12}")

    print()


def print_server_health(health: Dict[str, Any]):
    """Print server health status."""
    status = health.get('status', 'unknown')
    active = health.get('active_agents', 0)
    ws = health.get('connected_websockets', 0)

    color = Colors.GREEN if status == 'healthy' else Colors.RED

    print(f"{Colors.BOLD}  SERVER STATUS{Colors.ENDC}")
    print(f"  Status: {color}{status}{Colors.ENDC}")
    print(f"  Active Agents: {active}")
    print(f"  WebSocket Connections: {ws}")
    print()


def print_commands():
    """Print available commands."""
    print(f"{Colors.BOLD}  QUICK COMMANDS{Colors.ENDC}")
    print("  " + "-" * 66)
    print("  Create agent:  curl -X POST http://localhost:8000/agents \\")
    print("                   -H 'Content-Type: application/json' \\")
    print("                   -d '{\"name\":\"Agent\",\"llm_type\":\"gemini\",\"role\":0}'")
    print()
    print("  Start agent:   curl -X POST http://localhost:8000/agents/ID/start")
    print("  Stop agent:    curl -X POST http://localhost:8000/agents/ID/stop")
    print("  Delete agent:  curl -X DELETE http://localhost:8000/agents/ID")
    print()
    print(f"  {Colors.CYAN}Press Ctrl+C to exit{Colors.ENDC}")
    print()


async def fetch_data(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
    """Fetch data from API endpoint."""
    try:
        response = await client.get(url, timeout=5.0)
        return response.json()
    except Exception as e:
        return {'error': str(e)}


async def monitor_loop(base_url: str, interval: float):
    """Main monitoring loop."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                clear_screen()
                print_header()

                # Fetch health
                health = await fetch_data(client, f"{base_url}/health")
                if 'error' in health:
                    print(f"  {Colors.RED}Server Error: {health['error']}{Colors.ENDC}")
                    print(f"\n  Make sure the MCP server is running:")
                    print("  python -m uvicorn mcp_server.server:app --reload")
                else:
                    print_server_health(health)

                    # Fetch agents
                    agents = await fetch_data(client, f"{base_url}/agents")
                    if isinstance(agents, list):
                        print_agent_status(agents)

                print_commands()

                # Wait for next update
                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Exiting monitor...{Colors.ENDC}")
                break
            except Exception as e:
                print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}")
                await asyncio.sleep(interval)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Monitor AI agents in the Malmo MCP Server'
    )
    parser.add_argument(
        '--interval', '-i',
        type=float,
        default=3.0,
        help='Update interval in seconds (default: 3)'
    )
    parser.add_argument(
        '--url', '-u',
        type=str,
        default='http://localhost:8000',
        help='MCP Server URL (default: http://localhost:8000)'
    )

    args = parser.parse_args()

    print(f"Starting Agent Monitor...")
    print(f"Server: {args.url}")
    print(f"Refresh: every {args.interval}s")
    print("Press Ctrl+C to exit\n")

    try:
        asyncio.run(monitor_loop(args.url, args.interval))
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
