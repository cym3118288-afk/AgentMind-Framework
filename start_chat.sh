#!/bin/bash

echo "=========================================="
echo "  AgentMind Chat - Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "Step 1: Installing dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

echo ""
echo "Step 2: Installing AgentMind framework..."
$PYTHON_CMD -m pip install -e .

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Starting AgentMind Chat Server..."
echo ""

$PYTHON_CMD chat_server.py
