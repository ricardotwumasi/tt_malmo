"""
MCP Server - Main FastAPI server for coordinating AI agents in Malmo.

Provides:
- REST API for agent management
- WebSocket connections for real-time agent<->environment communication
- Agent lifecycle management
- Coordination with Malmo backend
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import asyncio
import uvicorn
from datetime import datetime

from .agent_manager import AgentManager
from .protocol.messages import (
    AgentCreateRequest,
    AgentCreateResponse,
    AgentStatusResponse,
    ObservationMessage,
    ActionMessage
)
from malmo_integration.environment_manager import MalmoEnvironmentManager
from malmo_integration.mission_builder import MissionBuilder

# Initialize FastAPI app
app = FastAPI(
    title="Malmo MCP Server",
    description="Model Context Protocol server for multi-agent Minecraft AI benchmarking",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent manager
agent_manager = AgentManager()

# Environment managers for connected agents (agent_id -> MalmoEnvironmentManager)
env_managers: Dict[str, MalmoEnvironmentManager] = {}

# Mission state
mission_active = False
mission_xml = None

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for agents."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, agent_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        print(f"WebSocket connected for agent: {agent_id}")

    def disconnect(self, agent_id: str):
        """Remove WebSocket connection."""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            print(f"WebSocket disconnected for agent: {agent_id}")

    async def send_message(self, agent_id: str, message: dict):
        """Send message to specific agent."""
        if agent_id in self.active_connections:
            websocket = self.active_connections[agent_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected agents."""
        for agent_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {agent_id}: {e}")


connection_manager = ConnectionManager()


# REST API Endpoints

@app.get("/")
async def root():
    """Root endpoint - server info."""
    return {
        "name": "Malmo MCP Server",
        "version": "0.1.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_agents": len(agent_manager.agents),
        "connected_websockets": len(connection_manager.active_connections)
    }


@app.post("/agents", response_model=AgentCreateResponse)
async def create_agent(request: AgentCreateRequest):
    """
    Create a new agent.

    Args:
        request: Agent creation request

    Returns:
        Agent creation response with agent_id
    """
    try:
        agent_id = await agent_manager.create_agent(
            name=request.name,
            llm_type=request.llm_type,
            role=request.role,
            traits=request.traits
        )

        return AgentCreateResponse(
            agent_id=agent_id,
            name=request.name,
            status="created",
            message=f"Agent {request.name} created successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents", response_model=List[AgentStatusResponse])
async def list_agents():
    """
    List all agents.

    Returns:
        List of agent status responses
    """
    agents = agent_manager.list_agents()
    return [
        AgentStatusResponse(
            agent_id=agent['agent_id'],
            name=agent['name'],
            status=agent['status'],
            llm_type=agent['llm_type'],
            role=agent['role']
        )
        for agent in agents
    ]


@app.get("/agents/{agent_id}", response_model=AgentStatusResponse)
async def get_agent(agent_id: str):
    """
    Get agent status.

    Args:
        agent_id: Agent ID

    Returns:
        Agent status response
    """
    agent = agent_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentStatusResponse(
        agent_id=agent['agent_id'],
        name=agent['name'],
        status=agent['status'],
        llm_type=agent['llm_type'],
        role=agent['role']
    )


@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """
    Delete an agent.

    Args:
        agent_id: Agent ID

    Returns:
        Deletion confirmation
    """
    success = await agent_manager.delete_agent(agent_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "agent_id": agent_id,
        "status": "deleted",
        "message": f"Agent {agent_id} deleted successfully"
    }


@app.post("/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """
    Start an agent's PIANO architecture.

    Args:
        agent_id: Agent ID

    Returns:
        Start confirmation
    """
    success = await agent_manager.start_agent(agent_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "agent_id": agent_id,
        "status": "started",
        "message": f"Agent {agent_id} PIANO architecture started"
    }


@app.post("/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """
    Stop an agent's PIANO architecture.

    Args:
        agent_id: Agent ID

    Returns:
        Stop confirmation
    """
    success = await agent_manager.stop_agent(agent_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "agent_id": agent_id,
        "status": "stopped",
        "message": f"Agent {agent_id} PIANO architecture stopped"
    }


@app.post("/agents/{agent_id}/goal")
async def set_agent_goal(agent_id: str, goal: dict):
    """
    Set a goal for an agent.

    Args:
        agent_id: Agent ID
        goal: Goal dictionary with 'description' and optional 'priority'

    Returns:
        Confirmation with goal details
    """
    if agent_id not in agent_manager.agent_states:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent_state = agent_manager.agent_states[agent_id]

    # Create goal object
    new_goal = {
        'description': goal.get('description', 'No description'),
        'priority': goal.get('priority', 10),  # High priority for user-set goals
        'source': 'user',
        'timestamp': datetime.now().isoformat()
    }

    # Add to agent's current goals (at the front for high priority)
    with agent_state.lock:
        agent_state.current_goals.insert(0, new_goal)
        # Keep only top 5 goals
        agent_state.current_goals = agent_state.current_goals[:5]

    agent_name = agent_manager.agents[agent_id]['name']
    print(f"[{agent_name}] New goal set: {new_goal['description']}")

    return {
        "agent_id": agent_id,
        "goal": new_goal,
        "message": f"Goal set for agent {agent_name}"
    }


@app.post("/agents/broadcast-goal")
async def broadcast_goal(goal: dict):
    """
    Set the same goal for all agents.

    Args:
        goal: Goal dictionary with 'description' and optional 'priority'

    Returns:
        Confirmation with affected agents
    """
    affected_agents = []

    for agent_id, agent_state in agent_manager.agent_states.items():
        new_goal = {
            'description': goal.get('description', 'No description'),
            'priority': goal.get('priority', 10),
            'source': 'user_broadcast',
            'timestamp': datetime.now().isoformat()
        }

        with agent_state.lock:
            agent_state.current_goals.insert(0, new_goal)
            agent_state.current_goals = agent_state.current_goals[:5]

        agent_name = agent_manager.agents[agent_id]['name']
        affected_agents.append(agent_name)
        print(f"[{agent_name}] Broadcast goal: {new_goal['description']}")

    return {
        "goal": goal.get('description'),
        "affected_agents": affected_agents,
        "message": f"Goal broadcast to {len(affected_agents)} agents"
    }


# Mission Control Endpoints

@app.post("/mission/start")
async def start_mission(base_port: int = 9000):
    """
    Start Malmo mission with all running agents.

    This connects running PIANO agents to actual Minecraft characters.
    Each agent gets assigned a sequential port starting from base_port.

    Args:
        base_port: Starting port for Malmo connections (default 9000)

    Returns:
        Mission start status with connected agent count
    """
    global mission_active, mission_xml, env_managers

    if mission_active:
        raise HTTPException(400, "Mission already active. Stop current mission first.")

    # Get all running agents
    agents = agent_manager.list_agents()
    running_agents = [a for a in agents if a['status'] == 'running']

    if not running_agents:
        raise HTTPException(400, "No running agents. Start agents first via /agents/{id}/start")

    # Generate mission XML for all running agents
    builder = MissionBuilder()
    mission_xml = builder.create_benchmark_mission(num_agents=len(running_agents))

    print(f"\n{'='*60}")
    print(f"🚀 Starting Malmo Mission with {len(running_agents)} agents")
    print(f"{'='*60}\n")

    connected_agents = []
    failed_agents = []

    # Connect each agent to Malmo on sequential ports
    for i, agent in enumerate(running_agents):
        agent_id = agent['agent_id']
        port = base_port + i

        try:
            # Create environment manager for this agent
            env_manager = MalmoEnvironmentManager(
                mission_xml=mission_xml,
                port=port
            )

            # Connect to Malmo
            env_manager.connect()

            # Store for later cleanup and control
            env_managers[agent_id] = env_manager

            # Start the agent control loop in background
            agent_state = agent_manager.agent_states[agent_id]
            asyncio.create_task(
                env_manager.run_agent_loop(
                    agent_state=agent_state,
                    agent_manager=agent_manager,
                    agent_id=agent_id,
                    max_steps=10000  # Long mission
                )
            )

            connected_agents.append({
                'agent_id': agent_id,
                'name': agent['name'],
                'port': port,
                'status': 'connected'
            })

            print(f"✅ Agent {agent['name']} connected on port {port}")

        except Exception as e:
            failed_agents.append({
                'agent_id': agent_id,
                'name': agent['name'],
                'port': port,
                'error': str(e)
            })
            print(f"❌ Failed to connect {agent['name']} on port {port}: {e}")

    if connected_agents:
        mission_active = True
        print(f"\n🎮 Mission started! {len(connected_agents)} agents in Minecraft world\n")

    return {
        "status": "mission_started" if connected_agents else "mission_failed",
        "connected_agents": len(connected_agents),
        "failed_agents": len(failed_agents),
        "agents": connected_agents,
        "failures": failed_agents,
        "message": f"Connected {len(connected_agents)}/{len(running_agents)} agents to Malmo"
    }


@app.post("/mission/stop")
async def stop_mission():
    """
    Stop the current Malmo mission.

    Disconnects all agents from Minecraft and returns them to thinking-only mode.
    Agents keep running their PIANO architecture but no longer control Minecraft characters.

    Returns:
        Mission stop status
    """
    global mission_active, mission_xml, env_managers

    if not mission_active:
        raise HTTPException(400, "No active mission to stop")

    print(f"\n{'='*60}")
    print(f"🛑 Stopping Malmo Mission")
    print(f"{'='*60}\n")

    disconnected = []

    # Stop and close all environment managers
    for agent_id, env_manager in env_managers.items():
        try:
            env_manager.stop()
            env_manager.close()

            agent = agent_manager.get_agent(agent_id)
            agent_name = agent['name'] if agent else agent_id

            disconnected.append({
                'agent_id': agent_id,
                'name': agent_name,
                'status': 'disconnected'
            })

            print(f"✅ Disconnected {agent_name}")

        except Exception as e:
            print(f"⚠️  Error disconnecting {agent_id}: {e}")

    # Clear state
    env_managers.clear()
    mission_active = False
    mission_xml = None

    print(f"\n🏁 Mission stopped. Agents returned to thinking-only mode.\n")

    return {
        "status": "mission_stopped",
        "disconnected_agents": len(disconnected),
        "agents": disconnected,
        "message": f"Disconnected {len(disconnected)} agents from Malmo"
    }


@app.get("/mission/status")
async def mission_status():
    """
    Get current mission status.

    Returns:
        Mission status including active state and connected agents
    """
    connected_count = len(env_managers)
    connected_info = []

    for agent_id, env_manager in env_managers.items():
        agent = agent_manager.get_agent(agent_id)
        agent_name = agent['name'] if agent else agent_id

        connected_info.append({
            'agent_id': agent_id,
            'name': agent_name,
            'port': env_manager.port,
            'running': env_manager.running
        })

    return {
        "mission_active": mission_active,
        "connected_agents": connected_count,
        "agents": connected_info
    }


# WebSocket Endpoints

@app.websocket("/ws/agent/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for agent communication.

    Handles bidirectional communication:
    - Server -> Agent: Observations from Malmo
    - Agent -> Server: Actions to execute in Malmo

    Args:
        websocket: WebSocket connection
        agent_id: Agent ID
    """
    # Verify agent exists
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        await websocket.close(code=1008, reason="Agent not found")
        return

    await connection_manager.connect(agent_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get('type')

            if message_type == 'observation':
                # Process observation from Malmo
                observation = ObservationMessage(**data)
                await agent_manager.process_observation(agent_id, observation.observation)

            elif message_type == 'action_result':
                # Process action result
                await agent_manager.process_action_result(
                    agent_id,
                    data.get('action'),
                    data.get('success', True)
                )

            else:
                print(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        connection_manager.disconnect(agent_id)
        print(f"Agent {agent_id} disconnected")

    except Exception as e:
        print(f"WebSocket error for agent {agent_id}: {e}")
        connection_manager.disconnect(agent_id)


@app.websocket("/ws/broadcast")
async def broadcast_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for broadcast messages.

    Used by Malmo server to send global updates.

    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            message_type = data.get('type')

            if message_type == 'global_update':
                # Broadcast to all agents
                await connection_manager.broadcast(data)

    except WebSocketDisconnect:
        print("Broadcast client disconnected")

    except Exception as e:
        print(f"Broadcast WebSocket error: {e}")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the MCP server.

    Args:
        host: Host address
        port: Port number
    """
    print(f"Starting Malmo MCP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
