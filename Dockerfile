FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for API and CLI
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    click \
    rich

# Copy application code
COPY . .

# Install AgentMind in development mode
RUN pip install -e .

# Expose ports
# 8000 for FastAPI
# 11434 for Ollama
EXPOSE 8000 11434

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Start Ollama in the background\n\
echo "Starting Ollama..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
\n\
# Wait for Ollama to be ready\n\
echo "Waiting for Ollama to be ready..."\n\
sleep 5\n\
\n\
# Pull default model if specified\n\
if [ ! -z "$OLLAMA_MODEL" ]; then\n\
    echo "Pulling model: $OLLAMA_MODEL"\n\
    ollama pull $OLLAMA_MODEL\n\
fi\n\
\n\
# Start the application based on MODE\n\
if [ "$MODE" = "api" ]; then\n\
    echo "Starting FastAPI server..."\n\
    exec uvicorn api_server:app --host 0.0.0.0 --port 8000\n\
elif [ "$MODE" = "cli" ]; then\n\
    echo "Starting CLI..."\n\
    exec python cli.py "$@"\n\
else\n\
    echo "No MODE specified. Starting FastAPI server by default..."\n\
    exec uvicorn api_server:app --host 0.0.0.0 --port 8000\n\
fi\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set environment variables
ENV OLLAMA_HOST=http://localhost:11434
ENV MODE=api
ENV OLLAMA_MODEL=llama3.2

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
