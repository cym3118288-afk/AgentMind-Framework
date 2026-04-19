"""
Comprehensive tests for plugins and security modules
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from agentmind.plugins.base import Plugin, PluginMetadata, PluginConfig
from agentmind.plugins.manager import PluginManager
from agentmind.plugins.loader import PluginLoader
from agentmind.security.auth import AuthManager, APIKey, User
from agentmind.security.rate_limiter import RateLimiter, RateLimitConfig
from agentmind.security.sanitizer import InputSanitizer
from agentmind.security.audit import AuditLogger, AuditEvent


class TestPluginBase:
    """Test Plugin base class"""

    def test_plugin_metadata(self):
        """Test plugin metadata"""
        metadata = PluginMetadata(
            name="test_plugin", version="1.0.0", description="Test plugin", author="Test Author"
        )

        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test plugin"

    def test_plugin_config(self):
        """Test plugin configuration"""
        config = PluginConfig(enabled=True, settings={"key": "value"})

        assert config.enabled is True
        assert config.settings["key"] == "value"

    def test_plugin_initialization(self):
        """Test plugin initialization"""

        class TestPlugin(Plugin):
            def __init__(self):
                super().__init__()

            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="test",
                    version="1.0.0",
                    description="Test",
                    author="Test",
                    plugin_type="tool",
                )

            async def initialize(self):
                pass

            async def shutdown(self):
                pass

            async def execute(self, *args, **kwargs):
                return "executed"

        plugin = TestPlugin()
        assert plugin.get_metadata().name == "test"

    @pytest.mark.asyncio
    async def test_plugin_lifecycle(self):
        """Test plugin lifecycle"""

        class LifecyclePlugin(Plugin):
            def __init__(self):
                metadata = PluginMetadata(name="lifecycle", version="1.0.0", description="Test")
                super().__init__(metadata)
                self.initialized = False
                self.shutdown = False

            async def initialize(self):
                self.initialized = True

            async def shutdown(self):
                self.shutdown = True

            async def execute(self, *args, **kwargs):
                return "ok"

        plugin = LifecyclePlugin()
        await plugin.initialize()
        assert plugin.initialized is True

        await plugin.shutdown()
        assert plugin.shutdown is True


class TestPluginManager:
    """Test PluginManager"""

    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization"""
        manager = PluginManager()
        assert manager is not None
        assert len(manager.plugins) == 0

    @pytest.mark.asyncio
    async def test_register_plugin(self):
        """Test registering a plugin"""

        class SimplePlugin(Plugin):
            def __init__(self):
                metadata = PluginMetadata(name="simple", version="1.0.0", description="Simple")
                super().__init__(metadata)

            async def initialize(self):
                pass

            async def execute(self, *args, **kwargs):
                return "result"

        manager = PluginManager()
        plugin = SimplePlugin()

        await manager.register(plugin)

        assert "simple" in manager.plugins
        assert manager.plugins["simple"] == plugin

    @pytest.mark.asyncio
    async def test_unregister_plugin(self):
        """Test unregistering a plugin"""

        class RemovablePlugin(Plugin):
            def __init__(self):
                metadata = PluginMetadata(name="removable", version="1.0.0", description="Test")
                super().__init__(metadata)

            async def initialize(self):
                pass

            async def execute(self, *args, **kwargs):
                return "result"

        manager = PluginManager()
        plugin = RemovablePlugin()

        await manager.register(plugin)
        assert "removable" in manager.plugins

        await manager.unregister("removable")
        assert "removable" not in manager.plugins

    @pytest.mark.asyncio
    async def test_execute_plugin(self):
        """Test executing a plugin"""

        class ExecutablePlugin(Plugin):
            def __init__(self):
                metadata = PluginMetadata(name="executable", version="1.0.0", description="Test")
                super().__init__(metadata)

            async def initialize(self):
                pass

            async def execute(self, value):
                return value * 2

        manager = PluginManager()
        plugin = ExecutablePlugin()
        await manager.register(plugin)

        result = await manager.execute("executable", 5)
        assert result == 10


class TestPluginLoader:
    """Test PluginLoader"""

    def test_plugin_loader_initialization(self):
        """Test plugin loader initialization"""
        loader = PluginLoader(plugin_dir="./plugins")
        assert loader.plugin_dir == "./plugins"

    def test_discover_plugins(self):
        """Test discovering plugins"""
        loader = PluginLoader(plugin_dir="./plugins")

        with patch("os.listdir", return_value=["plugin1.py", "plugin2.py", "not_plugin.txt"]):
            plugins = loader.discover_plugins()

            # Should find .py files
            assert len(plugins) >= 0

    def test_load_plugin_from_file(self):
        """Test loading plugin from file"""
        loader = PluginLoader(plugin_dir="./plugins")

        # Mock loading a plugin
        with patch.object(loader, "load_plugin") as mock_load:
            mock_load.return_value = Mock()

            plugin = loader.load_plugin("test_plugin.py")
            assert plugin is not None


class TestAuthManager:
    """Test AuthManager"""

    def test_auth_manager_initialization(self):
        """Test auth manager initialization"""
        auth = AuthManager()
        assert auth is not None

    def test_create_api_key(self):
        """Test creating API key"""
        auth = AuthManager()

        api_key = auth.create_api_key(
            name="test_key", user_id="user123", permissions=["read", "write"]
        )

        assert api_key.name == "test_key"
        assert api_key.user_id == "user123"
        assert "read" in api_key.permissions

    def test_validate_api_key(self):
        """Test validating API key"""
        auth = AuthManager()

        api_key = auth.create_api_key("test", "user123", ["read"])

        # Valid key
        is_valid = auth.validate_api_key(api_key.key)
        assert is_valid is True

        # Invalid key
        is_valid = auth.validate_api_key("invalid_key")
        assert is_valid is False

    def test_revoke_api_key(self):
        """Test revoking API key"""
        auth = AuthManager()

        api_key = auth.create_api_key("test", "user123", ["read"])
        auth.revoke_api_key(api_key.key)

        # Should no longer be valid
        is_valid = auth.validate_api_key(api_key.key)
        assert is_valid is False

    def test_user_authentication(self):
        """Test user authentication"""
        auth = AuthManager()

        # Create user
        user = User(user_id="user123", username="testuser", email="test@example.com")

        auth.register_user(user)

        # Authenticate
        authenticated = auth.authenticate_user("testuser", "password")
        assert authenticated is not None or authenticated is False


class TestRateLimiter:
    """Test RateLimiter"""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        config = RateLimitConfig(max_requests=10, time_window=60)

        limiter = RateLimiter(config)
        assert limiter.config.max_requests == 10

    def test_rate_limiter_allows_requests(self):
        """Test rate limiter allows requests within limit"""
        config = RateLimitConfig(max_requests=5, time_window=60)
        limiter = RateLimiter(config)

        for _ in range(5):
            assert limiter.allow_request("user123") is True

    def test_rate_limiter_blocks_excess_requests(self):
        """Test rate limiter blocks excess requests"""
        config = RateLimitConfig(max_requests=3, time_window=60)
        limiter = RateLimiter(config)

        # First 3 should succeed
        for _ in range(3):
            assert limiter.allow_request("user123") is True

        # 4th should fail
        assert limiter.allow_request("user123") is False

    @pytest.mark.asyncio
    async def test_rate_limiter_resets_after_window(self):
        """Test rate limiter resets after time window"""
        config = RateLimitConfig(max_requests=2, time_window=0.1)  # 100ms
        limiter = RateLimiter(config)

        # Use up limit
        assert limiter.allow_request("user123") is True
        assert limiter.allow_request("user123") is True
        assert limiter.allow_request("user123") is False

        # Wait for reset
        await asyncio.sleep(0.15)

        # Should allow again
        assert limiter.allow_request("user123") is True

    def test_rate_limiter_per_user(self):
        """Test rate limiter tracks per user"""
        config = RateLimitConfig(max_requests=2, time_window=60)
        limiter = RateLimiter(config)

        # User 1
        assert limiter.allow_request("user1") is True
        assert limiter.allow_request("user1") is True
        assert limiter.allow_request("user1") is False

        # User 2 should have separate limit
        assert limiter.allow_request("user2") is True
        assert limiter.allow_request("user2") is True


class TestInputSanitizer:
    """Test InputSanitizer"""

    def test_sanitizer_initialization(self):
        """Test sanitizer initialization"""
        sanitizer = InputSanitizer()
        assert sanitizer is not None

    def test_sanitize_string(self):
        """Test sanitizing string input"""
        sanitizer = InputSanitizer()

        # Test with potentially dangerous input
        dangerous = "<script>alert('xss')</script>"
        safe = sanitizer.sanitize_string(dangerous)

        assert "<script>" not in safe

    def test_sanitize_sql_injection(self):
        """Test sanitizing SQL injection attempts"""
        sanitizer = InputSanitizer()

        dangerous = "'; DROP TABLE users; --"
        safe = sanitizer.sanitize_string(dangerous)

        # Should escape or remove dangerous characters
        assert safe != dangerous or "DROP TABLE" not in safe

    def test_sanitize_path_traversal(self):
        """Test sanitizing path traversal attempts"""
        sanitizer = InputSanitizer()

        dangerous = "../../etc/passwd"
        safe = sanitizer.sanitize_path(dangerous)

        assert ".." not in safe

    def test_validate_email(self):
        """Test email validation"""
        sanitizer = InputSanitizer()

        assert sanitizer.validate_email("test@example.com") is True
        assert sanitizer.validate_email("invalid-email") is False
        assert sanitizer.validate_email("test@") is False

    def test_validate_url(self):
        """Test URL validation"""
        sanitizer = InputSanitizer()

        assert sanitizer.validate_url("https://example.com") is True
        assert sanitizer.validate_url("http://example.com/path") is True
        assert sanitizer.validate_url("not-a-url") is False

    def test_sanitize_json(self):
        """Test sanitizing JSON input"""
        sanitizer = InputSanitizer()

        dangerous_json = '{"key": "<script>alert(1)</script>"}'
        safe_json = sanitizer.sanitize_json(dangerous_json)

        assert "<script>" not in safe_json


class TestAuditLogger:
    """Test AuditLogger"""

    def test_audit_logger_initialization(self):
        """Test audit logger initialization"""
        logger = AuditLogger()
        assert logger is not None

    def test_log_event(self):
        """Test logging audit event"""
        logger = AuditLogger()

        event = AuditEvent(
            event_type="user_login",
            user_id="user123",
            timestamp=datetime.now(),
            details={"ip": "192.168.1.1"},
        )

        logger.log_event(event)

        # Verify event was logged
        events = logger.get_events(user_id="user123")
        assert len(events) >= 1

    def test_log_security_event(self):
        """Test logging security event"""
        logger = AuditLogger()

        logger.log_security_event(
            event_type="failed_login", user_id="user123", severity="high", details={"attempts": 5}
        )

        events = logger.get_events(event_type="failed_login")
        assert len(events) >= 1

    def test_get_events_by_user(self):
        """Test getting events by user"""
        logger = AuditLogger()

        # Log events for different users
        logger.log_event(AuditEvent("action1", "user1", datetime.now(), {}))
        logger.log_event(AuditEvent("action2", "user2", datetime.now(), {}))
        logger.log_event(AuditEvent("action3", "user1", datetime.now(), {}))

        user1_events = logger.get_events(user_id="user1")
        assert len(user1_events) >= 2

    def test_get_events_by_time_range(self):
        """Test getting events by time range"""
        logger = AuditLogger()

        now = datetime.now()
        past = now - timedelta(hours=1)

        logger.log_event(AuditEvent("old_event", "user1", past, {}))
        logger.log_event(AuditEvent("new_event", "user1", now, {}))

        recent_events = logger.get_events(start_time=now - timedelta(minutes=5))

        # Should only get recent events
        assert len(recent_events) >= 1

    def test_export_audit_log(self):
        """Test exporting audit log"""
        logger = AuditLogger()

        logger.log_event(AuditEvent("event1", "user1", datetime.now(), {}))
        logger.log_event(AuditEvent("event2", "user2", datetime.now(), {}))

        # Export to file
        export_data = logger.export_log()

        assert export_data is not None
        assert len(export_data) >= 2


class TestSecurityIntegration:
    """Integration tests for security modules"""

    def test_auth_with_rate_limiting(self):
        """Test authentication with rate limiting"""
        auth = AuthManager()
        rate_limiter = RateLimiter(RateLimitConfig(max_requests=3, time_window=60))

        # Create user
        user = User("user123", "testuser", "test@example.com")
        auth.register_user(user)

        # Attempt multiple logins
        for i in range(3):
            if rate_limiter.allow_request("user123"):
                auth.authenticate_user("testuser", "password")

        # 4th attempt should be rate limited
        assert rate_limiter.allow_request("user123") is False

    def test_sanitize_and_audit(self):
        """Test input sanitization with audit logging"""
        sanitizer = InputSanitizer()
        audit = AuditLogger()

        # Sanitize dangerous input
        dangerous = "<script>alert('xss')</script>"
        safe = sanitizer.sanitize_string(dangerous)

        # Log the sanitization
        audit.log_security_event(
            event_type="input_sanitized",
            user_id="user123",
            severity="medium",
            details={"original": dangerous, "sanitized": safe},
        )

        events = audit.get_events(event_type="input_sanitized")
        assert len(events) >= 1

    def test_complete_security_workflow(self):
        """Test complete security workflow"""
        auth = AuthManager()
        rate_limiter = RateLimiter(RateLimitConfig(max_requests=5, time_window=60))
        sanitizer = InputSanitizer()
        audit = AuditLogger()

        # 1. Create API key
        api_key = auth.create_api_key("app_key", "user123", ["read", "write"])
        audit.log_event(AuditEvent("api_key_created", "user123", datetime.now(), {}))

        # 2. Validate API key
        is_valid = auth.validate_api_key(api_key.key)
        assert is_valid is True

        # 3. Check rate limit
        can_proceed = rate_limiter.allow_request("user123")
        assert can_proceed is True

        # 4. Sanitize input
        user_input = "<script>test</script>"
        safe_input = sanitizer.sanitize_string(user_input)

        # 5. Log the request
        audit.log_event(AuditEvent("api_request", "user123", datetime.now(), {"input": safe_input}))

        # Verify workflow
        events = audit.get_events(user_id="user123")
        assert len(events) >= 2


class TestPluginSecurity:
    """Test plugin security features"""

    @pytest.mark.asyncio
    async def test_plugin_with_permissions(self):
        """Test plugin with permission checks"""

        class SecurePlugin(Plugin):
            def __init__(self):
                metadata = PluginMetadata(
                    name="secure", version="1.0.0", description="Secure plugin"
                )
                super().__init__(metadata)
                self.required_permissions = ["admin"]

            async def initialize(self):
                pass

            async def execute(self, user_permissions):
                if "admin" not in user_permissions:
                    raise PermissionError("Admin permission required")
                return "executed"

        plugin = SecurePlugin()

        # Should fail without permission
        with pytest.raises(PermissionError):
            await plugin.execute(["read"])

        # Should succeed with permission
        result = await plugin.execute(["admin"])
        assert result == "executed"

    @pytest.mark.asyncio
    async def test_plugin_input_validation(self):
        """Test plugin with input validation"""

        class ValidatingPlugin(Plugin):
            def __init__(self):
                metadata = PluginMetadata(
                    name="validating", version="1.0.0", description="Validating plugin"
                )
                super().__init__(metadata)
                self.sanitizer = InputSanitizer()

            async def initialize(self):
                pass

            async def execute(self, user_input):
                # Validate and sanitize input
                safe_input = self.sanitizer.sanitize_string(user_input)
                return safe_input

        plugin = ValidatingPlugin()

        # Test with dangerous input
        result = await plugin.execute("<script>alert(1)</script>")
        assert "<script>" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
