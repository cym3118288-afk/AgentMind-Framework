"""Code Review Team Example - Multi-agent code review and testing.

This example demonstrates a team of agents working together to review and test code:
- Reviewer: Analyzes code for bugs, style issues, and improvements
- Tester: Writes and executes test cases using code_executor
- Fixer: Implements fixes based on feedback

The team collaborates to improve code quality through automated testing.
"""

import asyncio
from agentmind.core import Agent, AgentMind, AgentConfig, Message, MessageRole
from agentmind.core.types import CollaborationStrategy
from agentmind.tools import CodeExecutor, Calculator, get_global_registry


# Sample buggy code to review
BUGGY_CODE = '''
def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

# Test cases
print("Average of [1, 2, 3, 4, 5]:", calculate_average([1, 2, 3, 4, 5]))
print("Average of [10, 20, 30]:", calculate_average([10, 20, 30]))
print("Average of []:", calculate_average([]))  # This will cause an error!
'''

FIXED_CODE = '''
def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0  # Handle empty list

    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

# Test cases
print("Average of [1, 2, 3, 4, 5]:", calculate_average([1, 2, 3, 4, 5]))
print("Average of [10, 20, 30]:", calculate_average([10, 20, 30]))
print("Average of []:", calculate_average([]))  # Now handles empty list
print("Average of [100]:", calculate_average([100]))
'''


async def main():
    """Run the code review team collaboration example."""

    print("=" * 60)
    print("Code Review Team Example - Automated Code Testing")
    print("=" * 60)
    print()

    # Register tools
    registry = get_global_registry()
    code_executor = CodeExecutor(timeout=5)
    calculator = Calculator()
    registry.register(code_executor)
    registry.register(calculator)

    # Create agent configurations
    reviewer_config = AgentConfig(
        name="reviewer",
        role="critic",
        backstory="Expert code reviewer who identifies bugs, security issues, and style problems.",
        temperature=0.5,
        max_tokens=400,
        tools=[]
    )

    tester_config = AgentConfig(
        name="tester",
        role="executor",
        backstory="QA engineer who writes and executes comprehensive test cases.",
        temperature=0.6,
        max_tokens=500,
        tools=["code_executor", "calculator"]
    )

    fixer_config = AgentConfig(
        name="fixer",
        role="assistant",
        backstory="Developer who implements fixes and improvements based on feedback.",
        temperature=0.7,
        max_tokens=500,
        tools=[]
    )

    # Create agents
    reviewer = Agent(name="reviewer", role="critic", config=reviewer_config)
    tester = Agent(name="tester", role="executor", config=tester_config)
    fixer = Agent(name="fixer", role="assistant", config=fixer_config)

    # Create AgentMind
    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN)
    mind.add_agent(reviewer)
    mind.add_agent(tester)
    mind.add_agent(fixer)

    print("\n[*] Team assembled:")
    print(f"    - {reviewer.name}: {reviewer.config.backstory}")
    print(f"    - {tester.name}: {tester.config.backstory}")
    print(f"    - {fixer.name}: {fixer.config.backstory}")
    print()

    # Display the buggy code
    print("[*] Code to Review:")
    print("-" * 60)
    print(BUGGY_CODE)
    print("-" * 60)
    print()

    # Phase 1: Code Review
    print("[Phase 1] Code Review")
    print("-" * 60)
    review_msg = Message(
        content=f"Review this code for bugs and issues:\n{BUGGY_CODE}",
        sender="system",
        role=MessageRole.SYSTEM
    )
    review_response = await reviewer.process_message(review_msg)
    print(f"{review_response.sender}: {review_response.content}")
    print()

    # Phase 2: Testing (Execute the buggy code)
    print("[Phase 2] Testing - Executing Buggy Code")
    print("-" * 60)
    test_msg = Message(
        content=f"Execute this code and report any errors:\n{BUGGY_CODE}",
        sender="system",
        role=MessageRole.SYSTEM
    )
    test_response = await tester.process_message(test_msg)
    print(f"{test_response.sender}: {test_response.content}")
    print()

    # Actually execute the buggy code
    print("[*] Tester uses code_executor tool on buggy code...")
    buggy_result = await code_executor.execute(code=BUGGY_CODE)
    print(f"[Tool Result] Success: {buggy_result.success}")
    if buggy_result.success:
        print(f"Output:\n{buggy_result.output}")
    else:
        print(f"Error:\n{buggy_result.error}")
    print()

    # Phase 3: Fix the code
    print("[Phase 3] Fixing Issues")
    print("-" * 60)
    fix_msg = Message(
        content=f"Fix the identified issues in the code. Original code:\n{BUGGY_CODE}",
        sender="system",
        role=MessageRole.SYSTEM
    )
    fix_response = await fixer.process_message(fix_msg)
    print(f"{fix_response.sender}: {fix_response.content}")
    print()

    # Display the fixed code
    print("[*] Fixed Code:")
    print("-" * 60)
    print(FIXED_CODE)
    print("-" * 60)
    print()

    # Phase 4: Test the fixed code
    print("[Phase 4] Testing - Executing Fixed Code")
    print("-" * 60)
    print("[*] Tester uses code_executor tool on fixed code...")
    fixed_result = await code_executor.execute(code=FIXED_CODE)
    print(f"[Tool Result] Success: {fixed_result.success}")
    if fixed_result.success:
        print(f"Output:\n{fixed_result.output}")
    else:
        print(f"Error:\n{fixed_result.error}")
    print()

    # Verify calculations with calculator tool
    print("[*] Verifying calculations with calculator tool...")
    calc_result = await calculator.execute(expression="(1+2+3+4+5)/5")
    print(f"[Calculator] (1+2+3+4+5)/5 = {calc_result.output}")
    calc_result2 = await calculator.execute(expression="(10+20+30)/3")
    print(f"[Calculator] (10+20+30)/3 = {calc_result2.output}")
    print()

    # Full collaboration
    print("\n" + "=" * 60)
    print("[*] Running full team collaboration...")
    print("=" * 60)
    print()

    result = await mind.start_collaboration(
        initial_message="Review, test, and fix the calculate_average function that has a division by zero bug.",
        max_rounds=3,
        use_llm=False
    )

    print()
    print("[*] Collaboration Results:")
    print(f"    - Success: {result.success}")
    print(f"    - Total Rounds: {result.total_rounds}")
    print(f"    - Total Messages: {result.total_messages}")
    print(f"    - Agent Contributions: {result.agent_contributions}")
    print()

    # Save session
    print("[*] Saving session...")
    session_path = mind.save_session("code_review_demo")
    print(f"    Session saved to: {session_path}")
    print()

    # Display final output
    print("=" * 60)
    print("Final Output")
    print("=" * 60)
    print(result.final_output)
    print()

    # Demonstrate more code executor capabilities
    print("=" * 60)
    print("[*] Additional Code Executor Tests")
    print("=" * 60)
    print()

    # Test 1: Simple calculation
    print("[Test 1] Simple calculation:")
    test1 = await code_executor.execute(code="print(2 ** 10)")
    print(f"Result: {test1.output.strip() if test1.success else test1.error}")
    print()

    # Test 2: List operations
    print("[Test 2] List operations:")
    test2 = await code_executor.execute(code="""
numbers = [1, 2, 3, 4, 5]
squared = [n**2 for n in numbers]
print(f"Original: {numbers}")
print(f"Squared: {squared}")
""")
    print(f"Result:\n{test2.output if test2.success else test2.error}")
    print()

    # Test 3: Timeout test (commented out to avoid delay)
    # print("[Test 3] Timeout test (infinite loop):")
    # test3 = await code_executor.execute(code="while True: pass", timeout=2)
    # print(f"Result: {test3.error}")
    # print()

    print("=" * 60)
    print("Code Review Team Example Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
