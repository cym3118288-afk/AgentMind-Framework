"""
AgentMind Quick Demo - Showcase Core Features
This script demonstrates AgentMind's main features: creating agents, collaboration, and output
"""

import asyncio
import sys
import io

# Fix Windows console encoding issues
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from agentmind.core import Agent, AgentMind, Message, MessageRole
from agentmind.core.types import CollaborationStrategy


class SimpleMockLLM:
    """简单的模拟 LLM，用于演示（无需真实 API）"""

    def __init__(self, model="demo-model"):
        self.model = model

    async def generate(self, messages, temperature=None, max_tokens=None, **kwargs):
        """生成模拟响应"""
        from agentmind.llm.provider import LLMResponse

        # 提取用户消息
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")

        # 根据角色生成不同的响应
        if "researcher" in system_msg.lower() or "research" in system_msg.lower():
            response = f"研究发现：关于'{user_msg}'，我发现了三个关键点：1) 技术趋势正在快速发展 2) 市场需求持续增长 3) 创新机会丰富"
        elif "writer" in system_msg.lower() or "creative" in system_msg.lower():
            response = f"创意内容：让我为'{user_msg}'创作一段引人入胜的内容。这个主题充满了可能性，我们可以从独特的角度来呈现它，让读者产生共鸣。"
        elif "analyst" in system_msg.lower():
            response = f"分析结果：针对'{user_msg}'，数据显示积极趋势。关键指标表现良好，建议继续推进。"
        else:
            response = f"我理解了'{user_msg}'，这是一个很好的话题。让我分享我的见解..."

        return LLMResponse(
            content=response,
            model=self.model,
            usage={"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
            metadata={}
        )

    async def generate_stream(self, messages, **kwargs):
        """流式生成（演示用）"""
        yield "Demo response"


async def demo_basic_collaboration():
    """演示 1: 基础协作 - 两个 agents 讨论一个话题"""
    print("\n" + "="*70)
    print("演示 1: 基础多 Agent 协作")
    print("="*70)

    # 创建模拟 LLM
    llm = SimpleMockLLM()

    # 初始化 AgentMind
    mind = AgentMind(
        strategy=CollaborationStrategy.BROADCAST,
        llm_provider=llm
    )

    # 创建专业化的 agents
    researcher = Agent(
        name="研究员",
        role="researcher",
        llm_provider=llm
    )
    researcher.config.system_prompt = "你是一个专业的研究员，擅长收集和分析信息。"

    writer = Agent(
        name="作家",
        role="creative",
        llm_provider=llm
    )
    writer.config.system_prompt = "你是一个富有创意的作家，擅长将信息转化为引人入胜的内容。"

    # 添加 agents 到系统
    mind.add_agent(researcher)
    mind.add_agent(writer)

    # 开始协作
    print("\n任务: 创作一篇关于人工智能未来的文章\n")
    result = await mind.start_collaboration(
        "创作一篇关于人工智能未来的文章",
        max_rounds=2,
        use_llm=True
    )

    # 显示结果
    print("\n" + "-"*70)
    print("协作结果:")
    print("-"*70)
    print(f"成功: {result.success}")
    print(f"轮次: {result.total_rounds}")
    print(f"消息数: {result.total_messages}")
    print(f"\n最终输出:\n{result.final_output}")

    # 显示每个 agent 的贡献
    print("\n" + "-"*70)
    print("Agent 贡献统计:")
    print("-"*70)
    for agent_name, count in result.agent_contributions.items():
        print(f"  {agent_name}: {count} 条消息")

    return mind


async def demo_hierarchical_team():
    """演示 2: 层级协作 - 主管协调多个专家"""
    print("\n" + "="*70)
    print("演示 2: 层级团队协作")
    print("="*70)

    llm = SimpleMockLLM()

    # 使用层级策略
    mind = AgentMind(
        strategy=CollaborationStrategy.HIERARCHICAL,
        llm_provider=llm
    )

    # 创建主管
    supervisor = Agent(
        name="项目主管",
        role="supervisor",
        llm_provider=llm
    )
    supervisor.config.system_prompt = "你是项目主管，负责协调团队并综合各方意见。"

    # 创建专家团队
    analyst = Agent(
        name="数据分析师",
        role="analyst",
        llm_provider=llm
    )
    analyst.config.system_prompt = "你是数据分析专家，提供基于数据的洞察。"

    creative = Agent(
        name="创意总监",
        role="creative",
        llm_provider=llm
    )
    creative.config.system_prompt = "你是创意专家，提供创新的想法和方案。"

    # 添加到系统
    mind.add_agent(supervisor)
    mind.add_agent(analyst)
    mind.add_agent(creative)

    print("\n任务: 设计一个新产品的营销策略\n")
    result = await mind.start_collaboration(
        "设计一个新产品的营销策略",
        max_rounds=1,
        use_llm=True
    )

    print("\n" + "-"*70)
    print("层级协作结果:")
    print("-"*70)
    print(f"成功: {result.success}")
    print(f"\n{result.final_output}")

    return mind


async def demo_agent_memory():
    """演示 3: Agent 记忆功能"""
    print("\n" + "="*70)
    print("演示 3: Agent 记忆与上下文")
    print("="*70)

    llm = SimpleMockLLM()

    agent = Agent(
        name="助手",
        role="assistant",
        llm_provider=llm
    )
    agent.config.system_prompt = "你是一个有记忆的智能助手。"

    # 发送多条消息，测试记忆
    messages = [
        "我叫张三，我在研究机器学习",
        "你还记得我的名字吗？",
        "我在研究什么？"
    ]

    print("\n对话序列:")
    for i, msg_content in enumerate(messages, 1):
        msg = Message(content=msg_content, sender="用户", role=MessageRole.USER)
        response = await agent.think_and_respond(msg)

        print(f"\n[轮次 {i}]")
        print(f"用户: {msg_content}")
        print(f"助手: {response.content}")

    # 显示记忆统计
    print("\n" + "-"*70)
    print("记忆统计:")
    print("-"*70)
    print(f"总消息数: {len(agent.memory)}")
    print(f"记忆摘要: {agent.get_memory_summary()}")

    # 显示最近的记忆
    print("\n最近的 4 条记忆:")
    recent = agent.get_recent_memory(limit=4)
    for msg in recent:
        print(f"  {msg.sender}: {msg.content[:50]}...")


async def demo_system_metrics():
    """演示 4: 系统指标和监控"""
    print("\n" + "="*70)
    print("演示 4: 系统指标与监控")
    print("="*70)

    llm = SimpleMockLLM()
    mind = AgentMind(llm_provider=llm)

    # 添加多个 agents
    for i in range(3):
        agent = Agent(
            name=f"Agent-{i+1}",
            role="assistant",
            llm_provider=llm
        )
        mind.add_agent(agent)

    # 执行几次协作
    print("\n执行多次协作任务...\n")
    tasks = [
        "分析市场趋势",
        "设计用户界面",
        "优化系统性能"
    ]

    for task in tasks:
        print(f"任务: {task}")
        await mind.start_collaboration(task, max_rounds=1, use_llm=True)

    # 获取系统指标
    metrics = mind.get_real_time_metrics()

    print("\n" + "-"*70)
    print("系统实时指标:")
    print("-"*70)
    print(f"Agents 总数: {metrics['agents']['total']}")
    print(f"活跃 Agents: {metrics['agents']['active']}")
    print(f"协作总数: {metrics['collaboration']['total']}")
    print(f"成功协作: {metrics['collaboration']['successful']}")
    print(f"成功率: {metrics['collaboration']['success_rate']:.1%}")
    print(f"总消息数: {metrics['messages']['total']}")

    # 获取对话摘要
    summary = mind.get_conversation_summary()
    print("\n对话摘要:")
    print(f"  总消息: {summary['total_messages']}")
    print(f"  活跃 agents: {summary['active_agents']}/{summary['total_agents']}")


async def main():
    """运行所有演示"""
    print("\n")
    print("=" * 70)
    print(" " * 20 + "AgentMind 快速演示")
    print(" " * 15 + "多 Agent 协作框架核心功能展示")
    print("=" * 70)

    try:
        # 运行所有演示
        await demo_basic_collaboration()
        await demo_hierarchical_team()
        await demo_agent_memory()
        await demo_system_metrics()

        print("\n" + "="*70)
        print("演示完成！")
        print("="*70)
        print("\n关键特性总结:")
        print("  * 多 Agent 协作 - 不同角色的 agents 协同工作")
        print("  * 灵活策略 - 支持广播、轮询、层级等多种协作模式")
        print("  * 智能记忆 - Agents 记住对话历史和上下文")
        print("  * 实时监控 - 完整的系统指标和性能追踪")
        print("  * 轻量高效 - 核心框架 <500 行代码")
        print("\n开始使用:")
        print("  1. pip install agentmind")
        print("  2. 配置 LLM provider (Ollama/OpenAI/Anthropic)")
        print("  3. 创建 agents 并开始协作！")
        print("\n文档: https://github.com/cym3118288-afk/AgentMind")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
