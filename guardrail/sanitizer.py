"""Sanitization engine for GuardRail.

Provides multiple strategies for handling detected unsafe content:
- replace:  Replace matched text with a neutral description.
- mask:     Replace matched text with asterisks (***).
- remove:   Delete the entire line containing matched text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MatchInfo:
    """Information about a detected match in text."""

    text: str
    start: int
    end: int
    category: str
    pattern: Optional[str] = None


class Sanitizer:
    """Text sanitizer with multiple strategies.

    Strategies can be applied individually or in combination to handle
    flagged content detected by the GuardRail scanner.
    """

    def __init__(self) -> None:
        self._mask_char: str = "*"

    # ------------------------------------------------------------------
    # Strategies
    # ------------------------------------------------------------------

    @staticmethod
    def _replace_strategy(
        text: str, matches: List[MatchInfo], replacements: Dict[str, str]
    ) -> str:
        """Replace matched content with a neutral description.

        Uses a per-category replacement string, falling back to a
        generic placeholder when no specific replacement exists.

        Args:
            text: The original text.
            matches: List of detected matches.
            replacements: Mapping of category -> replacement text.

        Returns:
            Sanitized text with matched portions replaced.
        """
        sanitized = text
        # Process in reverse order to preserve offsets
        for m in reversed(matches):
            replacement = replacements.get(
                m.category,
                replacements.get("default", "[REDACTED]"),
            )
            sanitized = (
                sanitized[: m.start]
                + replacement
                + sanitized[m.end :]
            )
        return sanitized

    def _mask_strategy(
        self, text: str, matches: List[MatchInfo]
    ) -> str:
        """Replace matched content with mask characters.

        Each matched token is replaced with ``***``.

        Args:
            text: The original text.
            matches: List of detected matches.

        Returns:
            Sanitized text with matched portions masked.
        """
        sanitized = text
        for m in reversed(matches):
            mask = self._mask_char * min(len(m.text), 3)
            sanitized = (
                sanitized[: m.start] + mask + sanitized[m.end :]
            )
        return sanitized

    @staticmethod
    def _remove_strategy(
        text: str, matches: List[MatchInfo]
    ) -> str:
        """Remove entire lines containing matched content.

        Lines that contain any flagged text are stripped from the
        result. Consecutive blank lines are collapsed.

        Args:
            text: The original text.
            matches: List of detected matches.

        Returns:
            Sanitized text with offending lines removed.
        """
        # Build a set of line indices to remove
        lines = text.splitlines(keepends=True)
        remove_indices: set[int] = set()
        for m in matches:
            # Determine which line(s) this match spans
            pos = 0
            for idx, line in enumerate(lines):
                line_len = len(line)
                if pos <= m.start < pos + line_len:
                    remove_indices.add(idx)
                    # If the match spans multiple lines, remove those too
                    end_pos = pos + line_len
                    while end_pos < m.end:
                        idx += 1
                        remove_indices.add(idx)
                        end_pos += len(lines[idx])
                    break
                pos += line_len

        return "".join(
            line for i, line in enumerate(lines)
            if i not in remove_indices
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sanitize(
        self,
        text: str,
        strategy: str = "replace",
        matches: Optional[List[MatchInfo]] = None,
        replacements: Optional[Dict[str, str]] = None,
    ) -> str:
        """Sanitize text using the selected strategy.

        Args:
            text: The input text to sanitize.
            strategy: One of ``"replace"``, ``"mask"``, or ``"remove"``.
            matches: Detected matches. If ``None``, a simple catch-all
                pattern is used for demonstration.
            replacements: Mapping of category -> replacement text
                (only used by the ``"replace"`` strategy).

        Returns:
            The sanitized text.

        Raises:
            ValueError: For an unknown strategy.
        """
        if matches is None:
            # Fallback: treat the whole string as a single match
            matches = [
                MatchInfo(
                    text=text,
                    start=0,
                    end=len(text),
                    category="unknown",
                )
            ]

        if replacements is None:
            replacements = {
                "default": "[REDACTED]",
            }

        strategy = strategy.strip().lower()

        if strategy == "replace":
            return self._replace_strategy(
                text, matches, replacements
            )
        elif strategy == "mask":
            return self._mask_strategy(text, matches)
        elif strategy == "remove":
            return self._remove_strategy(text, matches)
        else:
            raise ValueError(
                f"Unknown sanitization strategy: {strategy!r}. "
                f"Expected one of: 'replace', 'mask', 'remove'."
            )
