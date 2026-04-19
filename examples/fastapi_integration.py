"""FastAPI Integration Example

Demonstrates how to integrate AgentMind into a FastAPI application.
This example shows a practical API for content generation with multiple agents.

Use case: Content creation API with research, writing, and editing agents.
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agentmind import Agent, AgentMind
from agentmind.core.types import CollaborationStrategy
from agentmind.llm import OllamaProvider


# Request/Response models
class ContentRequest(BaseModel):
    """Request model for content generation."""

    topic: str
    style: str = "professional"
    max_rounds: int = 3
    model: str = "llama3.2"


class ContentResponse(BaseModel):
    """Response model for generated content."""

    content: str
    rounds: int
    participants: list[str]
    metadata: dict


# Initialize FastAPI app
app = FastAPI(
    title="AgentMind Content API", description="Multi-agent content generation API", version="1.0.0"
)


# Agent cache to avoid recreating on each request
_agent_cache = {}


def get_content_team(model: str = "llama3.2") -> AgentMind:
    """Get or create a content generation team.

    Args:
        model: Ollama model to use

    Returns:
        Configured AgentMind instance
    """
    cache_key = f"content_team_{model}"

    if cache_key in _agent_cache:
        return _agent_cache[cache_key]

    # Create LLM provider
    llm = OllamaProvider(model=model)

    # Create team with round-robin strategy
    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=llm)

    # Researcher agent
    researcher = Agent(name="Researcher", role="analyst", llm_provider=llm)
    researcher.config.system_prompt = """You are a research specialist.
Find key facts, statistics, and insights about topics.
Provide accurate, well-sourced information."""

    # Writer agent
    writer = Agent(name="Writer", role="creative", llm_provider=llm)
    writer.config.system_prompt = """You are a professional writer.
Create engaging, well-structured content.
Adapt your style based on requirements."""

    # Editor agent
    editor = Agent(name="Editor", role="critic", llm_provider=llm)
    editor.config.system_prompt = """You are an editor.
Review content for clarity, accuracy, and style.
Provide constructive improvements."""

    mind.add_agent(researcher)
    mind.add_agent(writer)
    mind.add_agent(editor)

    _agent_cache[cache_key] = mind
    return mind


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "AgentMind Content API",
        "version": "1.0.0",
        "endpoints": {"generate": "/generate", "health": "/health"},
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agents": "ready"}


@app.post("/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    """Generate content using multi-agent collaboration.

    Args:
        request: Content generation request

    Returns:
        Generated content with metadata

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Get agent team
        mind = get_content_team(request.model)

        # Create task prompt
        task = f"""Create content about: {request.topic}
Style: {request.style}

Requirements:
1. Research the topic thoroughly
2. Write engaging, accurate content
3. Edit for clarity and quality"""

        # Run collaboration
        result = await mind.collaborate(task=task, max_rounds=request.max_rounds)

        # Return response
        return ContentResponse(
            content=result.final_output,
            rounds=result.rounds,
            participants=result.participants,
            metadata={"topic": request.topic, "style": request.style, "model": request.model},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@app.post("/analyze")
async def analyze_text(text: str, model: str = "llama3.2"):
    """Analyze text using multiple agent perspectives.

    Args:
        text: Text to analyze
        model: Ollama model to use

    Returns:
        Analysis results
    """
    try:
        llm = OllamaProvider(model=model)
        mind = AgentMind(strategy=CollaborationStrategy.BROADCAST, llm_provider=llm)

        # Create analysis agents
        sentiment = Agent(name="Sentiment", role="analyst", llm_provider=llm)
        sentiment.config.system_prompt = "Analyze sentiment and emotional tone."

        structure = Agent(name="Structure", role="analyst", llm_provider=llm)
        structure.config.system_prompt = "Analyze structure and organization."

        quality = Agent(name="Quality", role="critic", llm_provider=llm)
        quality.config.system_prompt = "Evaluate quality and clarity."

        mind.add_agent(sentiment)
        mind.add_agent(structure)
        mind.add_agent(quality)

        result = await mind.collaborate(task=f"Analyze this text:\n\n{text}", max_rounds=1)

        return {"analysis": result.final_output, "perspectives": result.participants}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("Starting AgentMind Content API...")
    print("API docs available at: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)
