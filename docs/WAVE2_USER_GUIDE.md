# Wave 2 UI and Dashboard User Guide

## Quick Start

### Installation

1. Install Wave 2 dependencies:
```bash
pip install -r requirements-wave2.txt
```

2. Optional: Start Redis for session storage:
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally
# Windows: Download from https://redis.io/download
# Linux: sudo apt-get install redis-server
# Mac: brew install redis
```

### Starting the Services

#### Option 1: Start All Services
```bash
# Start all Wave 2 services
python agent_designer_enhanced.py &
python chat_server_wave2.py &
python dashboard_enhanced.py &
```

#### Option 2: Start Individual Services
```bash
# Agent Designer (Port 8002)
python agent_designer_enhanced.py

# Chat Server (Port 5000)
python chat_server_wave2.py

# Dashboard (Port 8001)
python dashboard_enhanced.py
```

## Agent Designer Enhanced

### Accessing the Designer
Open your browser to: http://localhost:8002/designer

### Creating an Agent Team

#### Step 1: Browse Templates
- View categorized agent templates in the left sidebar
- Categories: Development, Research, Creative, Business, Security
- Click category tabs to switch between template types

#### Step 2: Add Agents
- Drag agent templates from the sidebar to the canvas
- Drop them in the center area
- Each agent appears as a card with its role and description

#### Step 3: Configure Team
In the right panel, set:
- **Team Name**: Give your team a descriptive name
- **LLM Provider**: Choose Ollama (local), OpenAI, or Anthropic
- **Model**: Specify the model (e.g., llama3.2, gpt-4, claude-3-sonnet)
- **Max Rounds**: Set collaboration rounds (1-20)

#### Step 4: Test Your Team
1. Click "Test" in the header
2. Enter a test message
3. Click "Run Test"
4. View real-time responses in the test output panel

#### Step 5: Save and Export
- **Save Config**: Save configuration to database
- **Generate Code**: Export as ready-to-run Python code
- **Export**: Export as JSON, YAML, or Python

### Importing Configurations

1. Click "Import" in the header
2. Select a JSON or YAML file
3. Click "Import"
4. Configuration loads into the designer

### Keyboard Shortcuts
- `Delete`: Remove selected agent
- `Ctrl+S`: Save configuration
- `Ctrl+E`: Export configuration
- `Ctrl+T`: Toggle test panel

## Chat Server Wave 2

### Accessing the Chat Interface
Open your browser to: http://localhost:5000

### Features

#### Multi-Agent Conversations
- Multiple agents respond to your messages
- Each agent has a unique emoji and role
- Real-time message streaming
- Toggle agents on/off in the sidebar

#### Message Threading
- Reply to specific messages to create threads
- Thread indicators show conversation context
- Navigate between threads easily

#### File Uploads
1. Click the attachment icon (📎)
2. Select a file (max 16MB)
3. Supported formats: txt, pdf, images, code files, documents
4. File appears in the message with metadata

#### Code Sharing
- Paste code in messages
- Automatic syntax highlighting
- Language detection
- Copy code with one click

#### Exporting Conversations
1. Click "Export" button
2. Choose format:
   - **Markdown**: Human-readable format with formatting
   - **JSON**: Complete data with metadata
3. File downloads automatically

#### Search Messages
1. Click search icon (🔍)
2. Enter search term
3. View matching messages highlighted
4. Navigate between results

#### Message Reactions
- Hover over a message
- Click reaction emoji
- See who reacted to each message

#### Bookmarks
- Click bookmark icon on important messages
- View all bookmarked messages
- Quick navigation to bookmarks

### Tips
- Use Shift+Enter for new lines in messages
- Press Enter to send
- Type to show typing indicator to others
- Click agent names to view their profiles

## Dashboard Enhanced

### Accessing the Dashboard
Open your browser to: http://localhost:8001

### Dashboard Overview

#### Real-Time Metrics
The dashboard updates every 2 seconds with:
- Total requests
- Total tokens used
- Total cost
- Error rate
- Average response time
- Active agents
- Alert count

#### System Resources
Monitor in real-time:
- CPU usage (%)
- Memory usage (%)
- Disk usage (%)
- Network I/O

### Agent Performance Comparison

View the comparison table to see:
- Requests per agent
- Average response time
- Success rate
- Total cost
- Tokens per request

Sort by any column to identify:
- Most used agents
- Slowest agents
- Most expensive agents
- Most reliable agents

### Historical Analysis

1. Select time range (1h, 6h, 24h, 7d)
2. View charts showing:
   - Request volume over time
   - Token usage trends
   - Cost accumulation
   - Error rate changes
   - Response time patterns

### Alert Management

#### Viewing Alerts
- Active alerts appear in the alerts panel
- Color-coded by severity:
  - 🔴 Critical: Immediate attention required
  - 🟡 Warning: Monitor closely
  - 🟢 Info: Informational only

#### Configuring Alerts
1. Click "Alert Settings"
2. Set thresholds:
   - Response time (ms)
   - Error rate (%)
   - Cost ($)
   - Memory usage (%)
   - CPU usage (%)
3. Click "Save"

#### Acknowledging Alerts
- Click "Acknowledge" on an alert
- Alert moves to acknowledged section
- Stops notification sounds

### Cost Optimization

#### Recommendations Panel
View automated recommendations:
- Switch to cheaper models
- Use local models for development
- Optimize slow agents
- Fix high error rates

#### Cost Analysis
- View cost breakdown by agent
- See cost trends over time
- Identify expensive operations
- Get savings estimates

### Exporting Metrics

1. Click "Export Metrics"
2. Choose format (JSON)
3. Select time range
4. Download file

Export includes:
- Summary statistics
- Per-agent metrics
- Recent request history
- System metrics

### WebSocket Connection

The dashboard uses WebSocket for real-time updates:
- Automatic reconnection on disconnect
- Live metric streaming
- Instant alert notifications
- No page refresh needed

## API Usage

### Agent Designer API

#### Get Templates
```bash
curl http://localhost:8002/api/templates
```

#### Save Configuration
```bash
curl -X POST http://localhost:8002/api/configs \
  -H "Content-Type: application/json" \
  -d '{
    "team_name": "My Team",
    "agents": [{"name": "Agent1", "role": "test"}]
  }'
```

#### Export Configuration
```bash
curl http://localhost:8002/api/configs/{config_id}/export?format=python \
  -o my_team.py
```

### Chat Server API

#### Upload File
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@document.pdf"
```

#### Export Session
```bash
curl http://localhost:5000/api/sessions/{session_id}/export?format=markdown \
  -o conversation.md
```

#### Search Messages
```bash
curl "http://localhost:5000/api/search/{session_id}?q=search+term"
```

### Dashboard API

#### Get Metrics Summary
```bash
curl http://localhost:8001/api/metrics/summary
```

#### Get Agent Comparison
```bash
curl http://localhost:8001/api/metrics/comparison
```

#### Update Alert Config
```bash
curl -X POST http://localhost:8001/api/alerts/config \
  -H "Content-Type: application/json" \
  -d '{
    "response_time_threshold": 6000,
    "error_rate_threshold": 0.1
  }'
```

## Troubleshooting

### Agent Designer Issues

**Problem**: Templates not loading
- **Solution**: Check network connection, refresh page, check console for errors

**Problem**: Configuration won't save
- **Solution**: Validate configuration, check disk space, ensure write permissions

**Problem**: WebSocket connection fails
- **Solution**: Check firewall, ensure port 8002 is open, try different browser

### Chat Server Issues

**Problem**: File upload fails
- **Solution**: Check file size (<16MB), verify file type is allowed, check disk space

**Problem**: Messages not appearing
- **Solution**: Check WebSocket connection, refresh page, check Redis connection

**Problem**: Export not working
- **Solution**: Ensure session exists, check browser download settings

### Dashboard Issues

**Problem**: Metrics not updating
- **Solution**: Check WebSocket connection, verify services are running

**Problem**: High CPU usage
- **Solution**: Increase update interval, reduce history size, check for memory leaks

**Problem**: Alerts not triggering
- **Solution**: Verify alert thresholds, check alert configuration, ensure metrics are being collected

### General Issues

**Problem**: Port already in use
- **Solution**: Change port in code or stop conflicting service
```bash
# Find process using port
lsof -i :8002  # Mac/Linux
netstat -ano | findstr :8002  # Windows

# Kill process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

**Problem**: Redis connection failed
- **Solution**: Services work without Redis (in-memory mode), or start Redis server

**Problem**: Module not found
- **Solution**: Install dependencies
```bash
pip install -r requirements-wave2.txt
```

## Best Practices

### Agent Designer
1. Start with templates, customize as needed
2. Test configurations before deploying
3. Use descriptive team names
4. Export configurations regularly
5. Version control your configurations

### Chat Server
1. Clear old sessions periodically
2. Limit file upload sizes
3. Use threading for organized conversations
4. Export important conversations
5. Monitor session storage

### Dashboard
1. Set appropriate alert thresholds
2. Review recommendations regularly
3. Export metrics for analysis
4. Monitor resource usage
5. Acknowledge alerts promptly

## Advanced Usage

### Custom Templates
Add custom agent templates by editing `agent_designer_enhanced.py`:
```python
AGENT_TEMPLATES["custom"] = [
    {
        "id": "my_agent",
        "name": "My Custom Agent",
        "role": "custom",
        "description": "Does custom things",
        "icon": "🎯",
        "system_prompt": "You are a custom agent...",
        "plugins": ["custom_plugin"],
        "capabilities": ["custom_capability"]
    }
]
```

### Custom Metrics
Add custom metrics to the dashboard:
```python
# In dashboard_enhanced.py
metrics_store.add_request({
    "agent": "MyAgent",
    "duration": 1500,
    "tokens": 750,
    "cost": 0.015,
    "success": True,
    "timestamp": datetime.now().isoformat(),
    "custom_field": "custom_value"
})
```

### WebSocket Integration
Connect to WebSocket from your application:
```javascript
// Agent Designer Testing
const ws = new WebSocket('ws://localhost:8002/ws/test');
ws.send(JSON.stringify({
    action: 'test_agent',
    agent: {name: 'TestAgent', role: 'test'},
    input: 'Hello'
}));

// Dashboard Metrics
const ws = new WebSocket('ws://localhost:8001/ws/metrics');
ws.onmessage = (event) => {
    const metrics = JSON.parse(event.data);
    console.log('Metrics:', metrics);
};
```

## Support

For issues, questions, or feature requests:
1. Check this guide first
2. Review API documentation at `/docs` endpoints
3. Check logs for error messages
4. Create an issue on GitHub
5. Contact the development team

## Next Steps

After mastering Wave 2 features:
1. Explore Wave 3 production features
2. Integrate with your applications
3. Customize templates and dashboards
4. Deploy to production
5. Scale horizontally with load balancing

Happy building with AgentMind! 🚀
