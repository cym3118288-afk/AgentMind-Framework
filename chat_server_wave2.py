"""
Enhanced Chat Server - Wave 2 Implementation

Features:
- Multi-agent conversation view with threading
- Message threading and context management
- File upload support (documents, images, code)
- Code syntax highlighting with Prism.js
- Export conversation history (Markdown, JSON, PDF)
- Real-time typing indicators
- Message reactions and bookmarks
- Search and filter conversations
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import asyncio
from datetime import datetime
import sys
import os
import json
import uuid
from typing import Dict, List, Optional
import redis
from pathlib import Path
import hashlib
from werkzeug.utils import secure_filename

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from agentmind.core.agent import Agent, Message
from agentmind.core.mind import AgentMind

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SESSION_SECRET", "agentmind-chat-secret")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["UPLOAD_FOLDER"] = Path("./uploads")
app.config["UPLOAD_FOLDER"].mkdir(exist_ok=True)

CORS(app)
socketio = SocketIO(
    app, cors_allowed_origins="*", async_mode="threading", max_http_buffer_size=16 * 1024 * 1024
)

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "doc",
    "docx",
    "py",
    "js",
    "html",
    "css",
    "json",
    "xml",
    "md",
    "csv",
}

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
message_threads: Dict[str, List[str]] = {}  # thread_id -> [message_ids]
agents_initialized = False
mind = AgentMind()

# Typing indicators
typing_users: Dict[str, Set[str]] = {}  # session_id -> set of user names


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
    ]

    for name, role, emoji, description in agent_configs:
        agent = Agent(name, role)
        agent.emoji = emoji
        agent.description = description
        mind.add_agent(agent)

    agents_initialized = True
    print(f"[✓] Initialized {len(mind.agents)} agents")


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_session(session_id: str) -> Optional[Dict]:
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
            redis_client.setex(f"chat_session:{session_id}", 86400, json.dumps(data))
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

        # Include attachments
        if msg.get("attachments"):
            md += "**Attachments:**\n"
            for att in msg["attachments"]:
                md += f"- {att['filename']} ({att['size']} bytes)\n"
            md += "\n"

        # Include thread info
        if msg.get("thread_id"):
            md += f"*Thread: {msg['thread_id']}*\n\n"

        md += "---\n\n"

    return md


@app.route("/")
def index():
    """Serve the enhanced chat interface."""
    return render_template("chat_wave2.html")


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "agents": len(mind.agents),
            "redis_connected": redis_client is not None,
            "features": ["file_upload", "threading", "syntax_highlighting", "export"],
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
                            "last_message": (
                                data.get("messages", [])[-1] if data.get("messages") else None
                            ),
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
                    "last_message": data.get("messages", [])[-1] if data.get("messages") else None,
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
    """Export session to various formats."""
    format_type = request.args.get("format", "markdown")

    if format_type == "markdown":
        md_content = export_to_markdown(session_id)
        filename = f"agentmind_session_{session_id[:8]}.md"
        temp_path = app.config["UPLOAD_FOLDER"] / filename

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return send_file(
            temp_path, as_attachment=True, download_name=filename, mimetype="text/markdown"
        )

    elif format_type == "json":
        session = get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        filename = f"agentmind_session_{session_id[:8]}.json"
        temp_path = app.config["UPLOAD_FOLDER"] / filename

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2)

        return send_file(
            temp_path, as_attachment=True, download_name=filename, mimetype="application/json"
        )

    return jsonify({"error": "Unsupported format"}), 400


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file uploads."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_ext = filename.rsplit(".", 1)[1].lower()
        saved_filename = f"{file_id}.{file_ext}"
        file_path = app.config["UPLOAD_FOLDER"] / saved_filename

        file.save(file_path)

        return jsonify(
            {
                "success": True,
                "file_id": file_id,
                "filename": filename,
                "size": file_path.stat().st_size,
                "path": str(file_path),
            }
        )

    return jsonify({"error": "File type not allowed"}), 400


@app.route("/api/search/<session_id>", methods=["GET"])
def search_messages(session_id: str):
    """Search messages in a session."""
    query = request.args.get("q", "").lower()
    session = get_session(session_id)

    if not session:
        return jsonify({"error": "Session not found"}), 404

    results = []
    for msg in session.get("messages", []):
        if query in msg.get("content", "").lower():
            results.append(msg)

    return jsonify({"results": results, "count": len(results)})


@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    initialize_agents()

    session_id = str(uuid.uuid4())

    session_data = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "threads": {},
    }
    save_session(session_id, session_data)

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
    """Handle user message with threading support."""
    content = data.get("content", "")
    username = data.get("username", "User")
    session_id = data.get("session_id")
    thread_id = data.get("thread_id")
    attachments = data.get("attachments", [])

    if not content.strip() and not attachments:
        return

    message_id = str(uuid.uuid4())
    message_data = {
        "id": message_id,
        "sender": username,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "type": "user",
        "emoji": "👤",
        "thread_id": thread_id,
        "attachments": attachments,
    }

    session = get_session(session_id)
    if session:
        session["messages"].append(message_data)
        save_session(session_id, session)

    emit("new_message", message_data, room=session_id, broadcast=True)

    user_msg = Message(content=content, sender=username)

    def process_agents():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            responses = loop.run_until_complete(
                mind.broadcast_message(user_msg, exclude_sender=False)
            )

            for response in responses:
                agent = next((a for a in mind.agents if a.name == response.sender), None)

                agent_message = {
                    "id": str(uuid.uuid4()),
                    "sender": response.sender,
                    "content": response.content,
                    "timestamp": response.timestamp.strftime("%H:%M:%S"),
                    "type": "agent",
                    "role": agent.role if agent else "assistant",
                    "emoji": getattr(agent, "emoji", "🤖") if agent else "🤖",
                    "thread_id": thread_id,
                    "reply_to": message_id,
                }

                session = get_session(session_id)
                if session:
                    session["messages"].append(agent_message)
                    save_session(session_id, session)

                socketio.emit("new_message", agent_message, room=session_id)

        finally:
            loop.close()

    socketio.start_background_task(process_agents)


@socketio.on("typing")
def handle_typing(data):
    """Handle typing indicator."""
    session_id = data.get("session_id")
    username = data.get("username")
    is_typing = data.get("is_typing", True)

    emit(
        "user_typing",
        {"username": username, "is_typing": is_typing},
        room=session_id,
        broadcast=True,
        include_self=False,
    )


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


@socketio.on("react_message")
def handle_message_reaction(data):
    """Handle message reactions."""
    session_id = data.get("session_id")
    message_id = data.get("message_id")
    reaction = data.get("reaction")
    username = data.get("username")

    emit(
        "message_reaction",
        {"message_id": message_id, "reaction": reaction, "username": username},
        room=session_id,
        broadcast=True,
    )


@socketio.on("bookmark_message")
def handle_bookmark_message(data):
    """Handle message bookmarking."""
    session_id = data.get("session_id")
    message_id = data.get("message_id")
    bookmarked = data.get("bookmarked", True)

    emit(
        "message_bookmarked",
        {"message_id": message_id, "bookmarked": bookmarked},
        room=session_id,
        broadcast=True,
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AgentMind Enhanced Chat Server (Wave 2)")
    print("=" * 60)
    print("📡 Server: http://localhost:5000")
    print("💬 Features: Threading, File Upload, Syntax Highlighting")
    print("📤 Export: Markdown, JSON")
    print("=" * 60)
    socketio.run(app, debug=False, host="0.0.0.0", port=5000)
