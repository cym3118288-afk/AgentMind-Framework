# AgentMind Chat Interface

A real-time web-based chat interface for multi-agent collaboration. Chat with 10+ AI agents simultaneously in a modern, social-media-style interface.

## Features

- **Multi-Agent Chat**: Interact with 12 different AI agents, each with unique roles and personalities
- **Real-Time Communication**: WebSocket-based instant messaging
- **Emoji Support**: Full emoji picker and emoticon support
- **Modern UI**: Clean, responsive design similar to popular chat applications
- **Agent Management**: Toggle agents on/off during conversations
- **Role-Based Responses**: Each agent responds according to their specialized role

## Agents

The system includes 12 pre-configured agents:

1. **Alice** 🔍 - Analyst
2. **Bob** 🎨 - Creative
3. **Charlie** 📋 - Coordinator
4. **Diana** 💻 - Technical
5. **Eve** 📚 - Researcher
6. **Frank** ♟️ - Strategist
7. **Grace** ✨ - Designer
8. **Henry** ⚙️ - Developer
9. **Iris** 📢 - Marketer
10. **Jack** 🤔 - Philosopher
11. **Kate** 🔬 - Scientist
12. **Leo** 💡 - Entrepreneur

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the AgentMind framework is installed:
```bash
pip install -e .
```

## Running the Chat Server

Start the server:
```bash
python chat_server.py
```

The server will start on `http://localhost:5000`

Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Set Your Username**: Enter your name in the sidebar (default: "User")
2. **Send Messages**: Type in the input box and press Enter or click Send
3. **Use Emojis**: Click the emoji button to open the emoji picker
4. **Toggle Agents**: Click on any agent in the sidebar to enable/disable them
5. **View Responses**: All active agents will respond to your messages in real-time

## Keyboard Shortcuts

- **Enter**: Send message
- **Shift + Enter**: New line in message

## Architecture

### Backend (Flask + SocketIO)
- `chat_server.py`: Main server with WebSocket handling
- Integrates with AgentMind framework for agent management
- Handles real-time message broadcasting

### Frontend
- `templates/chat.html`: Main chat interface
- `static/css/chat.css`: Modern, responsive styling
- `static/js/chat.js`: WebSocket client and UI interactions

### AgentMind Integration
- Uses the existing `Agent` and `AgentMind` classes
- Async message processing for concurrent agent responses
- Memory system for conversation history

## Customization

### Adding More Agents

Edit `chat_server.py` and add to the `agent_configs` list:

```python
agent_configs = [
    ("AgentName", "role", "emoji"),
    # Add more agents here
]
```

### Changing Agent Behavior

Modify the `process_message` method in `src/agentmind/core/agent.py` to customize how agents respond.

### Styling

Edit `static/css/chat.css` to customize the appearance.

## Technical Details

- **Framework**: Flask with Flask-SocketIO
- **Real-Time**: WebSocket protocol via Socket.IO
- **Async**: Python asyncio for concurrent agent processing
- **Frontend**: Vanilla JavaScript (no framework dependencies)

## Troubleshooting

**Port already in use:**
```bash
# Change the port in chat_server.py:
socketio.run(app, debug=True, host='0.0.0.0', port=5001)
```

**Agents not responding:**
- Check that all agents are active (green status indicator)
- Click on inactive agents to re-enable them

**Connection issues:**
- Ensure no firewall is blocking port 5000
- Try accessing via `http://127.0.0.1:5000` instead of localhost

## Future Enhancements

- Persistent chat history
- File/image sharing
- Voice messages
- Agent personality customization
- Multi-room support
- User authentication

## License

MIT License - See LICENSE file for details
