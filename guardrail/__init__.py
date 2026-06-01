"""GuardRail — AI content safety scanner."""

from guardrail.scanner import GuardRail, ScanResult
from guardrail.sanitizer import Sanitizer

__version__ = "0.1.0"
__all__ = ["GuardRail", "ScanResult", "Sanitizer"]
