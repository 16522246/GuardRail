"""Proxy middleware stub for GuardRail.

Provides a callable middleware that can be integrated into web
frameworks (Flask, FastAPI, Starlette, etc.) or LLM proxy servers to
inspect and sanitize content in-flight.

Usage (conceptual):

    from guardrail.proxy import GuardRailMiddleware

    middleware = GuardRailMiddleware()
    safe, result = middleware.check("user input text")
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

from guardrail import GuardRail
from guardrail.sanitizer import Sanitizer


class GuardRailMiddleware:
    """Proxy middleware for intercepting and scanning content.

    Acts as a transparent layer that inspects requests and responses
    for unsafe content. Designed to be plugged into ASGI/WSGI
    applications or custom proxy pipelines.
    """

    def __init__(
        self,
        scanner: Optional[GuardRail] = None,
        sanitizer: Optional[Sanitizer] = None,
        block_on_trigger: bool = True,
        default_sanitize_strategy: str = "replace",
    ):
        """Initialize the middleware.

        Args:
            scanner: A GuardRail instance (created fresh if None).
            sanitizer: A Sanitizer instance (created fresh if None).
            block_on_trigger: Whether to block requests that trigger
                safety violations (True) or just flag them (False).
            default_sanitize_strategy: Strategy to use when sanitizing
                content.
        """
        self.scanner = scanner or GuardRail()
        self.sanitizer = sanitizer or Sanitizer()
        self.block_on_trigger = block_on_trigger
        self.default_sanitize_strategy = default_sanitize_strategy

    def check(
        self,
        text: str,
        sanitize: bool = True,
        strategy: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check a single text string for unsafe content.

        Args:
            text: The text to check.
            sanitize: Whether to produce a sanitized version.
            strategy: Override sanitization strategy (default from
                constructor).

        Returns:
            Tuple of ``(is_safe, details_dict)`` where ``details_dict``
            contains:
                - "triggers": List of triggered categories/patterns.
                - "sanitized": Sanitized text (if sanitize=True).
                - "blocked": Whether the content was blocked.
        """
        result = self.scanner.scan(text)
        details: Dict[str, Any] = {
            "triggers": result.triggers,
            "blocked": self.block_on_trigger and not result.safe,
        }

        if sanitize:
            details["sanitized"] = result.sanitized
        else:
            details["sanitized"] = text

        return result.safe, details

    def check_request(
        self,
        messages: List[Dict[str, str]],
        sanitize: bool = True,
        strategy: Optional[str] = None,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check a list of LLM-style messages.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            sanitize: Whether to produce sanitized versions.
            strategy: Override sanitization strategy.

        Returns:
            Tuple of ``(all_safe, per_message_details)``.
        """
        details_list: List[Dict[str, Any]] = []
        all_safe = True

        for msg in messages:
            content = msg.get("content", "")
            safe, details = self.check(
                content, sanitize=sanitize, strategy=strategy
            )
            details["role"] = msg.get("role", "unknown")
            details_list.append(details)
            if not safe:
                all_safe = False

        return all_safe, details_list

    def sanitize_response(
        self,
        text: str,
        strategy: Optional[str] = None,
    ) -> str:
        """Sanitize a response string.

        Convenience method that runs the full scan and returns the
        sanitized output directly.

        Args:
            text: The response text to sanitize.
            strategy: Override sanitization strategy.

        Returns:
            The sanitized text.
        """
        _, details = self.check(
            text, sanitize=True, strategy=strategy
        )
        return details.get("sanitized", text)

    async def async_check(
        self,
        text: str,
        sanitize: bool = True,
        strategy: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Async version of :meth:`check`.

        Currently a synchronous wrapper; provided for API compatibility
        with async frameworks.
        """
        return self.check(
            text, sanitize=sanitize, strategy=strategy
        )
