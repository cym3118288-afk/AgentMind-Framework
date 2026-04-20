/**
 * AgentMind Monitoring Dashboard
 *
 * Real-time monitoring with:
 * - Token usage tracking
 * - Cost estimation
 * - Performance metrics
 * - Bottleneck analysis
 */

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const redis = require('redis');
const axios = require('axios');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// Configuration
const PORT = process.env.PORT || 3000;
const API_URL = process.env.API_URL || 'http://localhost:8000';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379/2';
const REFRESH_INTERVAL = parseInt(process.env.REFRESH_INTERVAL) || 5000;

// Redis client
let redisClient;
(async () => {
    try {
        redisClient = redis.createClient({ url: REDIS_URL });
        await redisClient.connect();
        console.log('[✓] Redis connected');
    } catch (err) {
        console.log('[!] Redis not available:', err.message);
    }
})();

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// In-memory metrics storage
let metrics = {
    totalRequests: 0,
    activeRequests: 0,
    totalTokens: 0,
    totalCost: 0,
    avgResponseTime: 0,
    requestHistory: [],
    tokenUsageByModel: {},
    costByModel: {},
    errorRate: 0,
    errors: []
};

// LLM Pricing (per 1M tokens)
const LLM_PRICING = {
    'llama3.2': { input: 0, output: 0, provider: 'Ollama (Local)' },
    'gpt-4': { input: 30, output: 60, provider: 'OpenAI' },
    'gpt-4-turbo': { input: 10, output: 30, provider: 'OpenAI' },
    'gpt-3.5-turbo': { input: 0.5, output: 1.5, provider: 'OpenAI' },
    'claude-3-opus': { input: 15, output: 75, provider: 'Anthropic' },
    'claude-3-sonnet': { input: 3, output: 15, provider: 'Anthropic' },
    'claude-3-haiku': { input: 0.25, output: 1.25, provider: 'Anthropic' },
    'gemini-pro': { input: 0.5, output: 1.5, provider: 'Google' }
};

// Routes
app.get('/', (req, res) => {
    res.render('dashboard', {
        title: 'AgentMind Dashboard',
        apiUrl: API_URL
    });
});

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        uptime: process.uptime(),
        redis: redisClient ? redisClient.isOpen : false
    });
});

app.get('/api/metrics', async (req, res) => {
    try {
        // Fetch metrics from API
        const response = await axios.get(`${API_URL}/metrics`);

        // Parse Prometheus metrics
        const prometheusMetrics = parsePrometheusMetrics(response.data);

        // Combine with local metrics
        const combinedMetrics = {
            ...metrics,
            prometheus: prometheusMetrics,
            pricing: LLM_PRICING
        };

        res.json(combinedMetrics);
    } catch (err) {
        console.error('Error fetching metrics:', err.message);
        res.json(metrics);
    }
});

app.get('/api/sessions', async (req, res) => {
    try {
        const response = await axios.get(`${API_URL}/sessions`, {
            headers: {
                'Authorization': 'Bearer demo-token'
            }
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error fetching sessions:', err.message);
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/cost-analysis', (req, res) => {
    const analysis = {
        totalCost: metrics.totalCost,
        costByModel: metrics.costByModel,
        costTrend: calculateCostTrend(),
        recommendations: generateCostRecommendations()
    };
    res.json(analysis);
});

app.get('/api/performance', (req, res) => {
    const performance = {
        avgResponseTime: metrics.avgResponseTime,
        p50: calculatePercentile(50),
        p95: calculatePercentile(95),
        p99: calculatePercentile(99),
        bottlenecks: identifyBottlenecks(),
        throughput: calculateThroughput()
    };
    res.json(performance);
});

// WebSocket for real-time updates
io.on('connection', (socket) => {
    console.log('[+] Client connected:', socket.id);

    // Send initial metrics
    socket.emit('metrics', metrics);

    // Start sending updates
    const interval = setInterval(() => {
        socket.emit('metrics', metrics);
    }, REFRESH_INTERVAL);

    socket.on('disconnect', () => {
        console.log('[-] Client disconnected:', socket.id);
        clearInterval(interval);
    });
});

// Helper functions
function parsePrometheusMetrics(data) {
    const lines = data.split('\n');
    const parsed = {};

    for (const line of lines) {
        if (line.startsWith('#') || !line.trim()) continue;

        const match = line.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)\{?([^}]*)\}?\s+([0-9.]+)/);
        if (match) {
            const [, name, labels, value] = match;
            parsed[name] = parseFloat(value);
        }
    }

    return parsed;
}

function calculateCostTrend() {
    const history = metrics.requestHistory.slice(-20);
    if (history.length < 2) return 0;

    const recent = history.slice(-5).reduce((sum, r) => sum + (r.cost || 0), 0) / 5;
    const older = history.slice(-10, -5).reduce((sum, r) => sum + (r.cost || 0), 0) / 5;

    return older > 0 ? ((recent - older) / older) * 100 : 0;
}

function generateCostRecommendations() {
    const recommendations = [];

    // Check for expensive models
    for (const [model, cost] of Object.entries(metrics.costByModel)) {
        if (cost > 10 && LLM_PRICING[model]?.input > 5) {
            recommendations.push({
                type: 'cost_optimization',
                message: `Consider using a cheaper alternative to ${model}`,
                savings: `Potential savings: $${(cost * 0.5).toFixed(2)}`
            });
        }
    }

    // Check for local model availability
    if (metrics.totalCost > 50) {
        recommendations.push({
            type: 'local_model',
            message: 'Consider using local models (Ollama) for development',
            savings: `Potential savings: $${(metrics.totalCost * 0.8).toFixed(2)}`
        });
    }

    return recommendations;
}

function calculatePercentile(p) {
    const times = metrics.requestHistory.map(r => r.duration).sort((a, b) => a - b);
    if (times.length === 0) return 0;

    const index = Math.ceil((p / 100) * times.length) - 1;
    return times[index] || 0;
}

function identifyBottlenecks() {
    const bottlenecks = [];

    // Check response time
    if (metrics.avgResponseTime > 5000) {
        bottlenecks.push({
            type: 'slow_response',
            severity: 'high',
            message: 'Average response time exceeds 5 seconds',
            suggestion: 'Consider optimizing agent collaboration or using faster models'
        });
    }

    // Check error rate
    if (metrics.errorRate > 0.05) {
        bottlenecks.push({
            type: 'high_error_rate',
            severity: 'critical',
            message: `Error rate is ${(metrics.errorRate * 100).toFixed(1)}%`,
            suggestion: 'Review error logs and fix underlying issues'
        });
    }

    // Check active requests
    if (metrics.activeRequests > 10) {
        bottlenecks.push({
            type: 'high_concurrency',
            severity: 'medium',
            message: 'High number of concurrent requests',
            suggestion: 'Consider scaling horizontally or implementing request queuing'
        });
    }

    return bottlenecks;
}

function calculateThroughput() {
    const recentRequests = metrics.requestHistory.filter(
        r => Date.now() - r.timestamp < 60000
    );
    return recentRequests.length; // Requests per minute
}

// Simulate metrics updates (for demo)
setInterval(() => {
    // Simulate request
    if (Math.random() > 0.7) {
        const duration = 1000 + Math.random() * 4000;
        const tokens = Math.floor(500 + Math.random() * 2000);
        const model = ['llama3.2', 'gpt-3.5-turbo', 'claude-3-haiku'][Math.floor(Math.random() * 3)];

        const pricing = LLM_PRICING[model];
        const cost = (tokens / 1000000) * (pricing.input + pricing.output) / 2;

        metrics.totalRequests++;
        metrics.totalTokens += tokens;
        metrics.totalCost += cost;

        metrics.requestHistory.push({
            timestamp: Date.now(),
            duration,
            tokens,
            model,
            cost
        });

        // Keep only last 100 requests
        if (metrics.requestHistory.length > 100) {
            metrics.requestHistory.shift();
        }

        // Update model-specific metrics
        metrics.tokenUsageByModel[model] = (metrics.tokenUsageByModel[model] || 0) + tokens;
        metrics.costByModel[model] = (metrics.costByModel[model] || 0) + cost;

        // Update average response time
        const recentDurations = metrics.requestHistory.slice(-20).map(r => r.duration);
        metrics.avgResponseTime = recentDurations.reduce((a, b) => a + b, 0) / recentDurations.length;

        // Simulate errors
        if (Math.random() > 0.95) {
            metrics.errors.push({
                timestamp: Date.now(),
                message: 'Simulated error',
                type: 'timeout'
            });
            metrics.errorRate = metrics.errors.length / metrics.totalRequests;
        }
    }
}, 2000);

// Start server
server.listen(PORT, () => {
    console.log('=' .repeat(60));
    console.log('🚀 AgentMind Dashboard Server Starting...');
    console.log('=' .repeat(60));
    console.log(`📊 Dashboard: http://localhost:${PORT}`);
    console.log(`🔗 API URL: ${API_URL}`);
    console.log(`🔄 Refresh Interval: ${REFRESH_INTERVAL}ms`);
    console.log('=' .repeat(60));
});
