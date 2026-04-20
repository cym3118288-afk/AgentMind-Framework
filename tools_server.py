"""
AgentMind Tools Server
Serves web-based tools and dashboards for AgentMind development
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import uvicorn
import json
import asyncio
from datetime import datetime
from typing import List, Dict
import os

app = FastAPI(title="AgentMind Tools", version="0.3.0")

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
templates_path = os.path.join(os.path.dirname(__file__), "templates")

if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

templates = Jinja2Templates(directory=templates_path)

# WebSocket connections for real-time collaboration viewer
active_connections: List[WebSocket] = []


@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with links to all tools"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AgentMind Tools</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                width: 100%;
            }
            .header {
                text-align: center;
                color: white;
                margin-bottom: 50px;
            }
            .header h1 {
                font-size: 3em;
                margin-bottom: 10px;
            }
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
            }
            .tools-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
            }
            .tool-card {
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                transition: all 0.3s;
                cursor: pointer;
            }
            .tool-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            }
            .tool-card h2 {
                color: #667eea;
                margin-bottom: 15px;
                font-size: 1.8em;
            }
            .tool-card p {
                color: #666;
                line-height: 1.6;
                margin-bottom: 20px;
            }
            .tool-card .btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                text-decoration: none;
                display: inline-block;
                font-weight: 500;
                transition: all 0.3s;
            }
            .tool-card .btn:hover {
                background: #764ba2;
            }
            .footer {
                text-align: center;
                color: white;
                margin-top: 50px;
                opacity: 0.8;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>AgentMind Tools</h1>
                <p>Web-based tools for building and monitoring multi-agent systems</p>
            </div>

            <div class="tools-grid">
                <div class="tool-card" onclick="window.location.href='/tools/agent-designer'">
                    <h2>Agent Designer</h2>
                    <p>Visual drag-and-drop interface for designing multi-agent systems. Create agents, define roles, and generate production-ready code.</p>
                    <a href="/tools/agent-designer" class="btn">Open Designer</a>
                </div>

                <div class="tool-card" onclick="window.location.href='/tools/performance-dashboard'">
                    <h2>Performance Dashboard</h2>
                    <p>Real-time monitoring of agent performance, token usage, costs, and system metrics with interactive charts.</p>
                    <a href="/tools/performance-dashboard" class="btn">View Dashboard</a>
                </div>

                <div class="tool-card" onclick="window.location.href='/tools/config-builder'">
                    <h2>Configuration Builder</h2>
                    <p>Generate complete project configurations including Python code, YAML configs, and Docker Compose files.</p>
                    <a href="/tools/config-builder" class="btn">Build Config</a>
                </div>

                <div class="tool-card" onclick="window.location.href='/tools/collaboration-viewer'">
                    <h2>Collaboration Viewer</h2>
                    <p>Watch agent collaboration in real-time with WebSocket streaming. See messages, decisions, and interactions live.</p>
                    <a href="/tools/collaboration-viewer" class="btn">View Live</a>
                </div>
            </div>

            <div class="footer">
                <p>AgentMind v0.3.0 - Built with FastAPI</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/tools/agent-designer", response_class=HTMLResponse)
async def agent_designer(request: Request):
    """Agent designer tool"""
    return templates.TemplateResponse("tools/agent_designer.html", {"request": request})


@app.get("/tools/performance-dashboard", response_class=HTMLResponse)
async def performance_dashboard(request: Request):
    """Performance monitoring dashboard"""
    return templates.TemplateResponse("tools/performance_dashboard.html", {"request": request})


@app.get("/tools/config-builder", response_class=HTMLResponse)
async def config_builder(request: Request):
    """Configuration builder tool"""
    return templates.TemplateResponse("tools/config_builder.html", {"request": request})


@app.get("/tools/collaboration-viewer", response_class=HTMLResponse)
async def collaboration_viewer():
    """Real-time collaboration viewer"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Collaboration Viewer</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: #1a1a2e;
                color: #eee;
                padding: 20px;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px;
                border-radius: 12px;
                margin-bottom: 30px;
            }
            .header h1 { font-size: 2.5em; margin-bottom: 10px; }
            .status {
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: 500;
            }
            .status.connected { background: #4ecca3; color: #000; }
            .status.disconnected { background: #ff6b6b; color: #fff; }
            .messages {
                background: #16213e;
                border-radius: 12px;
                padding: 20px;
                min-height: 600px;
                max-height: 600px;
                overflow-y: auto;
            }
            .message {
                background: #0f1419;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 15px;
                border-left: 4px solid #667eea;
            }
            .message .agent { color: #667eea; font-weight: bold; margin-bottom: 8px; }
            .message .timestamp { color: #888; font-size: 0.85em; margin-bottom: 8px; }
            .message .content { color: #eee; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Collaboration Viewer</h1>
                <p>Real-time agent collaboration monitoring</p>
                <div style="margin-top: 15px;">
                    <span class="status disconnected" id="status">Disconnected</span>
                </div>
            </div>
            <div class="messages" id="messages">
                <p style="text-align: center; color: #888; margin-top: 50px;">
                    Waiting for agent activity...
                </p>
            </div>
        </div>
        <script>
            const ws = new WebSocket('ws://localhost:8001/ws/collaboration');
            const messagesDiv = document.getElementById('messages');
            const statusDiv = document.getElementById('status');

            ws.onopen = () => {
                statusDiv.textContent = 'Connected';
                statusDiv.className = 'status connected';
                messagesDiv.innerHTML = '';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                messageDiv.innerHTML = `
                    <div class="agent">${data.agent}</div>
                    <div class="timestamp">${data.timestamp}</div>
                    <div class="content">${data.content}</div>
                `;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            };

            ws.onclose = () => {
                statusDiv.textContent = 'Disconnected';
                statusDiv.className = 'status disconnected';
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.websocket("/ws/collaboration")
async def websocket_collaboration(websocket: WebSocket):
    """WebSocket endpoint for real-time collaboration updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # Send initial connection message
        await websocket.send_json(
            {
                "agent": "System",
                "timestamp": datetime.now().isoformat(),
                "content": "Connected to collaboration stream",
            }
        )

        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            # Broadcast to all connected clients
            for connection in active_connections:
                try:
                    await connection.send_text(data)
                except:
                    active_connections.remove(connection)

    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.post("/api/broadcast")
async def broadcast_message(message: Dict):
    """API endpoint to broadcast messages to all connected WebSocket clients"""
    message_data = {
        "agent": message.get("agent", "Unknown"),
        "timestamp": datetime.now().isoformat(),
        "content": message.get("content", ""),
    }

    for connection in active_connections:
        try:
            await connection.send_json(message_data)
        except:
            active_connections.remove(connection)

    return {"status": "broadcasted", "connections": len(active_connections)}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agentmind-tools",
        "version": "0.3.0",
        "active_connections": len(active_connections),
    }


if __name__ == "__main__":
    print("Starting AgentMind Tools Server...")
    print("Access tools at: http://localhost:8001")
    print("\nAvailable tools:")
    print("  - Agent Designer: http://localhost:8001/tools/agent-designer")
    print("  - Performance Dashboard: http://localhost:8001/tools/performance-dashboard")
    print("  - Config Builder: http://localhost:8001/tools/config-builder")
    print("  - Collaboration Viewer: http://localhost:8001/tools/collaboration-viewer")

    uvicorn.run(app, host="0.0.0.0", port=8001)
