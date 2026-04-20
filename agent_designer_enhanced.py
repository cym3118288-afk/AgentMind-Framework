"""
Agent Designer Enhanced - Wave 2 Implementation

Features:
- Drag-and-drop workflow builder with visual connections
- Visual plugin configuration interface
- Real-time agent testing panel with WebSocket
- Template gallery with previews and categories
- Export/import agent definitions (JSON/YAML)
- Workflow validation and error checking
"""

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Request,
    UploadFile,
    File,
    HTTPException,
)
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Set
import os
import sys
import uuid
from pathlib import Path
import yaml

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from agentmind.core.agent import Agent
    from agentmind.core.mind import AgentMind
except ImportError:
    Agent = None
    AgentMind = None

app = FastAPI(title="AgentMind Agent Designer Enhanced", version="0.4.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage directories
CONFIGS_DIR = Path("./agent_configs")
TEMPLATES_DIR = Path("./agent_templates")
CONFIGS_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# WebSocket connections for real-time testing
active_connections: List[WebSocket] = []

# Agent templates with categories
AGENT_TEMPLATES = {
    "development": [
        {
            "id": "software_engineer",
            "name": "Software Engineer",
            "role": "engineer",
            "description": "Designs and implements software solutions with best practices",
            "icon": "💻",
            "system_prompt": "You are an expert software engineer. Write clean, efficient, and well-documented code.",
            "plugins": ["code_analyzer", "git_integration"],
            "capabilities": ["coding", "debugging", "code_review"],
        },
        {
            "id": "qa_engineer",
            "name": "QA Engineer",
            "role": "qa",
            "description": "Ensures quality through comprehensive testing",
            "icon": "🧪",
            "system_prompt": "You are a QA engineer focused on quality assurance and testing.",
            "plugins": ["test_runner", "bug_tracker"],
            "capabilities": ["testing", "quality_assurance", "bug_detection"],
        },
        {
            "id": "devops_engineer",
            "name": "DevOps Engineer",
            "role": "devops",
            "description": "Manages deployment, infrastructure, and CI/CD",
            "icon": "🚀",
            "system_prompt": "You are a DevOps engineer specializing in automation and infrastructure.",
            "plugins": ["docker", "kubernetes", "ci_cd"],
            "capabilities": ["deployment", "monitoring", "automation"],
        },
    ],
    "research": [
        {
            "id": "researcher",
            "name": "Researcher",
            "role": "researcher",
            "description": "Conducts thorough research and gathers information",
            "icon": "🔍",
            "system_prompt": "You are a research specialist. Gather comprehensive information and cite sources.",
            "plugins": ["web_search", "document_analyzer"],
            "capabilities": ["research", "analysis", "fact_checking"],
        },
        {
            "id": "analyst",
            "name": "Data Analyst",
            "role": "analyst",
            "description": "Analyzes data and provides actionable insights",
            "icon": "📊",
            "system_prompt": "You are a data analyst. Analyze data and provide clear insights.",
            "plugins": ["data_processor", "visualization"],
            "capabilities": ["data_analysis", "statistics", "reporting"],
        },
    ],
    "creative": [
        {
            "id": "writer",
            "name": "Content Writer",
            "role": "writer",
            "description": "Creates engaging and well-structured content",
            "icon": "✍️",
            "system_prompt": "You are a professional content writer. Create engaging, clear content.",
            "plugins": ["grammar_checker", "seo_optimizer"],
            "capabilities": ["writing", "editing", "storytelling"],
        },
        {
            "id": "creative_director",
            "name": "Creative Director",
            "role": "creative",
            "description": "Generates innovative concepts and creative ideas",
            "icon": "🎨",
            "system_prompt": "You are a creative director. Generate innovative and compelling ideas.",
            "plugins": ["brainstorming", "design_tools"],
            "capabilities": ["ideation", "design", "branding"],
        },
    ],
    "business": [
        {
            "id": "marketing_manager",
            "name": "Marketing Manager",
            "role": "marketing",
            "description": "Develops and executes marketing strategies",
            "icon": "📢",
            "system_prompt": "You are a marketing manager. Create effective marketing strategies.",
            "plugins": ["analytics", "campaign_manager"],
            "capabilities": ["marketing", "strategy", "campaigns"],
        },
        {
            "id": "support_specialist",
            "name": "Support Specialist",
            "role": "support",
            "description": "Provides excellent customer support and assistance",
            "icon": "🤝",
            "system_prompt": "You are a customer support specialist. Provide helpful, empathetic support.",
            "plugins": ["ticket_system", "knowledge_base"],
            "capabilities": ["support", "communication", "problem_solving"],
        },
    ],
    "security": [
        {
            "id": "security_expert",
            "name": "Security Expert",
            "role": "security",
            "description": "Reviews security and identifies vulnerabilities",
            "icon": "🔒",
            "system_prompt": "You are a security expert. Identify vulnerabilities and recommend fixes.",
            "plugins": ["security_scanner", "vulnerability_db"],
            "capabilities": ["security_audit", "penetration_testing", "compliance"],
        }
    ],
}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to designer."""
    return HTMLResponse(content='<meta http-equiv="refresh" content="0; url=/designer">')


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.4.0",
        "features": ["drag_drop", "real_time_testing", "templates", "export_import"],
    }


@app.get("/api/templates")
async def get_templates():
    """Get all agent templates organized by category."""
    return {"templates": AGENT_TEMPLATES}


@app.get("/api/templates/{category}")
async def get_templates_by_category(category: str):
    """Get templates for a specific category."""
    if category not in AGENT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"category": category, "templates": AGENT_TEMPLATES[category]}


@app.post("/api/configs")
async def save_config(request: Request):
    """Save agent configuration."""
    try:
        config = await request.json()
        config_id = config.get("id", str(uuid.uuid4()))
        config["id"] = config_id
        config["updated_at"] = datetime.now().isoformat()

        # Validate configuration
        validation_result = validate_config(config)
        if not validation_result["valid"]:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid configuration", "details": validation_result["errors"]},
            )

        # Save to file
        config_path = CONFIGS_DIR / f"{config_id}.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return {"success": True, "config_id": config_id, "path": str(config_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/configs")
async def list_configs():
    """List all saved configurations."""
    configs = []
    for config_file in CONFIGS_DIR.glob("*.json"):
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                configs.append(
                    {
                        "id": config.get("id"),
                        "name": config.get("team_name", "Unnamed"),
                        "agent_count": len(config.get("agents", [])),
                        "updated_at": config.get("updated_at"),
                    }
                )
        except:
            continue
    return {"configs": configs}


@app.get("/api/configs/{config_id}")
async def get_config(config_id: str):
    """Get a specific configuration."""
    config_path = CONFIGS_DIR / f"{config_id}.json"
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Configuration not found")

    with open(config_path, "r") as f:
        config = json.load(f)
    return config


@app.delete("/api/configs/{config_id}")
async def delete_config(config_id: str):
    """Delete a configuration."""
    config_path = CONFIGS_DIR / f"{config_id}.json"
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Configuration not found")

    config_path.unlink()
    return {"success": True, "message": "Configuration deleted"}


@app.post("/api/configs/import")
async def import_config(file: UploadFile = File(...)):
    """Import configuration from file (JSON or YAML)."""
    try:
        content = await file.read()

        if file.filename.endswith(".json"):
            config = json.loads(content)
        elif file.filename.endswith((".yaml", ".yml")):
            config = yaml.safe_load(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # Validate and save
        config_id = str(uuid.uuid4())
        config["id"] = config_id
        config["updated_at"] = datetime.now().isoformat()

        validation_result = validate_config(config)
        if not validation_result["valid"]:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid configuration", "details": validation_result["errors"]},
            )

        config_path = CONFIGS_DIR / f"{config_id}.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return {"success": True, "config_id": config_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/configs/{config_id}/export")
async def export_config(config_id: str, format: str = "json"):
    """Export configuration to file."""
    config_path = CONFIGS_DIR / f"{config_id}.json"
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Configuration not found")

    with open(config_path, "r") as f:
        config = json.load(f)

    if format == "json":
        export_path = CONFIGS_DIR / f"{config_id}_export.json"
        with open(export_path, "w") as f:
            json.dump(config, f, indent=2)
        return FileResponse(export_path, filename=f"agentmind_{config_id}.json")

    elif format == "yaml":
        export_path = CONFIGS_DIR / f"{config_id}_export.yaml"
        with open(export_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        return FileResponse(export_path, filename=f"agentmind_{config_id}.yaml")

    elif format == "python":
        code = generate_python_code(config)
        export_path = CONFIGS_DIR / f"{config_id}_export.py"
        with open(export_path, "w") as f:
            f.write(code)
        return FileResponse(export_path, filename=f"agentmind_{config_id}.py")

    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")


@app.post("/api/validate")
async def validate_configuration(request: Request):
    """Validate agent configuration."""
    config = await request.json()
    result = validate_config(config)
    return result


@app.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent testing."""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "test_agent":
                # Test individual agent
                agent_config = data.get("agent")
                test_input = data.get("input", "Hello!")

                await websocket.send_json({"type": "test_start", "agent": agent_config.get("name")})

                # Simulate agent response
                await asyncio.sleep(1)

                await websocket.send_json(
                    {
                        "type": "test_response",
                        "agent": agent_config.get("name"),
                        "response": f"Test response from {agent_config.get('name')}: {test_input}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            elif action == "test_workflow":
                # Test entire workflow
                config = data.get("config")
                test_input = data.get("input", "Test workflow")

                await websocket.send_json(
                    {"type": "workflow_start", "agents": len(config.get("agents", []))}
                )

                # Simulate workflow execution
                for agent in config.get("agents", []):
                    await asyncio.sleep(0.5)
                    await websocket.send_json(
                        {
                            "type": "agent_processing",
                            "agent": agent.get("name"),
                            "status": "processing",
                        }
                    )

                await websocket.send_json(
                    {"type": "workflow_complete", "result": "Workflow test completed successfully"}
                )

    except WebSocketDisconnect:
        active_connections.remove(websocket)


def validate_config(config: Dict) -> Dict:
    """Validate agent configuration."""
    errors = []

    # Check required fields
    if not config.get("team_name"):
        errors.append("Team name is required")

    if not config.get("agents"):
        errors.append("At least one agent is required")

    # Validate agents
    agents = config.get("agents", [])
    agent_names = set()

    for i, agent in enumerate(agents):
        if not agent.get("name"):
            errors.append(f"Agent {i+1}: Name is required")
        else:
            if agent["name"] in agent_names:
                errors.append(f"Agent {i+1}: Duplicate name '{agent['name']}'")
            agent_names.add(agent["name"])

        if not agent.get("role"):
            errors.append(f"Agent {i+1}: Role is required")

    # Validate workflow connections
    connections = config.get("connections", [])
    for conn in connections:
        if conn.get("from") not in agent_names:
            errors.append(f"Connection: Invalid source agent '{conn.get('from')}'")
        if conn.get("to") not in agent_names:
            errors.append(f"Connection: Invalid target agent '{conn.get('to')}'")

    return {"valid": len(errors) == 0, "errors": errors}


def generate_python_code(config: Dict) -> str:
    """Generate Python code from configuration."""
    team_name = config.get("team_name", "My Team")
    provider = config.get("llm_provider", "ollama")
    model = config.get("model", "llama3.2")
    max_rounds = config.get("max_rounds", 5)
    agents = config.get("agents", [])

    code = f'''"""
{team_name} - Generated by AgentMind Designer
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

from agentmind.core.agent import Agent
from agentmind.core.mind import AgentMind
from agentmind.llm import {"OllamaProvider" if provider == "ollama" else "LiteLLMProvider"}
import asyncio


async def main():
    """Initialize and run the agent team."""
    # Initialize LLM provider
    llm = {"OllamaProvider" if provider == "ollama" else "LiteLLMProvider"}(model="{model}")
    mind = AgentMind(llm_provider=llm)

    # Create agents
'''

    for agent in agents:
        agent_var = agent["name"].lower().replace(" ", "_").replace("-", "_")
        code += f"""    {agent_var} = Agent(
        name="{agent['name']}",
        role="{agent['role']}",
        system_prompt="{agent.get('system_prompt', '')}"
    )
    mind.add_agent({agent_var})

"""

    code += f"""    # Run collaboration
    result = await mind.collaborate(
        "Your task here",
        max_rounds={max_rounds}
    )

    print("\\nResult:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
"""

    return code


@app.get("/designer", response_class=HTMLResponse)
async def agent_designer():
    """Enhanced visual agent designer interface."""
    html_file = Path(__file__).parent / "templates" / "agent_designer_enhanced.html"

    if html_file.exists():
        with open(html_file, "r") as f:
            return HTMLResponse(content=f.read())

    # Fallback inline HTML
    return HTMLResponse(
        content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agent Designer Enhanced - AgentMind</title>
        <link rel="stylesheet" href="/static/css/designer_enhanced.css">
    </head>
    <body>
        <div id="app">
            <h1>Agent Designer Enhanced</h1>
            <p>Loading designer interface...</p>
        </div>
        <script src="/static/js/designer_enhanced.js"></script>
    </body>
    </html>
    """
    )


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🎨 AgentMind Agent Designer Enhanced")
    print("=" * 60)
    print("📍 Designer: http://localhost:8002/designer")
    print("📡 API Docs: http://localhost:8002/docs")
    print("🔧 Features: Drag-drop, Testing, Templates, Export/Import")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8002)
