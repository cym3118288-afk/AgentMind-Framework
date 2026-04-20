"""Enhanced chat server with modern UI and multi-session support.

Features:
- React-based modern UI
- Multi-session management
- Chat history with export (Markdown/PDF)
- Real-time streaming
- Session persistence
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import asyncio
from datetime import datetime
import sys
import os
import json
import uuid
from typing import Dict, List
import redis

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from agentmind.core.agent import Agent, Message
from agentmind.core.mind import AgentMind

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SESSION_SECRET", "agentmind-chat-secret")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Redis for session storage
try:
    redis_client = redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/1"), decode_responses=True
    )
    redis_client.ping()
    print("[✓] Redis connected")
except:
    redis_client = None
    print("[!] Redis not available, using in-memory storage")

# In-memory storage fallback
sessions: Dict[str, Dict] = {}
agents_initialized = False
mind = AgentMind()


def initialize_agents():
    """Initialize agents with different roles and personalities."""
    global agents_initialized
    if agents_initialized:
        return

    agent_configs = [
        ("Alice", "analyst", "🔍", "Data analysis and insights expert"),
        ("Bob", "creative", "🎨", "Creative thinking and brainstorming"),
        ("Charlie", "coordinator", "📋", "Project coordination and planning"),
        ("Diana", "technical", "💻", "Technical implementation specialist"),
        ("Eve", "researcher", "📚", "Research and information gathering"),
        ("Frank", "strategist", "♟️", "Strategic planning and decision making"),
        ("Grace", "designer", "✨", "UX/UI design and user experience"),
        ("Henry", "developer", "⚙️", "Software development and coding"),
        ("Iris", "marketer", "📢", "Marketing and communication"),
        ("Jack", "philosopher", "🤔", "Critical thinking and ethics"),
        ("Kate", "scientist", "🔬", "Scientific analysis and methodology"),
        ("Leo", "entrepreneur", "💡", "Business innovation and growth"),
    ]

    for name, role, emoji, description in agent_configs:
        agent = Agent(name, role)
        agent.emoji = emoji
        agent.description = description
        mind.add_agent(agent)

    agents_initialized = True
    print(f"[✓] Initialized {len(mind.agents)} agents")


def get_session(session_id: str) -> Dict:
    """Get session data from Redis or memory."""
    if redis_client:
        try:
            data = redis_client.get(f"chat_session:{session_id}")
            return json.loads(data) if data else None
        except:
            pass
    return sessions.get(session_id)


def save_session(session_id: str, data: Dict):
    """Save session data to Redis or memory."""
    if redis_client:
        try:
            redis_client.setex(f"chat_session:{session_id}", 86400, json.dumps(data))  # 24 hours
            return
        except:
            pass
    sessions[session_id] = data


def export_to_markdown(session_id: str) -> str:
    """Export chat history to Markdown."""
    session = get_session(session_id)
    if not session:
        return "# Session not found"

    md = f"# AgentMind Chat Session\n\n"
    md += f"**Session ID:** {session_id}\n"
    md += f"**Created:** {session.get('created_at', 'Unknown')}\n"
    md += f"**Messages:** {len(session.get('messages', []))}\n\n"
    md += "---\n\n"

    for msg in session.get("messages", []):
        sender = msg.get("sender", "Unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        msg_type = msg.get("type", "user")

        if msg_type == "user":
            md += f"### 👤 {sender} ({timestamp})\n\n"
        else:
            emoji = msg.get("emoji", "🤖")
            role = msg.get("role", "assistant")
            md += f"### {emoji} {sender} - *{role}* ({timestamp})\n\n"

        md += f"{content}\n\n"
        md += "---\n\n"

    return md


@app.route("/")
def index():
    """Serve the main chat interface."""
    return render_template("chat_enhanced.html")


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "agents": len(mind.agents),
            "redis_connected": redis_client is not None,
        }
    )


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    """List all chat sessions."""
    if redis_client:
        try:
            keys = redis_client.keys("chat_session:*")
            session_list = []
            for key in keys:
                session_id = key.split(":")[-1]
                data = get_session(session_id)
                if data:
                    session_list.append(
                        {
                            "session_id": session_id,
                            "created_at": data.get("created_at"),
                            "message_count": len(data.get("messages", [])),
                        }
                    )
            return jsonify({"sessions": session_list})
        except:
            pass

    return jsonify(
        {
            "sessions": [
                {
                    "session_id": sid,
                    "created_at": data.get("created_at"),
                    "message_count": len(data.get("messages", [])),
                }
                for sid, data in sessions.items()
            ]
        }
    )


@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session_data(session_id: str):
    """Get session data."""
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session)


@app.route("/api/sessions/<session_id>/export", methods=["GET"])
def export_session(session_id: str):
    """Export session to Markdown."""
    format_type = request.args.get("format", "markdown")

    if format_type == "markdown":
        md_content = export_to_markdown(session_id)
        filename = f"agentmind_session_{session_id[:8]}.md"

        # Save to temp file
        temp_path = f"/tmp/{filename}"
        with open(temp_path, "w") as f:
            f.write(md_content)

        return send_file(
            temp_path, as_attachment=True, download_name=filename, mimetype="text/markdown"
        )

    elif format_type == "json":
        session = get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        filename = f"agentmind_session_{session_id[:8]}.json"
        temp_path = f"/tmp/{filename}"

        with open(temp_path, "w") as f:
            json.dump(session, f, indent=2)

        return send_file(
            temp_path, as_attachment=True, download_name=filename, mimetype="application/json"
        )

    return jsonify({"error": "Unsupported format"}), 400


@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    initialize_agents()

    # Generate session ID
    session_id = str(uuid.uuid4())

    # Create new session
    session_data = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "messages": [],
    }
    save_session(session_id, session_data)

    # Send agent list to the newly connected client
    agent_list = [
        {
            "name": agent.name,
            "role": agent.role,
            "emoji": getattr(agent, "emoji", "🤖"),
            "description": getattr(agent, "description", ""),
            "is_active": agent.is_active,
        }
        for agent in mind.agents
    ]

    emit("session_created", {"session_id": session_id, "agents": agent_list})

    emit(
        "system_message",
        {
            "content": f"Welcome! {len(mind.agents)} agents are ready to collaborate.",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        },
    )


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    print("[!] Client disconnected")


@socketio.on("join_session")
def handle_join_session(data):
    """Join an existing session."""
    session_id = data.get("session_id")
    join_room(session_id)

    session = get_session(session_id)
    if session:
        emit("session_history", {"messages": session.get("messages", [])})


@socketio.on("user_message")
def handle_user_message(data):
    """Handle user message."""
    content = data.get("content", "")
    username = data.get("username", "User")
    session_id = data.get("session_id")

    if not content.strip():
        return

    # Create message object
    message_data = {
        "sender": username,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "type": "user",
        "emoji": "👤",
    }

    # Save to session
    session = get_session(session_id)
    if session:
        session["messages"].append(message_data)
        save_session(session_id, session)

    # Broadcast user message
    emit("new_message", message_data, room=session_id, broadcast=True)

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

                agent_message = {
                    "sender": response.sender,
                    "content": response.content,
                    "timestamp": response.timestamp.strftime("%H:%M:%S"),
                    "type": "agent",
                    "role": agent.role if agent else "assistant",
                    "emoji": getattr(agent, "emoji", "🤖") if agent else "🤖",
                }

                # Save to session
                session = get_session(session_id)
                if session:
                    session["messages"].append(agent_message)
                    save_session(session_id, session)

                socketio.emit("new_message", agent_message, room=session_id)

        finally:
            loop.close()

    # Run in background thread
    socketio.start_background_task(process_agents)


@socketio.on("toggle_agent")
def handle_toggle_agent(data):
    """Toggle agent active status."""
    agent_name = data.get("agent_name")
    session_id = data.get("session_id")

    agent = next((a for a in mind.agents if a.name == agent_name), None)

    if agent:
        agent.is_active = not agent.is_active
        emit(
            "agent_toggled",
            {"agent_name": agent_name, "is_active": agent.is_active},
            room=session_id,
            broadcast=True,
        )


@socketio.on("clear_session")
def handle_clear_session(data):
    """Clear session history."""
    session_id = data.get("session_id")

    session = get_session(session_id)
    if session:
        session["messages"] = []
        save_session(session_id, session)

        emit("session_cleared", {}, room=session_id, broadcast=True)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AgentMind Enhanced Chat Server Starting...")
    print("=" * 60)
    print("📡 Server will be available at: http://localhost:5000")
    print("💬 Multi-session chat interface with export support!")
    print("=" * 60)
    socketio.run(app, debug=False, host="0.0.0.0", port=5000)
