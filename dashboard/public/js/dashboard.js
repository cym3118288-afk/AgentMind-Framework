// AgentMind Dashboard Client-Side JavaScript

const socket = io();

// Chart instances
let tokenChart, costChart, performanceChart;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    connectWebSocket();
    loadPricingTable();
});

// Initialize charts
function initializeCharts() {
    // Token usage chart
    const tokenCtx = document.getElementById('token-chart').getContext('2d');
    tokenChart = new Chart(tokenCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Cost chart
    const costCtx = document.getElementById('cost-chart').getContext('2d');
    costChart = new Chart(costCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Cost (USD)',
                data: [],
                backgroundColor: '#10b981'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => '$' + value.toFixed(2)
                    }
                }
            }
        }
    });

    // Performance chart
    const perfCtx = document.getElementById('performance-chart').getContext('2d');
    performanceChart = new Chart(perfCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Response Time (ms)',
                data: [],
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Connect to WebSocket
function connectWebSocket() {
    socket.on('connect', () => {
        console.log('Connected to dashboard server');
        document.getElementById('status').style.color = '#10b981';
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from dashboard server');
        document.getElementById('status').style.color = '#ef4444';
    });

    socket.on('metrics', (metrics) => {
        updateDashboard(metrics);
    });
}

// Update dashboard with new metrics
function updateDashboard(metrics) {
    // Update header stats
    document.getElementById('total-requests').textContent = metrics.totalRequests.toLocaleString();
    document.getElementById('active-sessions').textContent = metrics.activeRequests;

    // Update token usage
    document.getElementById('total-tokens').textContent = metrics.totalTokens.toLocaleString();
    updateTokenChart(metrics.tokenUsageByModel);
    updateTokenBreakdown(metrics.tokenUsageByModel);

    // Update cost tracking
    document.getElementById('total-cost').textContent = '$' + metrics.totalCost.toFixed(2);
    updateCostChart(metrics.costByModel);
    updateCostBreakdown(metrics.costByModel);

    // Update performance metrics
    document.getElementById('avg-response').textContent = Math.round(metrics.avgResponseTime) + 'ms';
    updatePerformanceChart(metrics.requestHistory);

    // Fetch and update additional metrics
    fetchPerformanceMetrics();
    fetchBottlenecks();
    fetchRecommendations();
}

// Update token chart
function updateTokenChart(tokenUsageByModel) {
    const labels = Object.keys(tokenUsageByModel);
    const data = Object.values(tokenUsageByModel);

    tokenChart.data.labels = labels;
    tokenChart.data.datasets[0].data = data;
    tokenChart.update();
}

// Update token breakdown
function updateTokenBreakdown(tokenUsageByModel) {
    const container = document.getElementById('token-breakdown');
    container.innerHTML = '';

    for (const [model, tokens] of Object.entries(tokenUsageByModel)) {
        const item = document.createElement('div');
        item.className = 'breakdown-item';
        item.innerHTML = `
            <span class="breakdown-label">${model}</span>
            <span class="breakdown-value">${tokens.toLocaleString()}</span>
        `;
        container.appendChild(item);
    }
}

// Update cost chart
function updateCostChart(costByModel) {
    const labels = Object.keys(costByModel);
    const data = Object.values(costByModel);

    costChart.data.labels = labels;
    costChart.data.datasets[0].data = data;
    costChart.update();
}

// Update cost breakdown
function updateCostBreakdown(costByModel) {
    const container = document.getElementById('cost-breakdown');
    container.innerHTML = '';

    for (const [model, cost] of Object.entries(costByModel)) {
        const item = document.createElement('div');
        item.className = 'breakdown-item';
        item.innerHTML = `
            <span class="breakdown-label">${model}</span>
            <span class="breakdown-value">$${cost.toFixed(4)}</span>
        `;
        container.appendChild(item);
    }
}

// Update performance chart
function updatePerformanceChart(requestHistory) {
    const recent = requestHistory.slice(-20);
    const labels = recent.map((_, i) => i + 1);
    const data = recent.map(r => r.duration);

    performanceChart.data.labels = labels;
    performanceChart.data.datasets[0].data = data;
    performanceChart.update();
}

// Fetch performance metrics
async function fetchPerformanceMetrics() {
    try {
        const response = await fetch('/api/performance');
        const data = await response.json();

        document.getElementById('p95').textContent = Math.round(data.p95) + 'ms';
        document.getElementById('p99').textContent = Math.round(data.p99) + 'ms';
        document.getElementById('throughput').textContent = data.throughput + '/min';
    } catch (err) {
        console.error('Error fetching performance metrics:', err);
    }
}

// Fetch bottlenecks
async function fetchBottlenecks() {
    try {
        const response = await fetch('/api/performance');
        const data = await response.json();

        const container = document.getElementById('bottlenecks-list');
        container.innerHTML = '';

        if (data.bottlenecks.length === 0) {
            container.innerHTML = '<div class="no-bottlenecks">✓ No bottlenecks detected</div>';
            return;
        }

        for (const bottleneck of data.bottlenecks) {
            const item = document.createElement('div');
            item.className = `bottleneck-item ${bottleneck.severity}`;
            item.innerHTML = `
                <div class="bottleneck-type">${bottleneck.type.replace(/_/g, ' ')}</div>
                <div class="bottleneck-message">${bottleneck.message}</div>
                <div class="bottleneck-suggestion">💡 ${bottleneck.suggestion}</div>
            `;
            container.appendChild(item);
        }
    } catch (err) {
        console.error('Error fetching bottlenecks:', err);
    }
}

// Fetch recommendations
async function fetchRecommendations() {
    try {
        const response = await fetch('/api/cost-analysis');
        const data = await response.json();

        const container = document.getElementById('recommendations-list');
        container.innerHTML = '';

        if (data.recommendations.length === 0) {
            container.innerHTML = '<div class="no-recommendations">✓ No recommendations at this time</div>';
            return;
        }

        for (const rec of data.recommendations) {
            const item = document.createElement('div');
            item.className = 'recommendation-item';
            item.innerHTML = `
                <div class="recommendation-message">${rec.message}</div>
                <div class="recommendation-savings">${rec.savings}</div>
            `;
            container.appendChild(item);
        }
    } catch (err) {
        console.error('Error fetching recommendations:', err);
    }
}

// Load pricing table
async function loadPricingTable() {
    try {
        const response = await fetch('/api/metrics');
        const data = await response.json();

        const container = document.getElementById('pricing-table');
        container.innerHTML = '';

        // Header
        const header = document.createElement('div');
        header.className = 'pricing-row';
        header.innerHTML = `
            <div>Model</div>
            <div>Provider</div>
            <div style="text-align: right">Input ($/1M)</div>
            <div style="text-align: right">Output ($/1M)</div>
        `;
        container.appendChild(header);

        // Rows
        for (const [model, pricing] of Object.entries(data.pricing)) {
            const row = document.createElement('div');
            row.className = 'pricing-row';
            row.innerHTML = `
                <div class="pricing-model">${model}</div>
                <div class="pricing-provider">${pricing.provider}</div>
                <div class="pricing-cost">$${pricing.input.toFixed(2)}</div>
                <div class="pricing-cost">$${pricing.output.toFixed(2)}</div>
            `;
            container.appendChild(row);
        }
    } catch (err) {
        console.error('Error loading pricing table:', err);
    }
}

// Refresh data every 5 seconds
setInterval(() => {
    fetchPerformanceMetrics();
    fetchBottlenecks();
    fetchRecommendations();
}, 5000);
