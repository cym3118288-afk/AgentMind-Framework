@echo off
echo ==========================================
echo   AgentMind Chat - Quick Start
echo ==========================================
echo.

echo Step 1: Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo Step 2: Installing AgentMind framework...
python -m pip install -e .

echo.
echo ==========================================
echo   Installation Complete!
echo ==========================================
echo.
echo Starting AgentMind Chat Server...
echo.

python chat_server.py
pause
