# AgentMind Chat - Quick Start Guide

## 快速开始指南 (Quick Start Guide)

### 方法 1: 使用启动脚本 (Method 1: Using Startup Script)

**Windows 用户:**
1. 双击运行 `start_chat.bat`
2. 等待安装完成
3. 浏览器自动打开 http://localhost:5000

**Mac/Linux 用户:**
```bash
chmod +x start_chat.sh
./start_chat.sh
```

### 方法 2: 手动启动 (Method 2: Manual Start)

1. **安装依赖 (Install Dependencies):**
```bash
pip install -r requirements.txt
pip install -e .
```

2. **启动服务器 (Start Server):**
```bash
python chat_server.py
```

3. **打开浏览器 (Open Browser):**
访问 http://localhost:5000

## 使用说明 (Usage Instructions)

### 基本操作 (Basic Operations)

1. **设置用户名 (Set Username)**
   - 在左侧边栏底部输入你的名字
   - 默认名称是 "User"

2. **发送消息 (Send Messages)**
   - 在底部输入框输入消息
   - 按 Enter 发送
   - Shift + Enter 换行

3. **使用表情 (Use Emojis)**
   - 点击输入框左侧的笑脸按钮
   - 选择你想要的表情
   - 表情会插入到光标位置

4. **管理 Agent (Manage Agents)**
   - 左侧显示所有可用的 Agent
   - 点击 Agent 可以启用/禁用
   - 绿点表示活跃，红点表示禁用

### 系统中的 Agent (Agents in System)

系统包含 12 个不同角色的 Agent：

- 🔍 **Alice** - 分析师 (Analyst)
- 🎨 **Bob** - 创意专家 (Creative)
- 📋 **Charlie** - 协调员 (Coordinator)
- 💻 **Diana** - 技术专家 (Technical)
- 📚 **Eve** - 研究员 (Researcher)
- ♟️ **Frank** - 策略师 (Strategist)
- ✨ **Grace** - 设计师 (Designer)
- ⚙️ **Henry** - 开发者 (Developer)
- 📢 **Iris** - 营销专家 (Marketer)
- 🤔 **Jack** - 哲学家 (Philosopher)
- 🔬 **Kate** - 科学家 (Scientist)
- 💡 **Leo** - 企业家 (Entrepreneur)

### 功能特点 (Features)

✅ 实时聊天 (Real-time chat)
✅ 多 Agent 同时响应 (Multiple agents respond simultaneously)
✅ 表情支持 (Emoji support)
✅ 现代化界面 (Modern UI)
✅ 响应式设计 (Responsive design)
✅ Agent 开关控制 (Agent toggle control)

## 常见问题 (FAQ)

**Q: 端口被占用怎么办？**
A: 编辑 `chat_server.py`，修改最后一行的端口号：
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5001)
```

**Q: Agent 不响应？**
A: 检查左侧 Agent 列表，确保 Agent 是活跃状态（绿点）

**Q: 如何添加更多 Agent？**
A: 编辑 `chat_server.py` 中的 `agent_configs` 列表

**Q: 可以保存聊天记录吗？**
A: 当前版本不支持，但可以在未来版本中添加

## 技术支持 (Technical Support)

如遇到问题，请检查：
1. Python 版本 >= 3.7
2. 所有依赖已正确安装
3. 端口 5000 未被占用
4. 防火墙未阻止连接

## 项目结构 (Project Structure)

```
agentmind-fresh/
├── chat_server.py          # 主服务器
├── templates/
│   └── chat.html          # 聊天界面
├── static/
│   ├── css/
│   │   └── chat.css       # 样式文件
│   └── js/
│       └── chat.js        # 前端逻辑
├── src/agentmind/         # AgentMind 框架
├── requirements.txt       # 依赖列表
├── start_chat.bat        # Windows 启动脚本
└── start_chat.sh         # Mac/Linux 启动脚本
```

## 下一步 (Next Steps)

- 尝试与不同的 Agent 对话
- 测试表情功能
- 启用/禁用不同的 Agent 观察效果
- 自定义 Agent 的响应行为

享受与 AI Agent 的对话！🚀
