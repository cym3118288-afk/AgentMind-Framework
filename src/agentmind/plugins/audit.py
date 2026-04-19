"""Plugin audit logging for security and compliance."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""

    PLUGIN_REGISTERED = "plugin_registered"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    PLUGIN_ACTIVATED = "plugin_activated"
    PLUGIN_DEACTIVATED = "plugin_deactivated"
    PLUGIN_ERROR = "plugin_error"
    PLUGIN_EXECUTED = "plugin_executed"
    PERMISSION_DENIED = "permission_denied"
    CONFIG_CHANGED = "config_changed"
    DEPENDENCY_RESOLVED = "dependency_resolved"
    HEALTH_CHECK_FAILED = "health_check_failed"


class AuditEvent(BaseModel):
    """Audit event for plugin operations."""

    event_id: str = Field(..., description="Unique event ID")
    event_type: AuditEventType = Field(..., description="Event type")
    plugin_name: str = Field(..., description="Plugin name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    user_id: Optional[str] = Field(None, description="User ID if applicable")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event details")
    severity: str = Field(default="info", description="Event severity (info, warning, error)")
    success: bool = Field(default=True, description="Whether operation succeeded")


class PluginAuditLogger:
    """Audit logger for plugin operations."""

    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize audit logger.

        Args:
            log_dir: Directory for audit logs
        """
        self.log_dir = log_dir or Path.cwd() / "logs" / "plugin_audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._events: List[AuditEvent] = []
        self._event_counter = 0

    def _generate_event_id(self) -> str:
        """Generate unique event ID.

        Returns:
            Event ID
        """
        self._event_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"evt_{timestamp}_{self._event_counter:06d}"

    def log_event(
        self,
        event_type: AuditEventType,
        plugin_name: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        severity: str = "info",
        success: bool = True,
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            event_type: Type of event
            plugin_name: Plugin name
            details: Event details
            user_id: User ID
            severity: Event severity
            success: Whether operation succeeded

        Returns:
            Created audit event
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            plugin_name=plugin_name,
            details=details or {},
            user_id=user_id,
            severity=severity,
            success=success,
        )

        self._events.append(event)

        # Write to daily log file
        self._write_to_file(event)

        logger.debug(f"Audit event logged: {event.event_type} for {plugin_name}")
        return event

    def _write_to_file(self, event: AuditEvent) -> None:
        """Write event to log file.

        Args:
            event: Audit event
        """
        try:
            # Daily log file
            log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"

            with open(log_file, "a") as f:
                f.write(json.dumps(event.model_dump(mode="json"), default=str) + "\n")

        except Exception as e:
            logger.error(f"Error writing audit log: {e}")

    def get_events(
        self,
        plugin_name: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Get audit events with filters.

        Args:
            plugin_name: Filter by plugin name
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            user_id: Filter by user ID
            severity: Filter by severity

        Returns:
            List of matching events
        """
        results = self._events

        if plugin_name:
            results = [e for e in results if e.plugin_name == plugin_name]

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if start_time:
            results = [e for e in results if e.timestamp >= start_time]

        if end_time:
            results = [e for e in results if e.timestamp <= end_time]

        if user_id:
            results = [e for e in results if e.user_id == user_id]

        if severity:
            results = [e for e in results if e.severity == severity]

        return results

    def get_plugin_history(self, plugin_name: str) -> List[AuditEvent]:
        """Get complete history for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            List of events
        """
        return self.get_events(plugin_name=plugin_name)

    def get_failed_operations(self, plugin_name: Optional[str] = None) -> List[AuditEvent]:
        """Get failed operations.

        Args:
            plugin_name: Optional plugin name filter

        Returns:
            List of failed events
        """
        events = self._events if not plugin_name else self.get_events(plugin_name=plugin_name)
        return [e for e in events if not e.success]

    def get_security_events(self) -> List[AuditEvent]:
        """Get security-related events.

        Returns:
            List of security events
        """
        security_types = [AuditEventType.PERMISSION_DENIED, AuditEventType.PLUGIN_ERROR]
        return [e for e in self._events if e.event_type in security_types]

    def export_logs(
        self,
        output_file: Path,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> bool:
        """Export audit logs to file.

        Args:
            output_file: Output file path
            start_time: Start time filter
            end_time: End time filter

        Returns:
            True if successful
        """
        try:
            events = self.get_events(start_time=start_time, end_time=end_time)

            with open(output_file, "w") as f:
                for event in events:
                    f.write(json.dumps(event.model_dump(mode="json"), default=str) + "\n")

            logger.info(f"Exported {len(events)} audit events to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error exporting audit logs: {e}")
            return False

    def load_logs_from_file(self, log_file: Path) -> int:
        """Load audit logs from file.

        Args:
            log_file: Log file path

        Returns:
            Number of events loaded
        """
        try:
            count = 0
            with open(log_file, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        event = AuditEvent(**data)
                        self._events.append(event)
                        count += 1

            logger.info(f"Loaded {count} audit events from {log_file}")
            return count

        except Exception as e:
            logger.error(f"Error loading audit logs: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics.

        Returns:
            Statistics dictionary
        """
        total_events = len(self._events)
        failed_events = len([e for e in self._events if not e.success])

        event_type_counts = {}
        for event in self._events:
            event_type_counts[event.event_type.value] = (
                event_type_counts.get(event.event_type.value, 0) + 1
            )

        plugin_counts = {}
        for event in self._events:
            plugin_counts[event.plugin_name] = plugin_counts.get(event.plugin_name, 0) + 1

        severity_counts = {}
        for event in self._events:
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1

        return {
            "total_events": total_events,
            "failed_events": failed_events,
            "success_rate": (
                (total_events - failed_events) / total_events if total_events > 0 else 0
            ),
            "event_types": event_type_counts,
            "plugins": plugin_counts,
            "severity": severity_counts,
        }

    def clear_old_logs(self, days: int = 30) -> int:
        """Clear audit logs older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of events removed
        """
        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self._events)

        self._events = [e for e in self._events if e.timestamp >= cutoff]

        removed = original_count - len(self._events)
        logger.info(f"Removed {removed} old audit events")
        return removed


# Helper functions for common audit operations


def log_plugin_loaded(
    audit_logger: PluginAuditLogger, plugin_name: str, version: str, user_id: Optional[str] = None
) -> None:
    """Log plugin loaded event.

    Args:
        audit_logger: Audit logger instance
        plugin_name: Plugin name
        version: Plugin version
        user_id: User ID
    """
    audit_logger.log_event(
        event_type=AuditEventType.PLUGIN_LOADED,
        plugin_name=plugin_name,
        details={"version": version},
        user_id=user_id,
        severity="info",
        success=True,
    )


def log_plugin_error(
    audit_logger: PluginAuditLogger,
    plugin_name: str,
    error: Exception,
    user_id: Optional[str] = None,
) -> None:
    """Log plugin error event.

    Args:
        audit_logger: Audit logger instance
        plugin_name: Plugin name
        error: Exception that occurred
        user_id: User ID
    """
    audit_logger.log_event(
        event_type=AuditEventType.PLUGIN_ERROR,
        plugin_name=plugin_name,
        details={"error_type": type(error).__name__, "error_message": str(error)},
        user_id=user_id,
        severity="error",
        success=False,
    )


def log_permission_denied(
    audit_logger: PluginAuditLogger,
    plugin_name: str,
    resource: str,
    action: str,
    user_id: Optional[str] = None,
) -> None:
    """Log permission denied event.

    Args:
        audit_logger: Audit logger instance
        plugin_name: Plugin name
        resource: Resource name
        action: Action attempted
        user_id: User ID
    """
    audit_logger.log_event(
        event_type=AuditEventType.PERMISSION_DENIED,
        plugin_name=plugin_name,
        details={"resource": resource, "action": action},
        user_id=user_id,
        severity="warning",
        success=False,
    )


def log_config_changed(
    audit_logger: PluginAuditLogger,
    plugin_name: str,
    changes: Dict[str, Any],
    user_id: Optional[str] = None,
) -> None:
    """Log configuration change event.

    Args:
        audit_logger: Audit logger instance
        plugin_name: Plugin name
        changes: Configuration changes
        user_id: User ID
    """
    audit_logger.log_event(
        event_type=AuditEventType.CONFIG_CHANGED,
        plugin_name=plugin_name,
        details={"changes": changes},
        user_id=user_id,
        severity="info",
        success=True,
    )


from datetime import timedelta
