"""
Real-world Use Case: Code Review Automation

This example demonstrates an automated code review system using AgentMind.
Multiple specialized agents collaborate to review code for:
- Code quality and best practices
- Security vulnerabilities
- Performance issues
- Documentation completeness
- Test coverage

Features:
- Multi-agent code analysis
- Automated issue detection
- Prioritized recommendations
- Detailed review reports
"""

import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeIssue:
    """Represents a code review issue"""

    severity: IssueSeverity
    category: str
    line_number: Optional[int]
    description: str
    suggestion: str


@dataclass
class CodeReview:
    """Represents a complete code review"""

    file_path: str
    language: str
    issues: List[CodeIssue]
    overall_score: int  # 0-100
    summary: str
    recommendations: List[str]


class StaticAnalysisTool(Tool):
    """Simulates static code analysis"""

    def __init__(self):
        super().__init__(
            name="static_analysis",
            description="Run static analysis to detect code issues",
            parameters={"code": {"type": "string", "description": "Code to analyze"}},
        )

    async def execute(self, code: str) -> str:
        """Perform basic static analysis"""
        issues = []

        # Check for common issues
        if "eval(" in code:
            issues.append("CRITICAL: Use of eval() detected - security risk")
        if "TODO" in code or "FIXME" in code:
            issues.append("INFO: TODO/FIXME comments found")
        if code.count("\n") > 100:
            issues.append("MEDIUM: Function too long (>100 lines)")
        if "except:" in code or "except Exception:" in code:
            issues.append("MEDIUM: Bare except clause - catch specific exceptions")
        if "print(" in code:
            issues.append("LOW: Print statement found - use logging instead")

        if issues:
            return "Static analysis issues:\n" + "\n".join(f"- {issue}" for issue in issues)
        return "No static analysis issues found."


class SecurityScanTool(Tool):
    """Simulates security vulnerability scanning"""

    def __init__(self):
        super().__init__(
            name="security_scan",
            description="Scan code for security vulnerabilities",
            parameters={"code": {"type": "string", "description": "Code to scan"}},
        )

    async def execute(self, code: str) -> str:
        """Perform security scan"""
        vulnerabilities = []

        # Check for security issues
        if "password" in code.lower() and "=" in code:
            vulnerabilities.append("CRITICAL: Hardcoded password detected")
        if "sql" in code.lower() and "+" in code:
            vulnerabilities.append("HIGH: Potential SQL injection vulnerability")
        if "os.system" in code or "subprocess.call" in code:
            vulnerabilities.append("HIGH: Command injection risk")
        if "pickle.loads" in code:
            vulnerabilities.append("HIGH: Unsafe deserialization")
        if "random.random" in code and "password" in code.lower():
            vulnerabilities.append("MEDIUM: Weak random number generator for security")

        if vulnerabilities:
            return "Security vulnerabilities:\n" + "\n".join(
                f"- {vuln}" for vuln in vulnerabilities
            )
        return "No security vulnerabilities detected."


class ComplexityAnalysisTool(Tool):
    """Analyzes code complexity"""

    def __init__(self):
        super().__init__(
            name="complexity_analysis",
            description="Analyze code complexity and maintainability",
            parameters={"code": {"type": "string", "description": "Code to analyze"}},
        )

    async def execute(self, code: str) -> str:
        """Analyze complexity"""
        metrics = []

        # Simple complexity metrics
        lines = code.split("\n")
        num_lines = len(lines)
        num_functions = code.count("def ")
        num_classes = code.count("class ")
        nesting_level = max(len(line) - len(line.lstrip()) for line in lines) // 4

        metrics.append(f"Lines of code: {num_lines}")
        metrics.append(f"Functions: {num_functions}")
        metrics.append(f"Classes: {num_classes}")
        metrics.append(f"Max nesting level: {nesting_level}")

        if nesting_level > 4:
            metrics.append("WARNING: High nesting level - consider refactoring")
        if num_lines > 200:
            metrics.append("WARNING: File too large - consider splitting")

        return "Complexity metrics:\n" + "\n".join(metrics)


async def create_code_review_system() -> AgentMind:
    """Create the code review multi-agent system"""

    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)

    # Create tools
    static_tool = StaticAnalysisTool()
    security_tool = SecurityScanTool()
    complexity_tool = ComplexityAnalysisTool()

    # 1. Static Analysis Agent
    static_agent = Agent(
        name="Static_Analyzer",
        role="static_analysis_specialist",
        system_prompt="""You are a static code analysis expert. Your job is to:
        1. Run static analysis tools
        2. Identify code quality issues
        3. Check for best practice violations
        4. Report findings clearly

        Focus on code quality, maintainability, and adherence to standards.""",
        tools=[static_tool],
    )

    # 2. Security Reviewer
    security_agent = Agent(
        name="Security_Reviewer",
        role="security_specialist",
        system_prompt="""You are a security expert. Your job is to:
        1. Scan for security vulnerabilities
        2. Identify potential attack vectors
        3. Check for secure coding practices
        4. Prioritize security issues

        Focus on preventing security breaches and protecting user data.""",
        tools=[security_tool],
    )

    # 3. Performance Analyst
    performance_agent = Agent(
        name="Performance_Analyst",
        role="performance_specialist",
        system_prompt="""You are a performance optimization expert. Your job is to:
        1. Identify performance bottlenecks
        2. Suggest optimization opportunities
        3. Check algorithmic complexity
        4. Review resource usage

        Focus on efficiency, scalability, and resource optimization.""",
        tools=[complexity_tool],
    )

    # 4. Documentation Reviewer
    docs_agent = Agent(
        name="Docs_Reviewer",
        role="documentation_specialist",
        system_prompt="""You are a documentation expert. Your job is to:
        1. Check for missing docstrings
        2. Verify documentation completeness
        3. Assess code readability
        4. Suggest documentation improvements

        Focus on making code understandable and maintainable.""",
    )

    # 5. Review Synthesizer
    synthesizer = Agent(
        name="Review_Synthesizer",
        role="review_coordinator",
        system_prompt="""You are a senior code reviewer. Your job is to:
        1. Synthesize findings from all reviewers
        2. Prioritize issues by severity
        3. Create actionable recommendations
        4. Generate comprehensive review summary

        Provide clear, constructive feedback that helps developers improve.""",
    )

    mind.add_agent(static_agent)
    mind.add_agent(security_agent)
    mind.add_agent(performance_agent)
    mind.add_agent(docs_agent)
    mind.add_agent(synthesizer)

    return mind


async def review_code(mind: AgentMind, file_path: str, code: str, language: str) -> CodeReview:
    """Review code using the multi-agent system"""

    print(f"\n{'='*60}")
    print(f"Reviewing: {file_path}")
    print(f"Language: {language}")
    print(f"Lines: {len(code.split(chr(10)))}")
    print(f"{'='*60}\n")

    # Create review context
    context = f"""
    Please review this {language} code:

    File: {file_path}

    Code:
    ```{language}
    {code}
    ```

    Perform comprehensive review covering:
    1. Static analysis and code quality
    2. Security vulnerabilities
    3. Performance and complexity
    4. Documentation completeness
    5. Overall assessment and recommendations
    """

    # Collaborate to review code
    result = await mind.collaborate(context, max_rounds=5)

    print(f"\n{'='*60}")
    print(f"Review Complete: {file_path}")
    print(f"\nReview Summary:\n{result}")
    print(f"{'='*60}\n")

    # Create review object (simplified)
    review = CodeReview(
        file_path=file_path,
        language=language,
        issues=[],
        overall_score=75,  # Would be calculated from actual analysis
        summary=result,
        recommendations=[],
    )

    return review


async def example_python_function():
    """Example 1: Review a Python function"""
    print("\n=== Example 1: Python Function Review ===\n")

    mind = await create_code_review_system()

    code = """
def process_user_data(user_input):
    # TODO: Add input validation
    password = "admin123"  # Hardcoded password

    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    result = eval(query)

    print("Processing:", user_input)

    return result
"""

    await review_code(mind, "user_processor.py", code, "python")


async def example_secure_code():
    """Example 2: Review secure, well-written code"""
    print("\n=== Example 2: Well-Written Code Review ===\n")

    mind = await create_code_review_system()

    code = """
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def calculate_discount(price: float, discount_percent: float) -> float:
    \"\"\"
    Calculate discounted price.

    Args:
        price: Original price
        discount_percent: Discount percentage (0-100)

    Returns:
        Discounted price

    Raises:
        ValueError: If inputs are invalid
    \"\"\"
    if price < 0:
        raise ValueError("Price cannot be negative")
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")

    discount_amount = price * (discount_percent / 100)
    final_price = price - discount_amount

    logger.info(f"Applied {discount_percent}% discount to ${price}")

    return final_price
"""

    await review_code(mind, "pricing.py", code, "python")


async def example_complex_code():
    """Example 3: Review complex code with multiple issues"""
    print("\n=== Example 3: Complex Code Review ===\n")

    mind = await create_code_review_system()

    code = """
def process_data(data):
    result = []
    for item in data:
        if item:
            if item['type'] == 'A':
                if item['status'] == 'active':
                    if item['value'] > 0:
                        if item['verified']:
                            result.append(item)

    # Process results
    for r in result:
        try:
            value = r['value']
            processed = value * 2
            r['processed'] = processed
        except:
            pass

    return result
"""

    await review_code(mind, "data_processor.py", code, "python")


async def example_api_endpoint():
    """Example 4: Review API endpoint code"""
    print("\n=== Example 4: API Endpoint Review ===\n")

    mind = await create_code_review_system()

    code = """
from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/execute')
def execute_command():
    cmd = request.args.get('cmd')
    result = os.system(cmd)
    return {'result': result}

@app.route('/user/<user_id>')
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    # Execute query...
    return {'user': 'data'}
"""

    await review_code(mind, "api.py", code, "python")


async def example_batch_review():
    """Example 5: Batch review multiple files"""
    print("\n=== Example 5: Batch Code Review ===\n")

    mind = await create_code_review_system()

    files = [
        ("utils.py", "def helper(x): return x * 2"),
        ("config.py", "API_KEY = 'secret123'\nDEBUG = True"),
        ("main.py", "import utils\nprint(utils.helper(5))"),
    ]

    print(f"Reviewing {len(files)} files in batch...\n")

    reviews = []
    for file_path, code in files:
        review = await review_code(mind, file_path, code, "python")
        reviews.append(review)

    print(f"\nBatch review complete! Reviewed {len(reviews)} files.")


async def main():
    """Run all code review examples"""
    print("=" * 60)
    print("Code Review Automation with AgentMind")
    print("=" * 60)

    await example_python_function()
    await example_secure_code()
    await example_complex_code()
    await example_api_endpoint()
    await example_batch_review()

    print("\n" + "=" * 60)
    print("Code review examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
