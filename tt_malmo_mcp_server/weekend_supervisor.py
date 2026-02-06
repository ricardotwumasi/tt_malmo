#!/usr/bin/env python3
"""
Weekend Supervisor - Top-level watchdog for autonomous multi-day benchmark runs.

Monitors and restarts:
- Ollama (LLM server on port 11434)
- MCP server (FastAPI on port 8080)
- Minecraft ports (pre-launched by user, only monitored)
- Mission health (agents alive and running)

Features:
- 5-minute cooldown between full restarts to prevent restart storms
- Logs everything to logs/weekend_run/supervisor_YYYYMMDD_HHMMSS.log
- Graceful Ctrl+C shutdown

Usage:
    python weekend_supervisor.py --speed 2x --agents 3 --time-limit 60 --check-interval 60
"""

import argparse
import logging
import os
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests


# City building goal (same as run_city_benchmark.py)
CITY_BUILDING_GOAL = """Build a village with houses and paths. You are already at the build site. Start placing blocks immediately. Use the build cycle: select a material, then place_block, then move or turn, then place_block again. Coordinate with other agents to build in different areas."""


class WeekendSupervisor:
    """Top-level process supervisor for autonomous weekend benchmark runs."""

    def __init__(self, args):
        self.speed = args.speed
        self.num_agents = args.agents
        self.time_limit_hours = args.time_limit
        self.check_interval = args.check_interval
        self.base_port = args.base_port
        self.server_url = args.server
        self.mcp_port = int(self.server_url.rsplit(':', 1)[-1])

        # State
        self.mcp_process = None
        self.ollama_process = None
        self.last_full_restart = datetime.min
        self.full_restart_cooldown = timedelta(minutes=5)
        self.shutdown_requested = False
        self.start_time = datetime.now()

        # Set up logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure dual logging: file + console."""
        log_dir = Path(__file__).parent / "logs" / "weekend_run"
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"supervisor_{timestamp}.log"

        # Create logger
        self.logger = logging.getLogger("supervisor")
        self.logger.setLevel(logging.DEBUG)

        # File handler (detailed)
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        # Console handler (info+)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        ))

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

        self.logger.info(f"Supervisor log: {log_file}")

    # --- Health Checks ---

    def check_ollama(self) -> bool:
        """Check if Ollama is responding on port 11434."""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def check_mcp_server(self) -> bool:
        """Check if MCP server is responding on its health endpoint."""
        try:
            r = requests.get(f"{self.server_url}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def check_minecraft_port(self, port: int) -> bool:
        """Check if a Minecraft instance is listening on the given port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def get_mission_status(self) -> dict:
        """Get mission status from MCP server. Returns empty dict on failure."""
        try:
            r = requests.get(f"{self.server_url}/mission/status", timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return {}

    def get_agent_list(self) -> list:
        """Get list of agents from MCP server."""
        try:
            r = requests.get(f"{self.server_url}/agents", timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return []

    # --- Component Management ---

    def start_ollama(self):
        """Start Ollama server as a background process."""
        if self.check_ollama():
            self.logger.info("Ollama already running")
            return True

        self.logger.info("Starting Ollama server...")
        try:
            self.ollama_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    if sys.platform == 'win32' else 0
            )
            # Wait for Ollama to become responsive
            for i in range(30):
                time.sleep(1)
                if self.check_ollama():
                    self.logger.info(f"Ollama started (took {i+1}s)")
                    return True
            self.logger.error("Ollama failed to start within 30s")
            return False
        except FileNotFoundError:
            self.logger.error("Ollama not found in PATH. Install from https://ollama.com")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start Ollama: {e}")
            return False

    def start_mcp_server(self):
        """Start the MCP server as a background subprocess."""
        if self.check_mcp_server():
            self.logger.info("MCP server already running")
            return True

        self.logger.info("Starting MCP server...")

        # Find the project directory (where this script lives)
        project_dir = Path(__file__).parent

        # Determine Python executable (prefer venv)
        venv_python = project_dir / "venv_win" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = project_dir / "venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = project_dir / "venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = Path(sys.executable)  # fallback to current python

        try:
            self.mcp_process = subprocess.Popen(
                [
                    str(venv_python), "-m", "uvicorn",
                    "mcp_server.server:app",
                    "--host", "0.0.0.0",
                    "--port", str(self.mcp_port)
                ],
                cwd=str(project_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    if sys.platform == 'win32' else 0
            )

            # Wait for server to become responsive
            for i in range(30):
                time.sleep(1)
                if self.check_mcp_server():
                    self.logger.info(f"MCP server started on port {self.mcp_port} (took {i+1}s)")
                    return True

            self.logger.error("MCP server failed to start within 30s")
            return False

        except Exception as e:
            self.logger.error(f"Failed to start MCP server: {e}")
            return False

    def stop_mcp_server(self):
        """Stop the MCP server subprocess."""
        if self.mcp_process and self.mcp_process.poll() is None:
            self.logger.info("Stopping MCP server...")
            self.mcp_process.terminate()
            try:
                self.mcp_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.mcp_process.kill()
            self.mcp_process = None

    # --- Benchmark Orchestration ---

    def start_benchmark(self) -> bool:
        """Start the full benchmark: create agents, start PIANO, set goal, start mission.

        Returns True if the benchmark was started successfully.
        """
        self.logger.info(f"Starting benchmark: {self.num_agents} agents, "
                         f"speed={self.speed}, time_limit={self.time_limit_hours}h")

        # Stop any existing mission first
        try:
            requests.post(f"{self.server_url}/mission/stop", timeout=10)
            time.sleep(2)
        except Exception:
            pass

        # Delete any existing agents
        for agent in self.get_agent_list():
            try:
                requests.delete(
                    f"{self.server_url}/agents/{agent['agent_id']}", timeout=10
                )
            except Exception:
                pass
        time.sleep(1)

        # Create agents
        agent_names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        builder_traits = [
            ["architect", "creative", "organized"],
            ["builder", "efficient", "cooperative"],
            ["designer", "detail-oriented", "helpful"],
            ["engineer", "strategic", "methodical"],
            ["craftsman", "resourceful", "patient"],
        ]

        agent_ids = []
        for i in range(self.num_agents):
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
                    aid = r.json()['agent_id']
                    agent_ids.append(aid)
                    self.logger.info(f"Created agent {name} ({aid[:8]}...)")
                else:
                    self.logger.error(f"Failed to create {name}: {r.text}")
                    return False
            except Exception as e:
                self.logger.error(f"Error creating agent {name}: {e}")
                return False

        # Start PIANO architecture for each agent
        for aid in agent_ids:
            try:
                r = requests.post(
                    f"{self.server_url}/agents/{aid}/start", timeout=10
                )
                if r.status_code != 200:
                    self.logger.warning(f"Failed to start agent {aid[:8]}")
            except Exception as e:
                self.logger.warning(f"Error starting agent {aid[:8]}: {e}")

        time.sleep(3)

        # Set the building goal
        try:
            r = requests.post(
                f"{self.server_url}/agents/broadcast-goal",
                json={"description": CITY_BUILDING_GOAL, "priority": 10},
                timeout=10
            )
            if r.status_code == 200:
                self.logger.info("City building goal set for all agents")
        except Exception as e:
            self.logger.warning(f"Error setting goal: {e}")

        # Start the mission
        try:
            r = requests.post(
                f"{self.server_url}/mission/start",
                params={
                    "base_port": self.base_port,
                    "mission_type": "city_building",
                    "speed": self.speed,
                    "include_spectator": False,
                    "time_limit_hours": self.time_limit_hours
                },
                timeout=120  # Mission start can take a while
            )
            if r.status_code == 200:
                data = r.json()
                connected = data.get('connected_agents', 0)
                self.logger.info(f"Mission started! {connected} agents connected")
                return connected > 0
            else:
                error = r.json().get('detail', r.text) if r.text else 'Unknown'
                self.logger.error(f"Mission start failed: {error}")
                return False
        except Exception as e:
            self.logger.error(f"Error starting mission: {e}")
            return False

    def should_full_restart(self) -> bool:
        """Check if enough time has passed since last full restart."""
        return datetime.now() - self.last_full_restart > self.full_restart_cooldown

    def do_full_restart(self):
        """Perform a full restart: stop MCP server, restart it, then restart benchmark."""
        if not self.should_full_restart():
            cooldown_remaining = (self.last_full_restart + self.full_restart_cooldown
                                  - datetime.now())
            self.logger.warning(f"Full restart cooldown active. "
                                f"Wait {cooldown_remaining.seconds}s more")
            return

        self.logger.info("=" * 60)
        self.logger.info("FULL RESTART triggered")
        self.logger.info("=" * 60)

        self.last_full_restart = datetime.now()

        # Stop existing MCP server
        self.stop_mcp_server()
        time.sleep(5)

        # Restart MCP server
        if not self.start_mcp_server():
            self.logger.error("Failed to restart MCP server")
            return

        time.sleep(5)

        # Restart benchmark
        if not self.start_benchmark():
            self.logger.error("Failed to restart benchmark")
        else:
            self.logger.info("Full restart completed successfully")

    # --- Main Loop ---

    def run(self):
        """Main supervisor loop."""
        self.logger.info("=" * 60)
        self.logger.info("WEEKEND SUPERVISOR starting")
        self.logger.info(f"  Agents: {self.num_agents}")
        self.logger.info(f"  Speed: {self.speed}")
        self.logger.info(f"  Time limit: {self.time_limit_hours} hours")
        self.logger.info(f"  Check interval: {self.check_interval}s")
        self.logger.info(f"  MCP server: {self.server_url}")
        self.logger.info(f"  Base port: {self.base_port}")
        self.logger.info("=" * 60)

        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        if sys.platform == 'win32':
            signal.signal(signal.SIGBREAK, self._signal_handler)

        # Step 1: Ensure Ollama is running
        self.logger.info("[STARTUP] Checking Ollama...")
        if not self.start_ollama():
            self.logger.error("Cannot start Ollama. Exiting.")
            return

        # Step 2: Ensure MCP server is running
        self.logger.info("[STARTUP] Checking MCP server...")
        if not self.start_mcp_server():
            self.logger.error("Cannot start MCP server. Exiting.")
            return

        # Step 3: Check Minecraft ports
        self.logger.info("[STARTUP] Checking Minecraft ports...")
        all_ports_ok = True
        for i in range(self.num_agents):
            port = self.base_port + i
            if self.check_minecraft_port(port):
                self.logger.info(f"  Port {port} (Agent {i}): OK")
            else:
                self.logger.warning(f"  Port {port} (Agent {i}): NOT DETECTED")
                all_ports_ok = False

        if not all_ports_ok:
            self.logger.warning(
                "Not all Minecraft ports detected. "
                "Make sure Minecraft instances are running. "
                "Continuing anyway..."
            )

        # Step 4: Start the benchmark
        self.logger.info("[STARTUP] Starting benchmark...")
        if not self.start_benchmark():
            self.logger.error("Initial benchmark start failed. Will retry in monitor loop.")

        self.last_full_restart = datetime.now()

        # Step 5: Monitor loop
        self.logger.info("[MONITOR] Entering monitor loop "
                         f"(checking every {self.check_interval}s)")

        while not self.shutdown_requested:
            time.sleep(self.check_interval)

            if self.shutdown_requested:
                break

            elapsed = datetime.now() - self.start_time
            self.logger.debug(f"Monitor check (uptime: {elapsed})")

            # Check Ollama
            if not self.check_ollama():
                self.logger.warning("Ollama is DOWN — restarting")
                self.start_ollama()
                continue

            # Check MCP server
            if not self.check_mcp_server():
                self.logger.warning("MCP server is DOWN — full restart")
                self.do_full_restart()
                continue

            # Check Minecraft ports (warning only, not auto-managed)
            for i in range(self.num_agents):
                port = self.base_port + i
                if not self.check_minecraft_port(port):
                    self.logger.warning(
                        f"Minecraft port {port} is DOWN. "
                        f"Agent {i} may be affected. "
                        f"(Minecraft instances must be restarted manually)"
                    )

            # Check mission status
            status = self.get_mission_status()

            if not status.get('mission_active'):
                self.logger.warning("Mission not active — triggering full restart")
                self.do_full_restart()
                continue

            # Check agent threads
            agents = status.get('agents', [])
            all_dead = True
            for agent_info in agents:
                name = agent_info.get('name', 'unknown')
                running = agent_info.get('running', False)
                thread_alive = agent_info.get('thread_alive', False)

                if running and thread_alive:
                    all_dead = False
                else:
                    self.logger.warning(
                        f"Agent {name}: running={running}, "
                        f"thread_alive={thread_alive}"
                    )

            if all_dead and len(agents) > 0:
                self.logger.warning("ALL agent threads are dead — "
                                    "triggering full restart")
                self._consecutive_dead_checks = 0
                self.do_full_restart()
                continue

            # Track consecutive checks where ANY agent is dead.
            # The in-server watchdog may fail to restart agents (e.g. role 0
            # can't rejoin an existing mission). If an agent stays dead for
            # 2+ checks (~2 minutes), force a full mission restart.
            alive_count = sum(1 for a in agents
                              if a.get('running') and a.get('thread_alive'))
            dead_count = len(agents) - alive_count

            if dead_count > 0:
                if not hasattr(self, '_consecutive_dead_checks'):
                    self._consecutive_dead_checks = 0
                self._consecutive_dead_checks += 1
                self.logger.warning(
                    f"{dead_count}/{len(agents)} agent(s) dead "
                    f"(consecutive checks: {self._consecutive_dead_checks})"
                )
                if self._consecutive_dead_checks >= 2:
                    self.logger.warning(
                        f"Agent(s) dead for {self._consecutive_dead_checks} "
                        f"consecutive checks — watchdog failed, "
                        f"triggering full mission restart"
                    )
                    self._consecutive_dead_checks = 0
                    self.do_full_restart()
                    continue
            else:
                self._consecutive_dead_checks = 0

            self.logger.info(
                f"[OK] {alive_count}/{len(agents)} agents alive | "
                f"Uptime: {elapsed}"
            )

        # Shutdown
        self._shutdown()

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C / SIGTERM gracefully."""
        self.logger.info(f"Received signal {signum} — shutting down...")
        self.shutdown_requested = True

    def _shutdown(self):
        """Clean shutdown of all managed processes."""
        self.logger.info("=" * 60)
        self.logger.info("SUPERVISOR SHUTDOWN")
        self.logger.info("=" * 60)

        # Stop mission
        try:
            requests.post(f"{self.server_url}/mission/stop", timeout=10)
            self.logger.info("Mission stopped")
        except Exception:
            pass

        # Stop MCP server (only if we started it)
        self.stop_mcp_server()

        # We don't stop Ollama — it may be shared with other processes

        elapsed = datetime.now() - self.start_time
        self.logger.info(f"Total uptime: {elapsed}")
        self.logger.info("Supervisor shutdown complete")


def main():
    parser = argparse.ArgumentParser(
        description="Weekend Supervisor - autonomous multi-day benchmark watchdog"
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
        "--time-limit", type=float, default=60.0,
        help="Mission time limit in hours (default: 60)"
    )
    parser.add_argument(
        "--check-interval", type=int, default=60,
        help="Seconds between health checks (default: 60)"
    )
    parser.add_argument(
        "--base-port", type=int, default=9000,
        help="Starting Malmo port (default: 9000)"
    )
    parser.add_argument(
        "--server", default="http://localhost:8080",
        help="MCP server URL (default: http://localhost:8080)"
    )

    args = parser.parse_args()

    print("""
============================================================
     WEEKEND SUPERVISOR - Autonomous Benchmark Watchdog
============================================================
  Monitors Ollama, MCP server, Minecraft, and agents.
  Auto-restarts any crashed component.
  Press Ctrl+C for graceful shutdown.
============================================================
""")

    supervisor = WeekendSupervisor(args)
    supervisor.run()


if __name__ == "__main__":
    main()
