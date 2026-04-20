"""FastAPI server for AgentMind multi-agent collaboration.

This module provides a production-ready REST API for running multi-agent
collaborations with streaming support, observability, and error handling.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider, LiteLLMProvider
from agentmind.utils.observability import Tracer
from agentmind.utils.retry import RetryConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AgentMind API", description="Multi-agent collaboration framework API", version="0.3.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (use Redis/DB in production)
sessions: Dict[str, Dict[str, Any]] = {}


# Request/Response Models
class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    tools: List[str] = Field(default_factory=list, description="Available tools")


class CollaborationRequest(BaseModel):
    """Request to start a collaboration."""

    task: str = Field(..., description="Task description")
    agents: List[AgentConfig] = Field(..., description="Agent configurations")
    max_rounds: int = Field(default=5, ge=1, le=20, description="Maximum collaboration rounds")
    llm_provider: str = Field(
        default="ollama", description="LLM provider (ollama, openai, anthropic)"
    )
    llm_model: str = Field(default="llama3.2", description="LLM model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    stream: bool = Field(default=False, description="Stream responses")
    enable_tracing: bool = Field(default=True, description="Enable observability tracing")


class CollaborationResponse(BaseModel):
    """Response from a collaboration."""

    session_id: str = Field(..., description="Unique session identifier")
    result: str = Field(..., description="Collaboration result")
    rounds: int = Field(..., description="Number of rounds executed")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage statistics")
    cost_estimate: Dict[str, float] = Field(default_factory=dict, description="Cost estimate")
    duration_ms: float = Field(..., description="Total duration in milliseconds")


class SessionStatus(BaseModel):
    """Status of a collaboration session."""

    session_id: str
    status: str  # running, completed, failed
    progress: Optional[str] = None
    result: Optional[str] = None


# Helper Functions
def create_llm_provider(provider_type: str, model: str, temperature: float):
    """Create an LLM provider based on configuration."""
    if provider_type == "ollama":
        return OllamaProvider(model=model, temperature=temperature)
    elif provider_type in ["openai", "anthropic", "gemini"]:
        return LiteLLMProvider(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_type}")


async def run_collaboration(
    session_id: str, request: CollaborationRequest, tracer: Optional[Tracer] = None
) -> CollaborationResponse:
    """Run a multi-agent collaboration.

    Args:
        session_id: Unique session identifier
        request: Collaboration request
        tracer: Optional tracer for observability

    Returns:
        Collaboration response
    """
    import time

    start_time = time.time()

    try:
        # Update session status
        sessions[session_id]["status"] = "running"

        # Create LLM provider
        llm_provider = create_llm_provider(
            request.llm_provider, request.llm_model, request.temperature
        )

        # Create AgentMind instance
        mind = AgentMind(llm_provider=llm_provider)

        # Create and add agents
        for agent_config in request.agents:
            agent = Agent(name=agent_config.name, role=agent_config.role, llm_provider=llm_provider)
            mind.add_agent(agent)

        # Start tracing if enabled
        if tracer:
            tracer.start()

        # Run collaboration
        result = await mind.collaborate(task=request.task, max_rounds=request.max_rounds)

        # End tracing
        if tracer:
            tracer.end()

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Get token usage and cost from tracer
        token_usage = {}
        cost_estimate = {}
        if tracer:
            summary = tracer.get_summary()
            token_usage = summary.get("token_usage", {})
            cost_estimate = summary.get("cost_estimate", {})

        # Create response
        response = CollaborationResponse(
            session_id=session_id,
            result=result,
            rounds=len(mind.conversation_history) // len(request.agents),
            token_usage=token_usage,
            cost_estimate=cost_estimate,
            duration_ms=duration_ms,
        )

        # Update session
        sessions[session_id]["status"] = "completed"
        sessions[session_id]["result"] = response.model_dump()

        return response

    except Exception as e:
        logger.error(f"Collaboration failed: {e}", exc_info=True)
        sessions[session_id]["status"] = "failed"
        sessions[session_id]["error"] = str(e)
        raise


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AgentMind API",
        "version": "0.3.0",
        "description": "Multi-agent collaboration framework",
        "endpoints": {
            "POST /collaborate": "Start a new collaboration",
            "GET /session/{session_id}": "Get session status",
            "GET /health": "Health check",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len([s for s in sessions.values() if s["status"] == "running"]),
    }


@app.post("/collaborate", response_model=CollaborationResponse)
async def collaborate(request: CollaborationRequest, background_tasks: BackgroundTasks):
    """Start a multi-agent collaboration.

    Args:
        request: Collaboration request
        background_tasks: FastAPI background tasks

    Returns:
        Collaboration response

    Raises:
        HTTPException: If collaboration fails
    """
    # Generate session ID
    session_id = str(uuid.uuid4())

    # Initialize session
    sessions[session_id] = {
        "status": "initializing",
        "request": request.model_dump(),
        "created_at": asyncio.get_event_loop().time(),
    }

    # Create tracer if enabled
    tracer = None
    if request.enable_tracing:
        tracer = Tracer(
            session_id=session_id, metadata={"task": request.task, "agents": len(request.agents)}
        )

    try:
        # Run collaboration
        response = await run_collaboration(session_id, request, tracer)

        # Save trace in background if enabled
        if tracer and request.enable_tracing:
            background_tasks.add_task(tracer.save_jsonl, f"traces/{session_id}.jsonl")

        return response

    except Exception as e:
        logger.error(f"Collaboration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collaborate/stream")
async def collaborate_stream(request: CollaborationRequest):
    """Start a streaming multi-agent collaboration.

    Args:
        request: Collaboration request

    Returns:
        Streaming response with collaboration events
    """
    session_id = str(uuid.uuid4())

    async def event_generator():
        """Generate server-sent events for collaboration progress."""
        try:
            # Send session start event
            yield f"data: {{'event': 'session_start', 'session_id': '{session_id}'}}\n\n"

            # Create LLM provider
            llm_provider = create_llm_provider(
                request.llm_provider, request.llm_model, request.temperature
            )

            # Create AgentMind instance
            mind = AgentMind(llm_provider=llm_provider)

            # Create and add agents
            for agent_config in request.agents:
                agent = Agent(
                    name=agent_config.name, role=agent_config.role, llm_provider=llm_provider
                )
                mind.add_agent(agent)
                yield f"data: {{'event': 'agent_added', 'agent': '{agent_config.name}'}}\n\n"

            # Run collaboration with streaming
            # Note: This is a simplified version - full streaming would require
            # modifications to the AgentMind.collaborate method
            result = await mind.collaborate(task=request.task, max_rounds=request.max_rounds)

            # Send completion event
            yield f"data: {{'event': 'completed', 'result': '{result}'}}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {{'event': 'error', 'message': '{str(e)}'}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/session/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Get the status of a collaboration session.

    Args:
        session_id: Session identifier

    Returns:
        Session status

    Raises:
        HTTPException: If session not found
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    return SessionStatus(
        session_id=session_id, status=session["status"], result=session.get("result")
    )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a collaboration session.

    Args:
        session_id: Session identifier

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If session not found
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]

    return {"message": "Session deleted", "session_id": session_id}


@app.get("/sessions")
async def list_sessions():
    """List all collaboration sessions.

    Returns:
        List of session summaries
    """
    return {
        "total": len(sessions),
        "sessions": [
            {
                "session_id": sid,
                "status": session["status"],
                "created_at": session.get("created_at"),
            }
            for sid, session in sessions.items()
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
