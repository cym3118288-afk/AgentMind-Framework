// Initialize Socket.IO connection
const socket = io();

// DOM Elements
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const agentList = document.getElementById('agentList');
const agentCount = document.getElementById('agentCount');
const usernameInput = document.getElementById('usernameInput');
const emojiBtn = document.getElementById('emojiBtn');
const emojiPicker = document.getElementById('emojiPicker');

// State
let agents = [];
let username = 'User';

// Socket Event Handlers
socket.on('connect', () => {
    console.log('Connected to server');
    addSystemMessage('Connected to AgentMind Chat Server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    addSystemMessage('Disconnected from server');
});

socket.on('agent_list', (data) => {
    agents = data.agents;
    renderAgentList();
});

socket.on('system_message', (data) => {
    addSystemMessage(data.content, data.timestamp);
});

socket.on('new_message', (data) => {
    addMessage(data);
});

socket.on('agent_toggled', (data) => {
    const agent = agents.find(a => a.name === data.agent_name);
    if (agent) {
        agent.is_active = data.is_active;
        renderAgentList();
    }
});

// Render Functions
function renderAgentList() {
    agentList.innerHTML = '';
    agentCount.textContent = agents.length;

    agents.forEach(agent => {
        const agentItem = document.createElement('div');
        agentItem.className = `agent-item ${agent.is_active ? '' : 'inactive'}`;
        agentItem.onclick = () => toggleAgent(agent.name);

        agentItem.innerHTML = `
            <div class="agent-emoji">${agent.emoji}</div>
            <div class="agent-info">
                <div class="agent-name">${agent.name}</div>
                <div class="agent-role">${agent.role}</div>
            </div>
            <div class="agent-status ${agent.is_active ? '' : 'inactive'}"></div>
        `;

        agentList.appendChild(agentItem);
    });
}

function addMessage(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${data.type}`;

    const timestamp = data.timestamp || getCurrentTime();
    const emoji = data.emoji || '🤖';
    const role = data.role || '';

    messageDiv.innerHTML = `
        <div class="message-avatar">${emoji}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${data.sender}</span>
                ${role ? `<span class="message-role">${role}</span>` : ''}
                <span class="message-timestamp">${timestamp}</span>
            </div>
            <div class="message-text">${escapeHtml(data.content)}</div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function addSystemMessage(content, timestamp) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';

    messageDiv.innerHTML = `
        <div class="message-avatar">ℹ️</div>
        <div class="message-content">
            <div class="message-text">${escapeHtml(content)}</div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Message Sending
function sendMessage() {
    const content = messageInput.value.trim();
    if (!content) return;

    username = usernameInput.value.trim() || 'User';

    socket.emit('user_message', {
        content: content,
        username: username
    });

    messageInput.value = '';
    autoResizeTextarea();
}

// Agent Toggle
function toggleAgent(agentName) {
    socket.emit('toggle_agent', { agent_name: agentName });
}

// Emoji Picker
emojiBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    emojiPicker.classList.toggle('active');
});

document.addEventListener('click', (e) => {
    if (!emojiPicker.contains(e.target) && e.target !== emojiBtn) {
        emojiPicker.classList.remove('active');
    }
});

document.querySelectorAll('.emoji-item').forEach(item => {
    item.addEventListener('click', () => {
        const emoji = item.textContent;
        const cursorPos = messageInput.selectionStart;
        const textBefore = messageInput.value.substring(0, cursorPos);
        const textAfter = messageInput.value.substring(cursorPos);

        messageInput.value = textBefore + emoji + textAfter;
        messageInput.focus();
        messageInput.selectionStart = messageInput.selectionEnd = cursorPos + emoji.length;

        emojiPicker.classList.remove('active');
        autoResizeTextarea();
    });
});

// Input Handlers
sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

messageInput.addEventListener('input', autoResizeTextarea);

usernameInput.addEventListener('change', () => {
    username = usernameInput.value.trim() || 'User';
});

// Auto-resize textarea
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

// Utility Functions
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
autoResizeTextarea();
messageInput.focus();
