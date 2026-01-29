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
