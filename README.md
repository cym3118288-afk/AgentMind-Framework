# AgentMind

Multi-Agent Collaboration Framework - Lightweight Python framework for building collaborative AI agent systems

## Overview

AgentMind is a lightweight Python framework for building multi-agent systems where AI agents with different roles can collaborate to solve problems.

## Features

- Multiple Agent Roles: Create agents with different personalities and expertise
- Message Broadcasting: Agents can communicate and respond to each other
- Memory System: Each agent maintains conversation history
- Async Support: Built on asyncio for efficient concurrent operations
- Collaboration Tracking: Monitor conversation flow and agent activity

## Quick Start

```python
from agentmind.core.agent import Agent
from agentmind.core.mind import AgentMind
import asyncio

async def main():
    # Create AgentMind instance
    mind = AgentMind()
    
    # Create agents with different roles
    analyst = Agent("Alice", "analyst")
    creative = Agent("Bob", "creative")
    coordinator = Agent("Charlie", "coordinator")
    
    # Add agents to the system
    mind.add_agent(analyst)
    mind.add_agent(creative)
    mind.add_agent(coordinator)
    
    # Start collaboration
    await mind.start_collaboration("Let's brainstorm ideas for a new app")
    
    # Get summary
    summary = mind.get_conversation_summary()
    print(summary)

asyncio.run(main())
```

## Installation

```bash
# Clone the repository
git clone https://github.com/cym3118288-afk/AgentMind-Framework.git
cd AgentMind-Framework

# Install in development mode
pip install -e .
```

## Running Examples

```bash
cd examples
python basic_collaboration.py
python debate_example.py
```

## Project Structure

```
agentmind/
├── src/
│   └── agentmind/
│       ├── __init__.py
│       └── core/
│           ├── __init__.py
│           ├── agent.py      # Agent and Message classes
│           └── mind.py       # AgentMind orchestrator
├── examples/
│   ├── basic_collaboration.py
│   └── debate_example.py
├── tests/
│   └── test_basic.py
├── README.md
└── setup.py
```

## Core Concepts

### Agent

An agent represents an AI entity with:
- Name: Unique identifier
- Role: Defines behavior (analyst, creative, coordinator, etc.)
- Memory: Stores conversation history
- Active Status: Can be enabled/disabled

### Message

A message contains:
- Content: The actual message text
- Sender: Who sent the message
- Timestamp: When it was sent

### AgentMind

The orchestrator that:
- Manages multiple agents
- Broadcasts messages between agents
- Tracks conversation history
- Provides collaboration summaries

## Use Cases

- Brainstorming: Multiple perspectives on creative problems
- Analysis: Different analytical approaches to data
- Decision Making: Collaborative problem solving
- Idea Generation: Creative collaboration between agents
- Research: Multi-angle investigation of topics

## Testing

Run the test suite:

```bash
python tests/test_basic.py
```

## License

MIT License

