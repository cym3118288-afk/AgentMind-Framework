"""
Enhanced Monitoring Dashboard - Wave 2 Implementation

Features:
- Real-time metrics visualization with Chart.js and Plotly
- Agent performance comparison and benchmarking
- Resource usage tracking (CPU, memory, tokens)
- Alert configuration UI with thresholds
- Historical data analysis with time-series charts
- Cost optimization recommendations
- Export metrics and reports
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import sys
from pathlib import Path
import redis
import psutil
from collections import defaultdict, deque

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

app = FastAPI(title="AgentMind Dashboard Enhanced", version="0.4.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
STATIC_DIR = Path("./dashboard/public")
TEMPLATES_DIR = Path("./dashboard/views")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if TEMPLATES_DIR.exists():
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
else:
    templates = None

# Redis for metrics storage
try:
    redis_client = redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/2"), decode_responses=True
    )
    redis_client.ping()
    print("[✓] Redis connected")
except:
    redis_client = None
    print("[!] Redis not available, using in-memory storage")

# WebSocket connections
active_connections: List[WebSocket] = []


# In-memory metrics storage
class MetricsStore:
    def __init__(self, max_history=1000):
        self.max_history = max_history
        self.requests = deque(maxlen=max_history)
        self.agent_metrics = defaultdict(
            lambda: {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "avg_response_time": 0,
                "error_count": 0,
                "success_count": 0,
            }
        )
        self.system_metrics = deque(maxlen=max_history)
        self.alerts = []
        self.alert_config = {
            "response_time_threshold": 5000,  # ms
            "error_rate_threshold": 0.05,  # 5%
            "cost_threshold": 100,  # $100
            "memory_threshold": 80,  # 80%
            "cpu_threshold": 80,  # 80%
        }

    def add_request(self, request_data: Dict):
        """Add a request to metrics."""
        self.requests.append(request_data)

        agent_name = request_data.get("agent")
        if agent_name:
            metrics = self.agent_metrics[agent_name]
            metrics["total_requests"] += 1
            metrics["total_tokens"] += request_data.get("tokens", 0)
            metrics["total_cost"] += request_data.get("cost", 0)

            if request_data.get("success"):
                metrics["success_count"] += 1
            else:
                metrics["error_count"] += 1

            # Update average response time
            current_avg = metrics["avg_response_time"]
            new_time = request_data.get("duration", 0)
            total = metrics["total_requests"]
            metrics["avg_response_time"] = (current_avg * (total - 1) + new_time) / total

    def add_system_metrics(self, metrics: Dict):
        """Add system metrics."""
        self.system_metrics.append(metrics)

    def check_alerts(self):
        """Check for alert conditions."""
        new_alerts = []

        # Check response time
        if self.requests:
            recent_times = [r.get("duration", 0) for r in list(self.requests)[-10:]]
            avg_time = sum(recent_times) / len(recent_times) if recent_times else 0

            if avg_time > self.alert_config["response_time_threshold"]:
                new_alerts.append(
                    {
                        "type": "response_time",
                        "severity": "warning",
                        "message": f"Average response time ({avg_time:.0f}ms) exceeds threshold",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Check error rate
        total_requests = sum(m["total_requests"] for m in self.agent_metrics.values())
        total_errors = sum(m["error_count"] for m in self.agent_metrics.values())

        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > self.alert_config["error_rate_threshold"]:
                new_alerts.append(
                    {
                        "type": "error_rate",
                        "severity": "critical",
                        "message": f"Error rate ({error_rate*100:.1f}%) exceeds threshold",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Check total cost
        total_cost = sum(m["total_cost"] for m in self.agent_metrics.values())
        if total_cost > self.alert_config["cost_threshold"]:
            new_alerts.append(
                {
                    "type": "cost",
                    "severity": "warning",
                    "message": f"Total cost (${total_cost:.2f}) exceeds threshold",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Check system resources
        if self.system_metrics:
            latest = self.system_metrics[-1]

            if latest.get("memory_percent", 0) > self.alert_config["memory_threshold"]:
                new_alerts.append(
                    {
                        "type": "memory",
                        "severity": "warning",
                        "message": f"Memory usage ({latest['memory_percent']:.1f}%) exceeds threshold",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            if latest.get("cpu_percent", 0) > self.alert_config["cpu_threshold"]:
                new_alerts.append(
                    {
                        "type": "cpu",
                        "severity": "warning",
                        "message": f"CPU usage ({latest['cpu_percent']:.1f}%) exceeds threshold",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        self.alerts.extend(new_alerts)
        return new_alerts

    def get_summary(self) -> Dict:
        """Get metrics summary."""
        total_requests = sum(m["total_requests"] for m in self.agent_metrics.values())
        total_tokens = sum(m["total_tokens"] for m in self.agent_metrics.values())
        total_cost = sum(m["total_cost"] for m in self.agent_metrics.values())
        total_errors = sum(m["error_count"] for m in self.agent_metrics.values())

        error_rate = (total_errors / total_requests) if total_requests > 0 else 0

        # Calculate average response time across all agents
        if self.agent_metrics:
            avg_response_time = sum(
                m["avg_response_time"] for m in self.agent_metrics.values()
            ) / len(self.agent_metrics)
        else:
            avg_response_time = 0

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "active_agents": len(self.agent_metrics),
            "alert_count": len(
                [
                    a
                    for a in self.alerts
                    if (datetime.now() - datetime.fromisoformat(a["timestamp"])).seconds < 3600
                ]
            ),
        }


metrics_store = MetricsStore()

# LLM Pricing (per 1M tokens)
LLM_PRICING = {
    "llama3.2": {"input": 0, "output": 0, "provider": "Ollama (Local)"},
    "gpt-4": {"input": 30, "output": 60, "provider": "OpenAI"},
    "gpt-4-turbo": {"input": 10, "output": 30, "provider": "OpenAI"},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5, "provider": "OpenAI"},
    "claude-3-opus": {"input": 15, "output": 75, "provider": "Anthropic"},
    "claude-3-sonnet": {"input": 3, "output": 15, "provider": "Anthropic"},
    "claude-3-haiku": {"input": 0.25, "output": 1.25, "provider": "Anthropic"},
}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Dashboard home page."""
    if templates:
        return templates.TemplateResponse("dashboard_enhanced.html", {"request": request})

    return HTMLResponse(
        content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgentMind Dashboard Enhanced</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <h1>AgentMind Dashboard Enhanced</h1>
        <p>Dashboard is loading...</p>
        <script>
            // WebSocket connection for real-time updates
            const ws = new WebSocket('ws://localhost:8001/ws/metrics');
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Metrics update:', data);
            };
        </script>
    </body>
    </html>
    """
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.4.0",
        "redis_connected": redis_client is not None,
        "features": [
            "real_time_metrics",
            "alerts",
            "performance_comparison",
            "historical_analysis",
        ],
    }


@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """Get metrics summary."""
    summary = metrics_store.get_summary()

    # Add system metrics
    try:
        summary["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }
    except:
        summary["system"] = {}

    return summary


@app.get("/api/metrics/agents")
async def get_agent_metrics():
    """Get per-agent metrics."""
    return {"agents": dict(metrics_store.agent_metrics)}


@app.get("/api/metrics/agents/{agent_name}")
async def get_agent_metrics_detail(agent_name: str):
    """Get detailed metrics for a specific agent."""
    if agent_name not in metrics_store.agent_metrics:
        raise HTTPException(status_code=404, detail="Agent not found")

    metrics = metrics_store.agent_metrics[agent_name]

    # Get request history for this agent
    agent_requests = [r for r in metrics_store.requests if r.get("agent") == agent_name]

    return {
        "agent": agent_name,
        "metrics": metrics,
        "recent_requests": list(agent_requests)[-50:],  # Last 50 requests
    }


@app.get("/api/metrics/comparison")
async def get_agent_comparison():
    """Compare performance across agents."""
    comparison = []

    for agent_name, metrics in metrics_store.agent_metrics.items():
        comparison.append(
            {
                "agent": agent_name,
                "total_requests": metrics["total_requests"],
                "avg_response_time": metrics["avg_response_time"],
                "success_rate": (
                    metrics["success_count"] / metrics["total_requests"]
                    if metrics["total_requests"] > 0
                    else 0
                ),
                "total_cost": metrics["total_cost"],
                "tokens_per_request": (
                    metrics["total_tokens"] / metrics["total_requests"]
                    if metrics["total_requests"] > 0
                    else 0
                ),
            }
        )

    # Sort by total requests
    comparison.sort(key=lambda x: x["total_requests"], reverse=True)

    return {"comparison": comparison}


@app.get("/api/metrics/historical")
async def get_historical_metrics(hours: int = 24):
    """Get historical metrics."""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    # Filter requests by time
    recent_requests = [
        r
        for r in metrics_store.requests
        if datetime.fromisoformat(r.get("timestamp", datetime.now().isoformat())) > cutoff_time
    ]

    # Group by hour
    hourly_data = defaultdict(
        lambda: {"requests": 0, "tokens": 0, "cost": 0, "avg_duration": 0, "errors": 0}
    )

    for req in recent_requests:
        timestamp = datetime.fromisoformat(req.get("timestamp", datetime.now().isoformat()))
        hour_key = timestamp.strftime("%Y-%m-%d %H:00")

        hourly_data[hour_key]["requests"] += 1
        hourly_data[hour_key]["tokens"] += req.get("tokens", 0)
        hourly_data[hour_key]["cost"] += req.get("cost", 0)
        hourly_data[hour_key]["avg_duration"] += req.get("duration", 0)
        if not req.get("success", True):
            hourly_data[hour_key]["errors"] += 1

    # Calculate averages
    for hour_key in hourly_data:
        if hourly_data[hour_key]["requests"] > 0:
            hourly_data[hour_key]["avg_duration"] /= hourly_data[hour_key]["requests"]

    return {"period": f"{hours} hours", "data": dict(hourly_data)}


@app.get("/api/alerts")
async def get_alerts():
    """Get active alerts."""
    # Filter alerts from last 24 hours
    cutoff = datetime.now() - timedelta(hours=24)
    recent_alerts = [
        a for a in metrics_store.alerts if datetime.fromisoformat(a["timestamp"]) > cutoff
    ]

    return {"alerts": recent_alerts, "count": len(recent_alerts)}


@app.get("/api/alerts/config")
async def get_alert_config():
    """Get alert configuration."""
    return {"config": metrics_store.alert_config}


@app.post("/api/alerts/config")
async def update_alert_config(request: Request):
    """Update alert configuration."""
    config = await request.json()
    metrics_store.alert_config.update(config)
    return {"success": True, "config": metrics_store.alert_config}


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Acknowledge an alert."""
    if 0 <= alert_id < len(metrics_store.alerts):
        metrics_store.alerts[alert_id]["acknowledged"] = True
        metrics_store.alerts[alert_id]["acknowledged_at"] = datetime.now().isoformat()
        return {"success": True}

    raise HTTPException(status_code=404, detail="Alert not found")


@app.get("/api/recommendations")
async def get_recommendations():
    """Get cost optimization recommendations."""
    recommendations = []

    # Check for expensive models
    for agent_name, metrics in metrics_store.agent_metrics.items():
        if metrics["total_cost"] > 10:
            recommendations.append(
                {
                    "type": "cost_optimization",
                    "severity": "medium",
                    "agent": agent_name,
                    "message": f"Agent '{agent_name}' has high costs (${metrics['total_cost']:.2f})",
                    "suggestion": "Consider using a cheaper model or local LLM for development",
                }
            )

    # Check for slow agents
    for agent_name, metrics in metrics_store.agent_metrics.items():
        if metrics["avg_response_time"] > 5000:
            recommendations.append(
                {
                    "type": "performance",
                    "severity": "high",
                    "agent": agent_name,
                    "message": f"Agent '{agent_name}' has slow response time ({metrics['avg_response_time']:.0f}ms)",
                    "suggestion": "Optimize prompts or use a faster model",
                }
            )

    # Check for high error rates
    for agent_name, metrics in metrics_store.agent_metrics.items():
        if metrics["total_requests"] > 0:
            error_rate = metrics["error_count"] / metrics["total_requests"]
            if error_rate > 0.1:
                recommendations.append(
                    {
                        "type": "reliability",
                        "severity": "critical",
                        "agent": agent_name,
                        "message": f"Agent '{agent_name}' has high error rate ({error_rate*100:.1f}%)",
                        "suggestion": "Review error logs and fix underlying issues",
                    }
                )

    return {"recommendations": recommendations}


@app.get("/api/export/metrics")
async def export_metrics(format: str = "json"):
    """Export metrics to file."""
    summary = metrics_store.get_summary()
    agent_metrics = dict(metrics_store.agent_metrics)

    export_data = {
        "exported_at": datetime.now().isoformat(),
        "summary": summary,
        "agents": agent_metrics,
        "recent_requests": list(metrics_store.requests)[-100:],
    }

    if format == "json":
        filename = f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path(f"/tmp/{filename}")

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2)

        return FileResponse(filepath, filename=filename, media_type="application/json")

    raise HTTPException(status_code=400, detail="Unsupported format")


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics updates."""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Send metrics update every 2 seconds
            await asyncio.sleep(2)

            summary = metrics_store.get_summary()

            # Add system metrics
            try:
                summary["system"] = {
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "timestamp": datetime.now().isoformat(),
                }
            except:
                pass

            # Check for new alerts
            new_alerts = metrics_store.check_alerts()
            if new_alerts:
                summary["new_alerts"] = new_alerts

            await websocket.send_json(summary)

    except WebSocketDisconnect:
        active_connections.remove(websocket)


# Background task to collect system metrics
async def collect_system_metrics():
    """Collect system metrics periodically."""
    while True:
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "network": psutil.net_io_counters()._asdict(),
            }

            metrics_store.add_system_metrics(metrics)

            # Broadcast to all connected clients
            for connection in active_connections:
                try:
                    await connection.send_json({"type": "system_metrics", "data": metrics})
                except:
                    pass

        except Exception as e:
            print(f"Error collecting system metrics: {e}")

        await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    """Start background tasks."""
    asyncio.create_task(collect_system_metrics())

    # Simulate some initial data for demo
    for i in range(20):
        metrics_store.add_request(
            {
                "agent": ["Alice", "Bob", "Charlie"][i % 3],
                "duration": 1000 + (i * 100),
                "tokens": 500 + (i * 50),
                "cost": 0.01 + (i * 0.001),
                "success": i % 10 != 0,
                "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
            }
        )


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("📊 AgentMind Dashboard Enhanced (Wave 2)")
    print("=" * 60)
    print("📍 Dashboard: http://localhost:8001")
    print("📡 API Docs: http://localhost:8001/docs")
    print("🔄 WebSocket: ws://localhost:8001/ws/metrics")
    print("🎯 Features: Real-time, Alerts, Comparison, Historical")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8001)
