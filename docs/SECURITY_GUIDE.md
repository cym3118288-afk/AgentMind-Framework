# Security Best Practices

AgentMind provides comprehensive security features to protect your applications and data. This guide covers security best practices and how to use the built-in security features.

## Overview

The security module (`agentmind.security`) includes:

- **Input Sanitization**: Protect against XSS, SQL injection, and other attacks
- **Rate Limiting**: Prevent abuse and DoS attacks
- **Authentication**: API key and user authentication
- **Authorization**: Role-based access control
- **Audit Logging**: Track security events and user actions

## Installation

Security features are included with AgentMind core. No additional dependencies required.

## Input Sanitization

### Basic Usage

```python
from agentmind.security import InputSanitizer, SanitizationLevel

# Initialize sanitizer
sanitizer = InputSanitizer(level=SanitizationLevel.MODERATE)

# Sanitize user input
user_input = "<script>alert('xss')</script>Hello"
clean_input = sanitizer.sanitize_text(user_input)
# Result: "&lt;script&gt;alert('xss')&lt;/script&gt;Hello"

# Validate input
is_valid = sanitizer.validate_input(
    user_input,
    max_length=1000,
    min_length=1
)
```

### Sanitization Levels

```python
# NONE - No sanitization (use with caution)
sanitizer = InputSanitizer(level=SanitizationLevel.NONE)

# BASIC - HTML escaping only
sanitizer = InputSanitizer(level=SanitizationLevel.BASIC)

# MODERATE - HTML escaping + dangerous pattern removal (recommended)
sanitizer = InputSanitizer(level=SanitizationLevel.MODERATE)

# STRICT - Aggressive filtering (may affect legitimate input)
sanitizer = InputSanitizer(level=SanitizationLevel.STRICT)
```

### Threat Detection

```python
# Detect SQL injection
if sanitizer.detect_sql_injection("SELECT * FROM users WHERE id=1 OR 1=1"):
    print("SQL injection detected!")

# Detect XSS
if sanitizer.detect_xss("<script>alert('xss')</script>"):
    print("XSS detected!")

# Detect path traversal
if sanitizer.detect_path_traversal("../../etc/passwd"):
    print("Path traversal detected!")

# Detect prompt injection
if sanitizer.check_prompt_injection("Ignore previous instructions and..."):
    print("Prompt injection detected!")
```

### Sanitize for LLM

```python
# Prepare text for LLM input
user_message = "User input with \x00 control chars and very long text..."
clean_message = sanitizer.sanitize_for_llm(user_message, max_length=10000)
```

### Sanitize Complex Data

```python
# Sanitize dictionary
data = {
    "name": "<script>alert('xss')</script>John",
    "email": "john@example.com",
    "message": "Hello <b>world</b>"
}

clean_data = sanitizer.sanitize_dict(data, keys_to_sanitize=["name", "message"])
```

## Rate Limiting

### Token Bucket Rate Limiter

```python
from agentmind.security import RateLimiter, RateLimitExceeded

# Create rate limiter (100 requests per 60 seconds)
limiter = RateLimiter(max_requests=100, time_window=60.0)

# Check rate limit
try:
    await limiter.check_rate_limit("user_123")
    # Process request
except RateLimitExceeded as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after}s")

# Acquire with automatic waiting
await limiter.acquire("user_123", wait=True)

# Get remaining requests
remaining = limiter.get_remaining("user_123")
print(f"Remaining requests: {remaining}")

# Reset rate limit
limiter.reset("user_123")
```

### Sliding Window Rate Limiter

```python
from agentmind.security import SlidingWindowRateLimiter

limiter = SlidingWindowRateLimiter(max_requests=100, time_window=60.0)

try:
    await limiter.check_rate_limit("user_123")
except RateLimitExceeded as e:
    print(f"Rate limited: {e}")
```

### Adaptive Rate Limiter

```python
from agentmind.security import AdaptiveRateLimiter

# Rate limiter that adapts to system load
limiter = AdaptiveRateLimiter(
    base_max_requests=100,
    time_window=60.0,
    min_requests=10,
    max_requests=1000
)

# Adjust based on system load (0.0 to 1.0)
limiter.adjust_limit(load_factor=0.7)  # 70% load

await limiter.acquire("user_123")
```

### Rate Limiting in API

```python
from fastapi import FastAPI, HTTPException, Request
from agentmind.security import RateLimiter

app = FastAPI()
limiter = RateLimiter(max_requests=100, time_window=60.0)

@app.post("/api/collaborate")
async def collaborate(request: Request):
    # Get client identifier
    client_id = request.client.host
    
    try:
        await limiter.check_rate_limit(client_id)
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {e.retry_after}s"
        )
    
    # Process request
    return {"status": "success"}
```

## Authentication

### API Key Management

```python
from agentmind.security import AuthManager

auth = AuthManager()

# Create user
user = auth.create_user(
    user_id="user_123",
    username="john_doe",
    email="john@example.com",
    roles=["user"]
)

# Generate API key
api_key = auth.generate_api_key(
    user_id="user_123",
    name="Production Key",
    permissions=["read", "write"],
    expires_in=86400 * 30  # 30 days
)

print(f"API Key: {api_key}")

# Validate API key
key_obj = auth.validate_api_key(api_key)
if key_obj:
    print(f"Valid key for user: {key_obj.user_id}")

# Revoke API key
auth.revoke_api_key(api_key)

# List user's API keys
keys = auth.list_api_keys(user_id="user_123")
```

### User Management

```python
# Create user with roles
user = auth.create_user(
    user_id="admin_001",
    username="admin",
    roles=["admin"]
)

# Update user roles
auth.update_user_roles("user_123", ["user", "premium"])

# Get user
user = auth.get_user("user_123")
print(f"User: {user.username}, Roles: {user.roles}")
```

### Authorization

```python
# Check permission
has_permission = auth.check_permission(
    user_id="user_123",
    permission="write",
    api_key=api_key
)

if has_permission:
    # Allow action
    pass
else:
    # Deny action
    raise PermissionError("Insufficient permissions")

# Define custom roles
auth.add_role("moderator", {"read", "write", "moderate"})
```

### Password Hashing

```python
# Hash password
password = "secure_password_123"
hashed, salt = auth.hash_password(password)

# Store hashed and salt in database
# ...

# Verify password
is_valid = auth.verify_password(password, hashed, salt)
```

### Secure API Endpoint

```python
from fastapi import FastAPI, HTTPException, Header
from agentmind.security import AuthManager

app = FastAPI()
auth = AuthManager()

@app.post("/api/secure-endpoint")
async def secure_endpoint(
    x_api_key: str = Header(...),
    data: dict = None
):
    # Validate API key
    key_obj = auth.validate_api_key(x_api_key)
    if not key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check permission
    if not auth.check_permission(key_obj.user_id, "write", x_api_key):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Process request
    return {"status": "success"}
```

## Audit Logging

### Basic Usage

```python
from agentmind.security import AuditLogger, AuditEventType
from pathlib import Path

# Initialize audit logger
audit = AuditLogger(
    log_file=Path("logs/audit.log"),
    console_output=True,
    json_format=True
)

# Log authentication success
audit.log_auth_success(
    user_id="user_123",
    ip_address="192.168.1.100",
    method="api_key"
)

# Log authentication failure
audit.log_auth_failure(
    user_id="user_123",
    ip_address="192.168.1.100",
    reason="invalid_api_key"
)

# Log permission denied
audit.log_permission_denied(
    user_id="user_123",
    resource="/api/admin",
    action="delete",
    ip_address="192.168.1.100"
)

# Log rate limit exceeded
audit.log_rate_limit_exceeded(
    user_id="user_123",
    ip_address="192.168.1.100",
    limit=100
)

# Log suspicious activity
audit.log_suspicious_activity(
    user_id="user_123",
    ip_address="192.168.1.100",
    activity="Multiple failed login attempts",
    details={"attempts": 5, "timespan": "60s"}
)

# Log data access
audit.log_data_access(
    user_id="user_123",
    resource="user_database",
    action="read",
    ip_address="192.168.1.100"
)
```

### Custom Events

```python
# Log custom event
audit.log_event(
    event_type=AuditEventType.AGENT_EXECUTED,
    user_id="user_123",
    resource="research_agent",
    action="execute",
    status="success",
    message="Agent completed task successfully",
    task_id="task_456",
    duration=12.5
)
```

### Query Events

```python
# Get events by type
auth_failures = audit.get_events(
    event_type=AuditEventType.AUTH_FAILURE,
    limit=100
)

# Get events by user
user_events = audit.get_events(
    user_id="user_123",
    start_time=time.time() - 3600  # Last hour
)

# Get statistics
stats = audit.get_statistics(
    start_time=time.time() - 86400  # Last 24 hours
)

print(f"Total events: {stats['total_events']}")
print(f"Unique users: {stats['unique_users']}")
print(f"By type: {stats['by_type']}")
```

### Cleanup

```python
# Clear old events (older than 30 days)
cleared = audit.clear_old_events(max_age=86400 * 30)
print(f"Cleared {cleared} old events")
```

## Complete Security Example

```python
from agentmind import Agent, AgentMind
from agentmind.llm import LiteLLMProvider
from agentmind.security import (
    InputSanitizer,
    RateLimiter,
    AuthManager,
    AuditLogger,
    SanitizationLevel
)
from pathlib import Path

# Initialize security components
sanitizer = InputSanitizer(level=SanitizationLevel.MODERATE)
limiter = RateLimiter(max_requests=100, time_window=60.0)
auth = AuthManager()
audit = AuditLogger(log_file=Path("logs/audit.log"))

# Create user and API key
user = auth.create_user("user_123", "john_doe", roles=["user"])
api_key = auth.generate_api_key("user_123", "Main Key", permissions=["read", "write"])

async def secure_agent_request(
    user_input: str,
    api_key: str,
    ip_address: str
):
    """Process agent request with security checks."""
    
    # 1. Validate API key
    key_obj = auth.validate_api_key(api_key)
    if not key_obj:
        audit.log_auth_failure(ip_address=ip_address, reason="invalid_api_key")
        raise ValueError("Invalid API key")
    
    audit.log_auth_success(key_obj.user_id, ip_address, method="api_key")
    
    # 2. Check rate limit
    try:
        await limiter.check_rate_limit(key_obj.user_id)
    except RateLimitExceeded as e:
        audit.log_rate_limit_exceeded(key_obj.user_id, ip_address, limit=100)
        raise
    
    # 3. Check permissions
    if not auth.check_permission(key_obj.user_id, "write", api_key):
        audit.log_permission_denied(key_obj.user_id, "agent_execute", "write", ip_address)
        raise PermissionError("Insufficient permissions")
    
    # 4. Sanitize input
    if sanitizer.check_prompt_injection(user_input):
        audit.log_suspicious_activity(
            key_obj.user_id,
            ip_address,
            "Prompt injection detected",
            {"input": user_input[:100]}
        )
        raise ValueError("Suspicious input detected")
    
    clean_input = sanitizer.sanitize_for_llm(user_input)
    
    # 5. Execute agent
    llm = LiteLLMProvider(model="gpt-4")
    mind = AgentMind(llm_provider=llm)
    
    agent = Agent(name="Assistant", role="assistant")
    mind.add_agent(agent)
    
    result = await mind.collaborate(clean_input, max_rounds=1)
    
    # 6. Log successful execution
    audit.log_event(
        AuditEventType.AGENT_EXECUTED,
        user_id=key_obj.user_id,
        ip_address=ip_address,
        resource="assistant_agent",
        action="execute",
        status="success"
    )
    
    return result.final_output

# Use the secure function
result = await secure_agent_request(
    user_input="What is the weather today?",
    api_key=api_key,
    ip_address="192.168.1.100"
)
```

## Security Checklist

### Input Validation
- [ ] Sanitize all user inputs
- [ ] Validate input length and format
- [ ] Check for SQL injection patterns
- [ ] Check for XSS patterns
- [ ] Check for path traversal attempts
- [ ] Check for prompt injection

### Authentication & Authorization
- [ ] Use API keys for authentication
- [ ] Set expiration times for API keys
- [ ] Implement role-based access control
- [ ] Use strong password hashing
- [ ] Validate permissions before actions

### Rate Limiting
- [ ] Implement rate limiting on all endpoints
- [ ] Use appropriate limits for different endpoints
- [ ] Handle rate limit errors gracefully
- [ ] Monitor rate limit violations

### Audit Logging
- [ ] Log all authentication attempts
- [ ] Log permission denials
- [ ] Log suspicious activities
- [ ] Log data access and modifications
- [ ] Regularly review audit logs
- [ ] Archive old logs

### General Security
- [ ] Use HTTPS in production
- [ ] Keep dependencies updated
- [ ] Use environment variables for secrets
- [ ] Implement proper error handling
- [ ] Don't expose sensitive information in errors
- [ ] Regular security audits

## Environment Variables

Store sensitive configuration in environment variables:

```bash
# .env file
AGENTMIND_API_KEY=your-api-key-here
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Security settings
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_TIME_WINDOW=60
SANITIZATION_LEVEL=moderate
```

Load in your application:

```python
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("AGENTMIND_API_KEY")
```

## Common Vulnerabilities

### Prompt Injection

```python
# Bad: Direct user input to LLM
result = await agent.process(user_input)

# Good: Sanitize and validate
if sanitizer.check_prompt_injection(user_input):
    raise ValueError("Invalid input")
clean_input = sanitizer.sanitize_for_llm(user_input)
result = await agent.process(clean_input)
```

### API Key Exposure

```python
# Bad: Hardcoded API key
api_key = "sk-1234567890abcdef"

# Good: Environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Good: Mask in logs
masked = sanitizer.sanitize_api_key(api_key)
logger.info(f"Using API key: {masked}")
```

### Insufficient Rate Limiting

```python
# Bad: No rate limiting
@app.post("/api/endpoint")
async def endpoint(data: dict):
    return process(data)

# Good: With rate limiting
@app.post("/api/endpoint")
async def endpoint(request: Request, data: dict):
    await limiter.check_rate_limit(request.client.host)
    return process(data)
```

## Troubleshooting

### Rate Limit Issues

```python
# Check remaining requests
remaining = limiter.get_remaining("user_123")
if remaining < 10:
    logger.warning(f"Low rate limit: {remaining} remaining")

# Cleanup old entries
limiter.cleanup_old_entries(max_age=3600)
```

### Authentication Issues

```python
# Debug API key validation
key_obj = auth.validate_api_key(api_key)
if not key_obj:
    print("Invalid API key")
elif not key_obj.is_active:
    print("API key is inactive")
elif key_obj.expires_at and time.time() > key_obj.expires_at:
    print("API key expired")
```

### Audit Log Analysis

```python
# Find failed authentication attempts
failures = audit.get_events(
    event_type=AuditEventType.AUTH_FAILURE,
    start_time=time.time() - 3600
)

# Group by IP address
from collections import Counter
ips = Counter(e.ip_address for e in failures if e.ip_address)
print(f"Failed attempts by IP: {ips.most_common(10)}")
```

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)
- [Prompt Injection Guide](https://simonwillison.net/2023/Apr/14/worst-that-can-happen/)

## Support

For security issues, please email security@agentmind.dev or open a private security advisory on GitHub.
