"""
Tutorial 06: Production Deployment

This tutorial covers production best practices:
- Error handling and recovery
- Logging and monitoring
- Performance optimization
- Security considerations
- Scaling strategies
- Testing and validation

Estimated time: 35 minutes
Difficulty: Advanced
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Example 1: Error Handling
class ResilientAgent(Agent):
    """Agent with enhanced error handling"""

    def __init__(self, *args, max_retries: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
        self.error_count = 0

    async def process_message_with_retry(self, message):
        """Process message with retry logic"""
        for attempt in range(self.max_retries):
            try:
                return await self.process_message(message)
            except Exception as e:
                self.error_count += 1
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")

                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Max retries reached")
                    raise


# Example 2: Performance Monitoring
class MonitoredAgent(Agent):
    """Agent with performance monitoring"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = {
            "total_messages": 0,
            "total_time": 0.0,
            "avg_response_time": 0.0,
            "errors": 0,
        }

    async def process_message(self, message):
        """Process message with timing"""
        start_time = time.time()

        try:
            response = await super().process_message(message)
            self.metrics["total_messages"] += 1

            elapsed = time.time() - start_time
            self.metrics["total_time"] += elapsed
            self.metrics["avg_response_time"] = (
                self.metrics["total_time"] / self.metrics["total_messages"]
            )

            logger.info(f"Message processed in {elapsed:.2f}s")
            return response

        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error processing message: {str(e)}")
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()


# Example 3: Circuit Breaker Pattern
class CircuitBreaker:
    """Circuit breaker for fault tolerance"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half - open

    def call(self, func):
        """Decorator for circuit breaker"""

        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "half - open"
                    logger.info("Circuit breaker: half - open")
                else:
                    raise Exception("Circuit breaker is open")

            try:
                result = await func(*args, **kwargs)
                if self.state == "half - open":
                    self.state = "closed"
                    self.failure_count = 0
                    logger.info("Circuit breaker: closed")
                return result

            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    logger.error("Circuit breaker: open")

                raise

        return wrapper


# Example 4: Rate Limiting
class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(self, max_calls: int = 10, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    async def acquire(self) -> bool:
        """Acquire permission to make a call"""
        now = time.time()

        # Remove old calls outside time window
        self.calls = [t for t in self.calls if now - t < self.time_window]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True

        # Calculate wait time
        oldest_call = min(self.calls)
        wait_time = self.time_window - (now - oldest_call)
        logger.warning(f"Rate limit reached. Wait {wait_time:.1f}s")
        return False


# Example 5: Health Check
class HealthChecker:
    """Health check for agent system"""

    def __init__(self, mind: AgentMind):
        self.mind = mind
        self.last_check: Optional[datetime] = None
        self.status = "unknown"

    async def check_health(self) -> Dict[str, Any]:
        """Perform health check"""
        self.last_check = datetime.now()

        health = {
            "status": "healthy",
            "timestamp": self.last_check.isoformat(),
            "agents": {},
            "issues": [],
        }

        # Check each agent
        for agent in self.mind.agents:
            agent_health = {
                "name": agent.name,
                "active": agent.is_active,
                "memory_size": len(agent.memory),
            }

            # Check for issues
            if not agent.is_active:
                health["issues"].append(f"Agent {agent.name} is inactive")
                health["status"] = "degraded"

            if len(agent.memory) > 1000:
                health["issues"].append(f"Agent {agent.name} has large memory")

            health["agents"][agent.name] = agent_health

        self.status = health["status"]
        return health


async def example_1_error_handling():
    """Example 1: Error handling and recovery"""
    print("\n=== Example 1: Error Handling ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = ResilientAgent(name="resilient", role="assistant", llm_provider=llm, max_retries=3)

    print(f"Agent configured with {agent.max_retries} max retries")
    print("Implements exponential backoff for failures\n")


async def example_2_performance_monitoring():
    """Example 2: Performance monitoring"""
    print("\n=== Example 2: Performance Monitoring ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = MonitoredAgent(name="monitored", role="assistant", llm_provider=llm)

    # Simulate some work
    from agentmind import Message

    for i in range(3):
        msg = Message(content=f"Test message {i + 1}", sender="user", role="user")
        await agent.process_message(msg)

    # Get metrics
    metrics = agent.get_metrics()
    print("Performance Metrics:")
    print(f"  Total messages: {metrics['total_messages']}")
    print(f"  Average response time: {metrics['avg_response_time']:.2f}s")
    print(f"  Errors: {metrics['errors']}\n")


async def example_3_circuit_breaker():
    """Example 3: Circuit breaker pattern"""
    print("\n=== Example 3: Circuit Breaker ===\n")

    breaker = CircuitBreaker(failure_threshold=3, timeout=60)

    print("Circuit breaker configured:")
    print(f"  Failure threshold: {breaker.failure_threshold}")
    print(f"  Timeout: {breaker.timeout}s")
    print(f"  Current state: {breaker.state}\n")


async def example_4_rate_limiting():
    """Example 4: Rate limiting"""
    print("\n=== Example 4: Rate Limiting ===\n")

    limiter = RateLimiter(max_calls=5, time_window=60)

    print("Rate limiter configured:")
    print(f"  Max calls: {limiter.max_calls}")
    print(f"  Time window: {limiter.time_window}s")

    # Test rate limiting
    for i in range(7):
        allowed = await limiter.acquire()
        if allowed:
            print(f"  Call {i + 1}: Allowed")
        else:
            print(f"  Call {i + 1}: Rate limited")


async def example_5_health_checks():
    """Example 5: Health checks"""
    print("\n=== Example 5: Health Checks ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create system
    agent1 = Agent(name="agent1", role="analyst", llm_provider=llm)
    agent2 = Agent(name="agent2", role="writer", llm_provider=llm)

    mind = AgentMind()
    mind.add_agent(agent1)
    mind.add_agent(agent2)

    # Perform health check
    checker = HealthChecker(mind)
    health = await checker.check_health()

    print("Health Check Results:")
    print(f"  Status: {health['status']}")
    print(f"  Timestamp: {health['timestamp']}")
    print(f"  Agents checked: {len(health['agents'])}")
    print(f"  Issues: {len(health['issues'])}\n")


async def example_6_logging_best_practices():
    """Example 6: Logging best practices"""
    print("\n=== Example 6: Logging Best Practices ===\n")

    # Configure structured logging
    logger.info("System starting up")
    logger.info(
        "Configuration loaded", extra={"config": {"model": "llama3.2:3b", "max_tokens": 1000}}
    )

    # Log different levels
    logger.debug("Debug information")
    logger.info("Informational message")
    logger.warning("Warning message")
    logger.error("Error message")

    print("Logging configured with:")
    print("  - Structured format")
    print("  - Timestamp")
    print("  - Log levels")
    print("  - Context information\n")


async def example_7_security_considerations():
    """Example 7: Security best practices"""
    print("\n=== Example 7: Security Considerations ===\n")

    security_checklist = [
        "Input validation and sanitization",
        "API key management (environment variables)",
        "Rate limiting to prevent abuse",
        "Audit logging for sensitive operations",
        "Secure communication (HTTPS / TLS)",
        "Access control and authentication",
        "Data encryption at rest and in transit",
        "Regular security updates",
    ]

    print("Security Best Practices:")
    for i, item in enumerate(security_checklist, 1):
        print(f"  {i}. {item}")
    print()


async def example_8_scaling_strategies():
    """Example 8: Scaling strategies"""
    print("\n=== Example 8: Scaling Strategies ===\n")

    strategies = {
        "Horizontal Scaling": [
            "Multiple agent instances",
            "Load balancing",
            "Distributed task queue",
        ],
        "Vertical Scaling": [
            "Increase resources per agent",
            "Optimize memory usage",
            "Use faster models",
        ],
        "Caching": ["Cache LLM responses", "Cache tool results", "Memory optimization"],
        "Async Processing": [
            "Non - blocking operations",
            "Parallel agent execution",
            "Background tasks",
        ],
    }

    print("Scaling Strategies:\n")
    for strategy, tactics in strategies.items():
        print(f"{strategy}:")
        for tactic in tactics:
            print(f"  - {tactic}")
        print()


async def main():
    """Run all examples"""
    print("=" * 60)
    print("AgentMind Tutorial 06: Production Deployment")
    print("=" * 60)

    await example_1_error_handling()
    await example_2_performance_monitoring()
    await example_3_circuit_breaker()
    await example_4_rate_limiting()
    await example_5_health_checks()
    await example_6_logging_best_practices()
    await example_7_security_considerations()
    await example_8_scaling_strategies()

    print("\n" + "=" * 60)
    print("Tutorial Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. Implement retry logic with exponential backo")
    print("2. Monitor performance metrics continuously")
    print("3. Use circuit breakers for fault tolerance")
    print("4. Apply rate limiting to prevent abuse")
    print("5. Implement health checks for system monitoring")
    print("6. Follow security best practices")
    print("7. Plan for horizontal and vertical scaling")
    print("8. Use structured logging for debugging")
    print("\nCongratulations! You've completed all tutorials.")


if __name__ == "__main__":
    asyncio.run(main())
