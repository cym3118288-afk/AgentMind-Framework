# AgentMind Chat - System Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Chat Interface (HTML)                   │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │   Sidebar   │  │  Chat Area   │  │  Input Area     │  │  │
│  │  │             │  │              │  │                 │  │  │
│  │  │ Agent List  │  │  Messages    │  │  Text Input     │  │  │
│  │  │ - Alice 🔍  │  │  - User      │  │  Emoji Picker   │  │  │
│  │  │ - Bob 🎨    │  │  - Agents    │  │  Send Button    │  │  │
│  │  │ - Charlie📋 │  │  - System    │  │                 │  │  │
│  │  │ ... (12)    │  │              │  │                 │  │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                    JavaScript (chat.js)                          │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                    WebSocket (Socket.IO)
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│                      FLASK SERVER                                 │
│                     (chat_server.py)                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Flask-SocketIO Handler                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │  │
│  │  │   connect    │  │ user_message │  │  toggle_agent   │ │  │
│  │  │   handler    │  │   handler    │  │    handler      │ │  │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│  ┌────────────────────────────▼──────────────────────────────┐   │
│  │                    AgentMind Core                         │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │              AgentMind Instance                      │ │   │
│  │  │  - Manages 12 agents                                 │ │   │
│  │  │  - Broadcasts messages                               │ │   │
│  │  │  - Tracks conversation history                       │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  │                              │                             │   │
│  │  ┌───────────────────────────▼──────────────────────────┐ │   │
│  │  │                  Agent Pool                          │ │   │
│  │  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │ │   │
│  │  │  │Alice │ │ Bob  │ │Charlie│ │Diana │ │ Eve  │ ...  │ │   │
│  │  │  │ 🔍   │ │ 🎨   │ │ 📋   │ │ 💻   │ │ 📚   │      │ │   │
│  │  │  │Analyst│ │Creative│ │Coord│ │Tech │ │Research│    │ │   │
│  │  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘      │ │   │
│  │  │                                                       │ │   │
│  │  │  Each agent has:                                     │ │   │
│  │  │  - Name & Role                                       │ │   │
│  │  │  - Memory (conversation history)                     │ │   │
│  │  │  - Active status (on/off)                            │ │   │
│  │  │  - process_message() method                          │ │   │
│  │  └───────────────────────────────────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

## Message Flow

```
1. USER SENDS MESSAGE
   User types: "Hello, what's your opinion on AI?"
   ↓
2. FRONTEND CAPTURES
   chat.js captures input, validates, formats
   ↓
3. WEBSOCKET SEND
   Socket.IO emits 'user_message' event
   ↓
4. SERVER RECEIVES
   chat_server.py receives message
   ↓
5. BROADCAST TO CLIENTS
   Server broadcasts message to all connected clients
   ↓
6. CREATE MESSAGE OBJECT
   Message(content="Hello...", sender="User")
   ↓
7. AGENTMIND PROCESSES
   mind.broadcast_message(message)
   ↓
8. AGENTS RESPOND (ASYNC)
   ┌─────────────────────────────────────┐
   │ Alice (Analyst):                    │
   │ "From a data perspective..."        │
   ├─────────────────────────────────────┤
   │ Bob (Creative):                     │
   │ "This gives me an interesting..."   │
   ├─────────────────────────────────────┤
   │ Charlie (Coordinator):              │
   │ "Let's integrate perspectives..."   │
   ├─────────────────────────────────────┤
   │ ... (all active agents)             │
   └─────────────────────────────────────┘
   ↓
9. RESPONSES SENT BACK
   Each response emitted via WebSocket
   ↓
10. FRONTEND DISPLAYS
    Messages appear in real-time in chat area
```

## Component Interaction

```
┌──────────────┐     WebSocket      ┌──────────────┐
│   Frontend   │ ←─────────────────→ │   Backend    │
│  (Browser)   │                     │   (Flask)    │
└──────────────┘                     └──────────────┘
       │                                     │
       │                                     │
   ┌───▼────┐                           ┌───▼────┐
   │ HTML   │                           │ Socket │
   │ CSS    │                           │  IO    │
   │ JS     │                           └────────┘
   └────────┘                                │
       │                                     │
   ┌───▼────────┐                      ┌────▼─────┐
   │ Socket.IO  │                      │AgentMind │
   │  Client    │                      │Framework │
   └────────────┘                      └──────────┘
                                            │
                                       ┌────▼────┐
                                       │ Agents  │
                                       │ (12)    │
                                       └─────────┘
```

## File Dependencies

```
chat_server.py
├── imports Flask, Flask-SocketIO
├── imports agentmind.core.agent (Agent, Message)
├── imports agentmind.core.mind (AgentMind)
├── serves templates/chat.html
└── serves static files (CSS, JS)

templates/chat.html
├── links to static/css/chat.css
├── links to static/js/chat.js
└── includes Socket.IO CDN

static/js/chat.js
├── connects to Socket.IO server
├── handles DOM manipulation
└── manages real-time events

static/css/chat.css
└── styles all UI components

src/agentmind/core/
├── agent.py (Agent, Message classes)
└── mind.py (AgentMind orchestrator)
```

## Technology Stack

```
┌─────────────────────────────────────┐
│         Frontend Layer              │
│  - HTML5                            │
│  - CSS3 (Flexbox, Grid, Animations) │
│  - Vanilla JavaScript (ES6+)        │
│  - Socket.IO Client                 │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      Communication Layer            │
│  - WebSocket Protocol               │
│  - Socket.IO (v4.5.4)               │
│  - Real-time Bidirectional          │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│         Backend Layer               │
│  - Python 3.7+                      │
│  - Flask (Web Framework)            │
│  - Flask-SocketIO                   │
│  - Asyncio (Concurrent Processing)  │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│       Application Layer             │
│  - AgentMind Framework              │
│  - Agent Management                 │
│  - Message Broadcasting             │
│  - Memory System                    │
└─────────────────────────────────────┘
```

## Deployment Architecture

```
                    ┌──────────────┐
                    │   Browser    │
                    │  (Client)    │
                    └──────┬───────┘
                           │
                    HTTP/WebSocket
                           │
                    ┌──────▼───────┐
                    │   Port 5000  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Flask Server │
                    │ chat_server  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼───┐   ┌───▼────┐  ┌───▼────┐
         │ Static │   │Template│  │AgentMind│
         │ Files  │   │ Engine │  │Framework│
         └────────┘   └────────┘  └────────┘
```

## Data Flow Example

```
User Input: "What do you think about AI?"

1. Frontend captures input
   → {content: "What do you think about AI?", username: "User"}

2. WebSocket transmission
   → emit('user_message', data)

3. Server receives
   → handle_user_message(data)

4. Create Message object
   → Message(content="What...", sender="User")

5. Broadcast to agents
   → mind.broadcast_message(message)

6. Each agent processes (async)
   → Alice: "[Analysis] From a data perspective..."
   → Bob: "[Creative] This gives me an idea..."
   → Charlie: "[Coordination] Let's integrate..."
   → ... (9 more agents)

7. Responses sent back
   → emit('new_message', {sender, content, timestamp, ...})

8. Frontend displays
   → Append message to messagesContainer
   → Scroll to bottom
   → Show with animation
```

This architecture provides a scalable, real-time multi-agent chat system with clean separation of concerns and modern web technologies.
