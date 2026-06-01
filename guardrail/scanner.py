"""Core scanning engine for GuardRail.

Provides exact-match keyword scanning and regex pattern matching
against user-defined rules loaded from YAML files.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml


@dataclass
class ScanResult:
    """Result of a content scan.

    Attributes:
        safe: Whether the content passed all safety checks.
        triggers: List of trigger categories or pattern names that matched.
        sanitized: Content with matched text replaced by safe descriptions.
    """

    safe: bool = True
    triggers: List[str] = field(default_factory=list)
    sanitized: str = ""


class GuardRail:
    """Content safety scanner.

    Loads trigger words (exact match) and regex patterns from YAML rule
    files bundled with the package and performs content analysis.
    """

    def __init__(
        self,
        rules_dir: Optional[str] = None,
        trigger_words_path: Optional[str] = None,
        patterns_path: Optional[str] = None,
        replacements_path: Optional[str] = None,
    ):
        """Initialize the scanner and load rules.

        Args:
            rules_dir: Override for the rules directory (default: bundled rules/).
            trigger_words_path: Override trigger words YAML path.
            patterns_path: Override patterns YAML path.
            replacements_path: Override replacements YAML path.
        """
        if rules_dir is None:
            rules_dir = os.path.join(os.path.dirname(__file__), "rules")

        self.rules_dir = rules_dir
        self._trigger_words: Dict[str, List[str]] = {}
        self._patterns: Dict[str, Dict[str, str]] = {}
        self._replacements: Dict[str, str] = {}

        self._load_trigger_words(trigger_words_path)
        self._load_patterns(patterns_path)
        self._load_replacements(replacements_path)

    # ------------------------------------------------------------------
    # Rule loading
    # ------------------------------------------------------------------

    def _load_yaml(self, filename: str) -> dict:
        """Load a YAML file from the rules directory."""
        path = os.path.join(self.rules_dir, filename)
        if not os.path.isfile(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    def _load_trigger_words(self, path: Optional[str] = None) -> None:
        """Load trigger words from YAML."""
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._trigger_words = data if isinstance(data, dict) else {}
        else:
            self._trigger_words = self._load_yaml("trigger_words.yml")

    def _load_patterns(self, path: Optional[str] = None) -> None:
        """Load regex patterns from YAML."""
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._patterns = data if isinstance(data, dict) else {}
        else:
            self._patterns = self._load_yaml("patterns.yml")

    def _load_replacements(self, path: Optional[str] = None) -> None:
        """Load replacement mappings from YAML."""
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._replacements = data if isinstance(data, dict) else {}
        else:
            self._replacements = self._load_yaml("replacements.yml")

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def scan(self, text: str) -> ScanResult:
        """Scan text for unsafe content.

        Performs both exact-match keyword detection and regex pattern
        matching. The sanitized field in the result contains the text
        with matched tokens replaced by their safe descriptions.

        Args:
            text: The input string to scan.

        Returns:
            A ScanResult with detection and sanitization details.
        """
        sanitized = text
        triggers: List[str] = []

        # 1. Exact-match keyword scanning
        for category, words in self._trigger_words.items():
            for word in words:
                # Case-insensitive word-boundary match
                pattern = re.compile(
                    r"\b" + re.escape(word) + r"\b", re.IGNORECASE
                )
                if pattern.search(sanitized):
                    triggers.append(category)
                    # Replace with a safe description
                    replacement = self._replacements.get(
                        "default", "[REDACTED]"
                    )
                    desc = self._replacements.get(
                        category, replacement
                    )
                    sanitized = pattern.sub(desc, sanitized)
                    break  # one trigger per category

        # 2. Regex pattern matching
        for pattern_name, info in self._patterns.items():
            try:
                regex = re.compile(info["pattern"], re.IGNORECASE)
            except (re.error, KeyError):
                continue
            if regex.search(sanitized):
                triggers.append(pattern_name)
                replacement = info.get(
                    "replacement",
                    info.get("description", "[REDACTED]"),
                )
                sanitized = regex.sub(replacement, sanitized)

        # Deduplicate while preserving order
        seen: set = set()
        unique_triggers: List[str] = []
        for t in triggers:
            if t not in seen:
                seen.add(t)
                unique_triggers.append(t)

        return ScanResult(
            safe=len(unique_triggers) == 0,
            triggers=unique_triggers,
            sanitized=sanitized,
        )

    def check_request(self, messages: List[Dict[str, str]]) -> bool:
        """Check whether a list of message dicts is safe.

        Designed for LLM request-style inputs such as
        ``[{"role": "user", "content": "..."}]``.

        Args:
            messages: List of dicts, each with at least a ``"content"`` key.

        Returns:
            True if *all* messages pass the safety scan.
        """
        for msg in messages:
            content = msg.get("content", "")
            result = self.scan(content)
            if not result.safe:
                return False
        return True
