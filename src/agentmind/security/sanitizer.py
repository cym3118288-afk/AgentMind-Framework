"""Input sanitization and validation."""

import re
import html
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class SanitizationLevel(str, Enum):
    """Sanitization strictness levels."""
    NONE = "none"
    BASIC = "basic"
    MODERATE = "moderate"
    STRICT = "strict"


class InputSanitizer:
    """Sanitize and validate user inputs."""

    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers
        r"eval\s*\(",  # eval() calls
        r"exec\s*\(",  # exec() calls
        r"__import__",  # Python imports
        r"subprocess",  # Subprocess calls
        r"os\.system",  # OS system calls
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--\s*$)",
        r"(;\s*DROP\b)",
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"\.\.\\",
    ]

    def __init__(self, level: SanitizationLevel = SanitizationLevel.MODERATE):
        """Initialize sanitizer.

        Args:
            level: Sanitization level
        """
        self.level = level

    def sanitize_text(self, text: str) -> str:
        """Sanitize text input.

        Args:
            text: Input text

        Returns:
            Sanitized text
        """
        if self.level == SanitizationLevel.NONE:
            return text

        # HTML escape
        sanitized = html.escape(text)

        if self.level in (SanitizationLevel.MODERATE, SanitizationLevel.STRICT):
            # Remove dangerous patterns
            for pattern in self.DANGEROUS_PATTERNS:
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        if self.level == SanitizationLevel.STRICT:
            # Additional strict filtering
            sanitized = self._strict_filter(sanitized)

        return sanitized

    def _strict_filter(self, text: str) -> str:
        """Apply strict filtering.

        Args:
            text: Input text

        Returns:
            Filtered text
        """
        # Remove all HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Remove special characters except basic punctuation
        text = re.sub(r"[^\w\s.,!?-]", "", text)

        return text

    def validate_input(
        self,
        text: str,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        allowed_chars: Optional[str] = None
    ) -> bool:
        """Validate input text.

        Args:
            text: Input text
            max_length: Maximum length
            min_length: Minimum length
            allowed_chars: Regex pattern of allowed characters

        Returns:
            True if valid, False otherwise
        """
        # Length checks
        if max_length and len(text) > max_length:
            logger.warning(f"Input exceeds max length: {len(text)} > {max_length}")
            return False

        if min_length and len(text) < min_length:
            logger.warning(f"Input below min length: {len(text)} < {min_length}")
            return False

        # Character validation
        if allowed_chars and not re.match(f"^[{allowed_chars}]+$", text):
            logger.warning("Input contains disallowed characters")
            return False

        return True

    def detect_sql_injection(self, text: str) -> bool:
        """Detect potential SQL injection attempts.

        Args:
            text: Input text

        Returns:
            True if SQL injection detected
        """
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return True
        return False

    def detect_path_traversal(self, path: str) -> bool:
        """Detect path traversal attempts.

        Args:
            path: File path

        Returns:
            True if path traversal detected
        """
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(f"Path traversal pattern detected: {pattern}")
                return True
        return False

    def detect_xss(self, text: str) -> bool:
        """Detect potential XSS attacks.

        Args:
            text: Input text

        Returns:
            True if XSS detected
        """
        xss_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"XSS pattern detected: {pattern}")
                return True
        return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename.

        Args:
            filename: Input filename

        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = filename.split("/")[-1].split("\\")[-1]

        # Remove dangerous characters
        filename = re.sub(r"[^\w\s.-]", "", filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = name[:250] + ("." + ext if ext else "")

        return filename

    def sanitize_dict(
        self,
        data: Dict[str, Any],
        keys_to_sanitize: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Sanitize dictionary values.

        Args:
            data: Input dictionary
            keys_to_sanitize: Specific keys to sanitize (None for all)

        Returns:
            Sanitized dictionary
        """
        sanitized = {}

        for key, value in data.items():
            if keys_to_sanitize is None or key in keys_to_sanitize:
                if isinstance(value, str):
                    sanitized[key] = self.sanitize_text(value)
                elif isinstance(value, dict):
                    sanitized[key] = self.sanitize_dict(value, keys_to_sanitize)
                elif isinstance(value, list):
                    sanitized[key] = [
                        self.sanitize_text(item) if isinstance(item, str) else item
                        for item in value
                    ]
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value

        return sanitized

    def validate_email(self, email: str) -> bool:
        """Validate email address.

        Args:
            email: Email address

        Returns:
            True if valid email
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def validate_url(self, url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
        """Validate URL.

        Args:
            url: URL to validate
            allowed_schemes: Allowed URL schemes (default: http, https)

        Returns:
            True if valid URL
        """
        allowed_schemes = allowed_schemes or ["http", "https"]

        pattern = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"
        if not re.match(pattern, url, re.IGNORECASE):
            return False

        # Check scheme
        scheme = url.split("://")[0].lower()
        return scheme in allowed_schemes

    def sanitize_for_llm(self, text: str, max_length: int = 10000) -> str:
        """Sanitize text for LLM input.

        Args:
            text: Input text
            max_length: Maximum length

        Returns:
            Sanitized text
        """
        # Remove control characters
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."

        return text.strip()

    def check_prompt_injection(self, text: str) -> bool:
        """Detect potential prompt injection attempts.

        Args:
            text: Input text

        Returns:
            True if prompt injection detected
        """
        injection_patterns = [
            r"ignore\s+(previous|above|all)\s+instructions",
            r"disregard\s+(previous|above|all)\s+instructions",
            r"forget\s+(previous|above|all)\s+instructions",
            r"you\s+are\s+now",
            r"new\s+instructions",
            r"system\s*:\s*",
            r"assistant\s*:\s*",
        ]

        for pattern in injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Prompt injection pattern detected: {pattern}")
                return True

        return False

    def sanitize_api_key(self, key: str) -> str:
        """Sanitize API key for logging.

        Args:
            key: API key

        Returns:
            Masked API key
        """
        if len(key) <= 8:
            return "***"

        return key[:4] + "*" * (len(key) - 8) + key[-4:]
