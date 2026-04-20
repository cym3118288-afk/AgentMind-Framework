"""
Agent Designer - Visual drag-and-drop interface for designing multi-agent systems.

Enhanced version with better UX and more features.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import os

app = FastAPI(title="AgentMind Agent Designer", version="0.3.0")


@app.get("/designer", response_class=HTMLResponse)
async def agent_designer():
    """Visual agent designer interface."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agent Designer - AgentMind</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f7fa;
                height: 100vh;
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header h1 {
                font-size: 24px;
                margin-bottom: 5px;
            }
            .header p {
                opacity: 0.9;
                font-size: 14px;
            }
            .container {
                display: flex;
                height: calc(100vh - 80px);
            }
            .sidebar {
                width: 300px;
                background: white;
                border-right: 1px solid #e1e8ed;
                overflow-y: auto;
                padding: 20px;
            }
            .canvas {
                flex: 1;
                padding: 30px;
                overflow-y: auto;
            }
            .properties {
                width: 350px;
                background: white;
                border-left: 1px solid #e1e8ed;
                overflow-y: auto;
                padding: 20px;
            }
            .section-title {
                font-size: 14px;
                font-weight: 600;
                color: #667eea;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 15px;
            }
            .agent-template {
                background: white;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                cursor: move;
                transition: all 0.2s;
            }
            .agent-template:hover {
                border-color: #667eea;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
                transform: translateY(-2px);
            }
            .agent-template h3 {
                font-size: 16px;
                color: #333;
                margin-bottom: 5px;
            }
            .agent-template p {
                font-size: 13px;
                color: #666;
                line-height: 1.4;
            }
            .agent-card {
                background: white;
                border: 2px solid #667eea;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                cursor: pointer;
                transition: all 0.2s;
                position: relative;
            }
            .agent-card:hover {
                box-shadow: 0 8px 24px rgba(0,0,0,0.12);
                transform: translateY(-2px);
            }
            .agent-card.selected {
                border-color: #764ba2;
                box-shadow: 0 8px 24px rgba(118, 75, 162, 0.2);
            }
            .agent-card h3 {
                font-size: 18px;
                color: #667eea;
                margin-bottom: 8px;
            }
            .agent-card .role {
                font-size: 13px;
                color: #666;
                margin-bottom: 12px;
            }
            .agent-card .prompt {
                font-size: 13px;
                color: #333;
                line-height: 1.5;
                max-height: 60px;
                overflow: hidden;
            }
            .remove-btn {
                position: absolute;
                top: 10px;
                right: 10px;
                background: #ff4757;
                color: white;
                border: none;
                border-radius: 50%;
                width: 28px;
                height: 28px;
                cursor: pointer;
                font-size: 18px;
                line-height: 1;
                transition: all 0.2s;
            }
            .remove-btn:hover {
                background: #ee5a6f;
                transform: scale(1.1);
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                font-size: 13px;
                font-weight: 600;
                color: #333;
                margin-bottom: 8px;
            }
            .form-group input,
            .form-group textarea,
            .form-group select {
                width: 100%;
                padding: 10px;
                border: 1px solid #e1e8ed;
                border-radius: 6px;
                font-size: 14px;
                font-family: inherit;
                transition: border-color 0.2s;
            }
            .form-group input:focus,
            .form-group textarea:focus,
            .form-group select:focus {
                outline: none;
                border-color: #667eea;
            }
            .form-group textarea {
                resize: vertical;
                min-height: 100px;
            }
            .btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                width: 100%;
                margin-bottom: 10px;
            }
            .btn:hover {
                background: #764ba2;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }
            .btn-secondary {
                background: #48dbfb;
            }
            .btn-secondary:hover {
                background: #0abde3;
            }
            .btn-success {
                background: #1dd1a1;
            }
            .btn-success:hover {
                background: #10ac84;
            }
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #999;
            }
            .empty-state svg {
                width: 120px;
                height: 120px;
                margin-bottom: 20px;
                opacity: 0.3;
            }
            .empty-state h3 {
                font-size: 20px;
                margin-bottom: 10px;
            }
            .empty-state p {
                font-size: 14px;
            }
            .drop-zone {
                border: 2px dashed #e1e8ed;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
                color: #999;
                transition: all 0.2s;
            }
            .drop-zone.drag-over {
                border-color: #667eea;
                background: rgba(102, 126, 234, 0.05);
            }
            .code-output {
                background: #2d3748;
                color: #e2e8f0;
                padding: 20px;
                border-radius: 8px;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.6;
                overflow-x: auto;
                margin-top: 20px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-card .value {
                font-size: 32px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .stat-card .label {
                font-size: 12px;
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Agent Designer</h1>
            <p>Drag and drop to design your multi-agent system</p>
        </div>

        <div class="container">
            <!-- Sidebar with agent templates -->
            <div class="sidebar">
                <div class="section-title">Agent Templates</div>

                <div class="agent-template" draggable="true" data-role="researcher">
                    <h3>Researcher</h3>
                    <p>Conducts thorough research and gathers information</p>
                </div>

                <div class="agent-template" draggable="true" data-role="analyst">
                    <h3>Analyst</h3>
                    <p>Analyzes data and provides insights</p>
                </div>

                <div class="agent-template" draggable="true" data-role="writer">
                    <h3>Writer</h3>
                    <p>Creates engaging written content</p>
                </div>

                <div class="agent-template" draggable="true" data-role="engineer">
                    <h3>Software Engineer</h3>
                    <p>Designs and implements software solutions</p>
                </div>

                <div class="agent-template" draggable="true" data-role="security">
                    <h3>Security Expert</h3>
                    <p>Reviews security and identifies vulnerabilities</p>
                </div>

                <div class="agent-template" draggable="true" data-role="qa">
                    <h3>QA Engineer</h3>
                    <p>Ensures quality through testing</p>
                </div>

                <div class="agent-template" draggable="true" data-role="devops">
                    <h3>DevOps Engineer</h3>
                    <p>Manages deployment and infrastructure</p>
                </div>

                <div class="agent-template" draggable="true" data-role="marketing">
                    <h3>Marketing Manager</h3>
                    <p>Develops marketing strategies</p>
                </div>

                <div class="agent-template" draggable="true" data-role="creative">
                    <h3>Creative Director</h3>
                    <p>Generates creative concepts and ideas</p>
                </div>

                <div class="agent-template" draggable="true" data-role="support">
                    <h3>Support Specialist</h3>
                    <p>Provides customer support and assistance</p>
                </div>
            </div>

            <!-- Canvas for designing -->
            <div class="canvas" id="canvas">
                <div class="stats">
                    <div class="stat-card">
                        <div class="value" id="agentCount">0</div>
                        <div class="label">Agents</div>
                    </div>
                    <div class="stat-card">
                        <div class="value" id="roleCount">0</div>
                        <div class="label">Unique Roles</div>
                    </div>
                </div>

                <div class="drop-zone" id="dropZone">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <h3>Drag agents here to start</h3>
                    <p>Build your multi-agent team by dragging templates from the left</p>
                </div>

                <div id="agentList"></div>
            </div>

            <!-- Properties panel -->
            <div class="properties">
                <div class="section-title">Team Configuration</div>

                <div class="form-group">
                    <label>Team Name</label>
                    <input type="text" id="teamName" placeholder="My Agent Team" value="My Agent Team">
                </div>

                <div class="form-group">
                    <label>LLM Provider</label>
                    <select id="llmProvider">
                        <option value="ollama">Ollama (Local)</option>
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Model</label>
                    <input type="text" id="model" placeholder="llama3.2" value="llama3.2">
                </div>

                <div class="form-group">
                    <label>Max Rounds</label>
                    <input type="number" id="maxRounds" value="5" min="1" max="20">
                </div>

                <button class="btn btn-success" onclick="generateCode()">Generate Code</button>
                <button class="btn btn-secondary" onclick="exportConfig()">Export Config</button>
                <button class="btn" onclick="clearCanvas()">Clear All</button>

                <div id="codeOutput"></div>
            </div>
        </div>

        <script>
            let agents = [];
            let selectedAgent = null;
            let agentCounter = 0;

            // Drag and drop functionality
            document.querySelectorAll('.agent-template').forEach(template => {
                template.addEventListener('dragstart', (e) => {
                    e.dataTransfer.setData('role', template.dataset.role);
                    e.dataTransfer.setData('name', template.querySelector('h3').textContent);
                });
            });

            const dropZone = document.getElementById('dropZone');
            const canvas = document.getElementById('canvas');

            [dropZone, canvas].forEach(element => {
                element.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    dropZone.classList.add('drag-over');
                });

                element.addEventListener('dragleave', () => {
                    dropZone.classList.remove('drag-over');
                });

                element.addEventListener('drop', (e) => {
                    e.preventDefault();
                    dropZone.classList.remove('drag-over');

                    const role = e.dataTransfer.getData('role');
                    const name = e.dataTransfer.getData('name');

                    addAgent(name, role);
                });
            });

            function addAgent(name, role) {
                agentCounter++;
                const agent = {
                    id: agentCounter,
                    name: name,
                    role: role,
                    prompt: `You are a ${name} specialized in ${role}.`
                };

                agents.push(agent);
                renderAgents();
                updateStats();

                // Hide drop zone after first agent
                if (agents.length > 0) {
                    dropZone.style.display = 'none';
                }
            }

            function removeAgent(id) {
                agents = agents.filter(a => a.id !== id);
                renderAgents();
                updateStats();

                // Show drop zone if no agents
                if (agents.length === 0) {
                    dropZone.style.display = 'block';
                }
            }

            function renderAgents() {
                const agentList = document.getElementById('agentList');
                agentList.innerHTML = agents.map(agent => `
                    <div class="agent-card ${selectedAgent === agent.id ? 'selected' : ''}"
                         onclick="selectAgent(${agent.id})">
                        <button class="remove-btn" onclick="event.stopPropagation(); removeAgent(${agent.id})">×</button>
                        <h3>${agent.name}</h3>
                        <div class="role">Role: ${agent.role}</div>
                        <div class="prompt">${agent.prompt}</div>
                    </div>
                `).join('');
            }

            function selectAgent(id) {
                selectedAgent = id;
                renderAgents();
            }

            function updateStats() {
                document.getElementById('agentCount').textContent = agents.length;
                const uniqueRoles = new Set(agents.map(a => a.role)).size;
                document.getElementById('roleCount').textContent = uniqueRoles;
            }

            function generateCode() {
                const teamName = document.getElementById('teamName').value;
                const provider = document.getElementById('llmProvider').value;
                const model = document.getElementById('model').value;
                const maxRounds = document.getElementById('maxRounds').value;

                const code = `from agentmind import Agent, AgentMind
from agentmind.llm import ${provider === 'ollama' ? 'OllamaProvider' : 'LiteLLMProvider'}
import asyncio

async def main():
    # Initialize LLM provider
    llm = ${provider === 'ollama' ? `OllamaProvider(model="${model}")` : `LiteLLMProvider(model="${model}")`}
    mind = AgentMind(llm_provider=llm)

    # Create agents
${agents.map(agent => `    ${agent.name.toLowerCase().replace(/\s+/g, '_')} = Agent(
        name="${agent.name}",
        role="${agent.role}",
        system_prompt="${agent.prompt}"
    )
    mind.add_agent(${agent.name.toLowerCase().replace(/\s+/g, '_')})`).join('\n\n')}

    # Run collaboration
    result = await mind.collaborate(
        "Your task here",
        max_rounds=${maxRounds}
    )

    print(result)

if __name__ == "__main__":
    asyncio.run(main())`;

                document.getElementById('codeOutput').innerHTML = `
                    <div class="code-output">${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
                `;
            }

            function exportConfig() {
                const config = {
                    team_name: document.getElementById('teamName').value,
                    llm_provider: document.getElementById('llmProvider').value,
                    model: document.getElementById('model').value,
                    max_rounds: parseInt(document.getElementById('maxRounds').value),
                    agents: agents.map(a => ({
                        name: a.name,
                        role: a.role,
                        system_prompt: a.prompt
                    }))
                };

                const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'agentmind-config.json';
                a.click();
            }

            function clearCanvas() {
                if (confirm('Are you sure you want to clear all agents?')) {
                    agents = [];
                    renderAgents();
                    updateStats();
                    dropZone.style.display = 'block';
                    document.getElementById('codeOutput').innerHTML = '';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
