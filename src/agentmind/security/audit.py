"""Audit logging for security events."""

import json
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INPUT_SANITIZED = "input_sanitized"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    AGENT_CREATED = "agent_created"
    AGENT_EXECUTED = "agent_executed"
    DATA_ACCESS = "data_access"
    DATA_MODIFIED = "data_modified"
    ERROR = "error"


class AuditEvent(BaseModel):
    """Audit event model."""
    event_id: str = Field(..., description="Unique event ID")
    event_type: AuditEventType = Field(..., description="Event type")
    timestamp: float = Field(default_factory=time.time, description="Event timestamp")
    user_id: Optional[str] = Field(None, description="User ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    resource: Optional[str] = Field(None, description="Resource accessed")
    action: Optional[str] = Field(None, description="Action performed")
    status: str = Field("success", description="Event status")
    message: Optional[str] = Field(None, description="Event message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AuditLogger:
    """Logger for security audit events."""

    def __init__(
        self,
        log_file: Optional[Path] = None,
        console_output: bool = True,
        json_format: bool = True
    ):
        """Initialize audit logger.

        Args:
            log_file: Path to log file
            console_output: Whether to output to console
            json_format: Whether to use JSON format
        """
        self.log_file = log_file
        self.console_output = console_output
        self.json_format = json_format
        self._events: List[AuditEvent] = []

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        message: Optional[str] = None,
        **metadata
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            event_type: Type of event
            user_id: User ID
            ip_address: IP address
            resource: Resource accessed
            action: Action performed
            status: Event status
            message: Event message
            **metadata: Additional metadata

        Returns:
            Created audit event
        """
        import uuid

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            status=status,
            message=message,
            metadata=metadata
        )

        self._events.append(event)

        # Write to file
        if self.log_file:
            self._write_to_file(event)

        # Console output
        if self.console_output:
            self._write_to_console(event)

        return event

    def _write_to_file(self, event: AuditEvent) -> None:
        """Write event to log file.

        Args:
            event: Audit event
        """
        try:
            with open(self.log_file, "a") as f:
                if self.json_format:
                    f.write(event.model_dump_json() + "\n")
                else:
                    f.write(self._format_event(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def _write_to_console(self, event: AuditEvent) -> None:
        """Write event to console.

        Args:
            event: Audit event
        """
        if event.status == "success":
            logger.info(self._format_event(event))
        elif event.status == "failure":
            logger.warning(self._format_event(event))
        else:
            logger.error(self._format_event(event))

    def _format_event(self, event: AuditEvent) -> str:
        """Format event for logging.

        Args:
            event: Audit event

        Returns:
            Formatted string
        """
        parts = [
            f"[{event.event_type.value}]",
            f"user={event.user_id or 'anonymous'}",
        ]

        if event.ip_address:
            parts.append(f"ip={event.ip_address}")

        if event.resource:
            parts.append(f"resource={event.resource}")

        if event.action:
            parts.append(f"action={event.action}")

        parts.append(f"status={event.status}")

        if event.message:
            parts.append(f"message={event.message}")

        return " ".join(parts)

    def log_auth_success(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        method: str = "api_key"
    ) -> AuditEvent:
        """Log successful authentication.

        Args:
            user_id: User ID
            ip_address: IP address
            method: Authentication method

        Returns:
            Audit event
        """
        return self.log_event(
            AuditEventType.AUTH_SUCCESS,
            user_id=user_id,
            ip_address=ip_address,
            action="authenticate",
            message=f"Authentication successful via {method}"
        )

    def log_auth_failure(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: str = "invalid_credentials"
    ) -> AuditEvent:
        """Log failed authentication.

        Args:
            user_id: User ID
            ip_address: IP address
            reason: Failure reason

        Returns:
            Audit event
        """
        return self.log_event(
            AuditEventType.AUTH_FAILURE,
            user_id=user_id,
            ip_address=ip_address,
            action="authenticate",
            status="failure",
            message=f"Authentication failed: {reason}"
        )

    def log_permission_denied(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: Optional[str] = None
    ) -> AuditEvent:
        """Log permission denied.

        Args:
            user_id: User ID
            resource: Resource accessed
            action: Action attempted
            ip_address: IP address

        Returns:
            Audit event
        """
        return self.log_event(
            AuditEventType.PERMISSION_DENIED,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            status="denied",
            message=f"Permission denied for {action} on {resource}"
        )

    def log_rate_limit_exceeded(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        limit: int = 0
    ) -> AuditEvent:
        """Log rate limit exceeded.

        Args:
            user_id: User ID
            ip_address: IP address
            limit: Rate limit

        Returns:
            Audit event
        """
        return self.log_event(
            AuditEventType.RATE_LIMIT_EXCEEDED,
            user_id=user_id,
            ip_address=ip_address,
            status="blocked",
            message=f"Rate limit exceeded: {limit} requests",
            limit=limit
        )

    def log_suspicious_activity(
        self,
        user_id: Optional[str],
        ip_address: Optional[str],
        activity: str,
        details: Optional[Dict] = None
    ) -> AuditEvent:
        """Log suspicious activity.

        Args:
            user_id: User ID
            ip_address: IP address
            activity: Activity description
            details: Additional details

        Returns:
            Audit event
        """
        return self.log_event(
            AuditEventType.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            ip_address=ip_address,
            status="warning",
            message=f"Suspicious activity detected: {activity}",
            **(details or {})
        )

    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str = "read",
        ip_address: Optional[str] = None
    ) -> AuditEvent:
        """Log data access.

        Args:
            user_id: User ID
            resource: Resource accessed
            action: Action performed
            ip_address: IP address

        Returns:
            Audit event
        """
        return self.log_event(
            AuditEventType.DATA_ACCESS,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            message=f"Data access: {action} on {resource}"
        )

    def get_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[AuditEvent]:
        """Get audit events with filters.

        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of events

        Returns:
            List of audit events
        """
        events = self._events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        if limit:
            events = events[-limit:]

        return events

    def get_statistics(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get audit statistics.

        Args:
            start_time: Start time
            end_time: End time

        Returns:
            Statistics dictionary
        """
        events = self.get_events(start_time=start_time, end_time=end_time)

        stats = {
            "total_events": len(events),
            "by_type": {},
            "by_status": {},
            "unique_users": set(),
            "unique_ips": set(),
        }

        for event in events:
            # Count by type
            event_type = event.event_type.value
            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1

            # Count by status
            stats["by_status"][event.status] = stats["by_status"].get(event.status, 0) + 1

            # Track unique users and IPs
            if event.user_id:
                stats["unique_users"].add(event.user_id)
            if event.ip_address:
                stats["unique_ips"].add(event.ip_address)

        stats["unique_users"] = len(stats["unique_users"])
        stats["unique_ips"] = len(stats["unique_ips"])

        return stats

    def clear_old_events(self, max_age: float = 86400 * 30) -> int:
        """Clear old events.

        Args:
            max_age: Maximum age in seconds (default: 30 days)

        Returns:
            Number of events cleared
        """
        cutoff = time.time() - max_age
        original_count = len(self._events)
        self._events = [e for e in self._events if e.timestamp > cutoff]
        cleared = original_count - len(self._events)

        if cleared > 0:
            logger.info(f"Cleared {cleared} old audit events")

        return cleared
