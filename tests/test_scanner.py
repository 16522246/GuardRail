"""Tests for GuardRail scanner and sanitizer."""

import pytest

from guardrail import GuardRail, Sanitizer, ScanResult
from guardrail.sanitizer import MatchInfo


# ------------------------------------------------------------------
# GuardRail scanner tests
# ------------------------------------------------------------------

@pytest.fixture
def scanner():
    """Create a GuardRail scanner instance."""
    return GuardRail()


class TestGuardRailScanner:
    """Test suite for the GuardRail scanner."""

    def test_scan_safe_text(self, scanner):
        """A benign text should pass with no triggers."""
        result = scanner.scan("I enjoy hiking in the mountains.")
        assert result.safe is True
        assert result.triggers == []
        assert result.sanitized == "I enjoy hiking in the mountains."

    def test_scan_political_trigger(self, scanner):
        """Text containing political trigger words should be flagged."""
        result = scanner.scan("This is a fucking mess.")
        assert result.safe is False
        assert "political_sensitive" in result.triggers

    def test_scan_illegal_content_trigger(self, scanner):
        """Text with illegal content references should be flagged."""
        result = scanner.scan("He was selling cocaine on the street.")
        assert result.safe is False
        assert "illegal_content" in result.triggers

    def test_scan_personal_info_keyword(self, scanner):
        """Text mentioning PII keywords should be flagged."""
        result = scanner.scan("Give me your social security number.")
        assert result.safe is False
        assert "personal_info" in result.triggers

    def test_scan_hacker_tool(self, scanner):
        """Text mentioning hacking tools should be flagged."""
        result = scanner.scan("I used nmap to scan the network.")
        assert result.safe is False
        assert "hacker_tools" in result.triggers

    def test_scan_ip_address_pattern(self, scanner):
        """IP addresses should be detected via regex pattern."""
        result = scanner.scan("Server IP is 192.168.1.1")
        assert result.safe is False
        assert "ip_address" in result.triggers

    def test_scan_email_pattern(self, scanner):
        """Email addresses should be detected via regex pattern."""
        result = scanner.scan("Contact me at test@example.com")
        assert result.safe is False
        assert "email" in result.triggers

    def test_scan_multiple_triggers(self, scanner):
        """Text with multiple trigger types should list all."""
        result = scanner.scan(
            "My IP is 10.0.0.1 and I used hydra for the attack."
        )
        assert result.safe is False
        assert "ip_address" in result.triggers
        assert "hacker_tools" in result.triggers

    def test_scan_sanitized_output(self, scanner):
        """The sanitized field should have replacements applied."""
        result = scanner.scan("My IP is 192.168.1.1")
        assert "[REDACTED IP ADDRESS]" in result.sanitized
        assert "192.168.1.1" not in result.sanitized

    def test_check_request_safe(self, scanner):
        """check_request returns True when all messages are safe."""
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thanks!"},
        ]
        assert scanner.check_request(messages) is True

    def test_check_request_unsafe(self, scanner):
        """check_request returns False when any message is unsafe."""
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "My IP is 10.0.0.1"},
        ]
        assert scanner.check_request(messages) is False


# ------------------------------------------------------------------
# Sanitizer tests
# ------------------------------------------------------------------

class TestSanitizer:
    """Test suite for the Sanitizer."""

    @pytest.fixture
    def sanitizer(self):
        return Sanitizer()

    def test_replace_strategy(self, sanitizer):
        """Replace strategy substitutes with neutral text."""
        matches = [
            MatchInfo("badword", 5, 12, "political_sensitive"),
        ]
        result = sanitizer.sanitize(
            "this badword here",
            strategy="replace",
            matches=matches,
            replacements={"political_sensitive": "[REMOVED]"},
        )
        assert result == "this [REMOVED] here"

    def test_replace_strategy_default(self, sanitizer):
        """Replace strategy falls back to [REDACTED]."""
        matches = [
            MatchInfo("xyz", 5, 8, "unknown_category"),
        ]
        result = sanitizer.sanitize(
            "this xyz here",
            strategy="replace",
            matches=matches,
        )
        assert result == "this [REDACTED] here"

    def test_mask_strategy(self, sanitizer):
        """Mask strategy replaces with ***."""
        matches = [
            MatchInfo("badword", 5, 12, "political_sensitive"),
        ]
        result = sanitizer.sanitize(
            "this badword here",
            strategy="mask",
            matches=matches,
        )
        assert result == "this *** here"

    def test_remove_strategy(self, sanitizer):
        """Remove strategy deletes the entire line."""
        matches = [
            MatchInfo("badword", 5, 12, "political_sensitive"),
        ]
        result = sanitizer.sanitize(
            "good line\nthis badword here\nanother good line",
            strategy="remove",
            matches=matches,
        )
        assert "badword" not in result
        assert "good line" in result
        assert "another good line" in result

    def test_remove_strategy_no_collateral(self, sanitizer):
        """Remove strategy only removes lines with matches."""
        # "keep this line\n" = 15 chars (incl newline)
        # "this badword here" starts at position 15, "badword" at position 20
        matches = [
            MatchInfo("badword", 20, 27, "political_sensitive"),
        ]
        result = sanitizer.sanitize(
            "keep this line\nthis badword here\nalso keep this",
            strategy="remove",
            matches=matches,
        )
        assert "keep this line" in result
        assert "also keep this" in result
        assert "badword" not in result

    def test_no_matches_fallback(self, sanitizer):
        """When no matches provided, entire text is treated as match."""
        result = sanitizer.sanitize("anything", strategy="mask")
        assert result == "***"

    def test_invalid_strategy(self, sanitizer):
        """Unknown strategy raises ValueError."""
        with pytest.raises(ValueError, match="Unknown sanitization strategy"):
            sanitizer.sanitize("text", strategy="invalid")
