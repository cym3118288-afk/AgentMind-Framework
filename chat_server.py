from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agentmind.core.agent import Agent, Message
from agentmind.core.mind import AgentMind

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agentmind-chat-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global AgentMind instance
mind = AgentMind()
agents_initialized = False

def initialize_agents():
    """Initialize 10+ agents with different roles and personalities"""
    global agents_initialized
    if agents_initialized:
        return

    agent_configs = [
        ("Alice", "analyst", "🔍"),
        ("Bob", "creative", "🎨"),
        ("Charlie", "coordinator", "📋"),
        ("Diana", "technical", "💻"),
        ("Eve", "researcher", "📚"),
        ("Frank", "strategist", "♟️"),
        ("Grace", "designer", "✨"),
        ("Henry", "developer", "⚙️"),
        ("Iris", "marketer", "📢"),
        ("Jack", "philosopher", "🤔"),
        ("Kate", "scientist", "🔬"),
        ("Leo", "entrepreneur", "💡"),
    ]

    for name, role, emoji in agent_configs:
        agent = Agent(name, role)
        agent.emoji = emoji
        mind.add_agent(agent)

    agents_initialized = True
    print(f"[✓] Initialized {len(mind.agents)} agents")

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('connect')
def handle_connect():
    initialize_agents()

    # Send agent list to the newly connected client
    agent_list = [
        {
            'name': agent.name,
            'role': agent.role,
            'emoji': getattr(agent, 'emoji', '🤖'),
            'is_active': agent.is_active
        }
        for agent in mind.agents
    ]

    emit('agent_list', {'agents': agent_list})
    emit('system_message', {
        'content': f'Welcome! {len(mind.agents)} agents are ready to chat.',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

@socketio.on('disconnect')
def handle_disconnect():
    print('[!] Client disconnected')

@socketio.on('user_message')
def handle_user_message(data):
    content = data.get('content', '')
    username = data.get('username', 'User')

    if not content.strip():
        return

    # Broadcast user message to all clients
    emit('new_message', {
        'sender': username,
        'content': content,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'type': 'user',
        'emoji': '👤'
    }, broadcast=True)

    # Create message for agents
    user_msg = Message(content=content, sender=username)

    # Process with agents asynchronously
    def process_agents():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            responses = loop.run_until_complete(
                mind.broadcast_message(user_msg, exclude_sender=False)
            )

            # Send agent responses
            for response in responses:
                agent = next((a for a in mind.agents if a.name == response.sender), None)
                socketio.emit('new_message', {
                    'sender': response.sender,
                    'content': response.content,
                    'timestamp': response.timestamp.strftime('%H:%M:%S'),
                    'type': 'agent',
                    'role': agent.role if agent else 'assistant',
                    'emoji': getattr(agent, 'emoji', '🤖') if agent else '🤖'
                })
        finally:
            loop.close()

    # Run in background thread
    socketio.start_background_task(process_agents)

@socketio.on('toggle_agent')
def handle_toggle_agent(data):
    agent_name = data.get('agent_name')
    agent = next((a for a in mind.agents if a.name == agent_name), None)

    if agent:
        agent.is_active = not agent.is_active
        emit('agent_toggled', {
            'agent_name': agent_name,
            'is_active': agent.is_active
        }, broadcast=True)

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AgentMind Chat Server Starting...")
    print("=" * 60)
    print("📡 Server will be available at: http://localhost:5000")
    print("💬 Multi-agent chat interface ready!")
    print("=" * 60)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
