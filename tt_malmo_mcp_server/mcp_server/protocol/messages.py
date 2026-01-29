"""
Protocol Messages - Data schemas for MCP server communication.

Defines Pydantic models for REST API and WebSocket messages.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# Agent Management Messages

class AgentCreateRequest(BaseModel):
    """Request to create a new agent."""
    name: str = Field(..., description="Agent name")
    llm_type: str = Field(default="claude", description="LLM type (claude or gemini)")
    role: int = Field(default=0, description="Malmo role number")
    traits: List[str] = Field(default=["curious", "cooperative"], description="Agent personality traits")


class AgentCreateResponse(BaseModel):
    """Response after creating an agent."""
    agent_id: str = Field(..., description="Generated agent ID")
    name: str = Field(..., description="Agent name")
    status: str = Field(..., description="Agent status")
    message: str = Field(..., description="Status message")


class AgentStatusResponse(BaseModel):
    """Agent status information."""
    agent_id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name")
    status: str = Field(..., description="Agent status (created/running/stopped)")
    llm_type: str = Field(..., description="LLM type")
    role: int = Field(..., description="Malmo role number")


# WebSocket Messages

class ObservationMessage(BaseModel):
    """Observation from Malmo environment."""
    type: str = Field(default="observation", description="Message type")
    agent_id: str = Field(..., description="Agent ID")
    observation: Dict[str, Any] = Field(..., description="Observation data from Malmo")
    timestamp: str = Field(..., description="Timestamp of observation")


class ActionMessage(BaseModel):
    """Action to execute in Malmo."""
    type: str = Field(default="action", description="Message type")
    agent_id: str = Field(..., description="Agent ID")
    action: str = Field(..., description="Action type (move, attack, use, etc.)")
    parameters: Dict[str, Any] = Field(default={}, description="Action parameters")
    timestamp: str = Field(..., description="Timestamp of action")


class ActionResultMessage(BaseModel):
    """Result of action execution."""
    type: str = Field(default="action_result", description="Message type")
    agent_id: str = Field(..., description="Agent ID")
    action: str = Field(..., description="Action that was executed")
    success: bool = Field(..., description="Whether action succeeded")
    message: Optional[str] = Field(None, description="Result message")
    timestamp: str = Field(..., description="Timestamp of result")


class ChatMessage(BaseModel):
    """Chat message between agents."""
    type: str = Field(default="chat", description="Message type")
    from_agent_id: str = Field(..., description="Sender agent ID")
    to_agent_id: Optional[str] = Field(None, description="Recipient agent ID (None for broadcast)")
    message: str = Field(..., description="Chat message content")
    timestamp: str = Field(..., description="Timestamp of message")


# Benchmarking Messages

class MetricsUpdateMessage(BaseModel):
    """Update of agent metrics."""
    type: str = Field(default="metrics_update", description="Message type")
    agent_id: str = Field(..., description="Agent ID")
    metrics: Dict[str, Any] = Field(..., description="Metrics data")
    timestamp: str = Field(..., description="Timestamp of update")


# Global Messages

class GlobalUpdateMessage(BaseModel):
    """Global update broadcast to all agents."""
    type: str = Field(default="global_update", description="Message type")
    event: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: str = Field(..., description="Timestamp of update")
