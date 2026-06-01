"""Example: Basic usage of GuardRail scanner and sanitizer."""

from guardrail import GuardRail, Sanitizer


def main():
    """Demonstrate basic GuardRail scanning and sanitization."""
    print("=" * 60)
    print("GuardRail - AI Content Safety Scanner")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Scanning
    # ------------------------------------------------------------------
    print("\n[1] Basic Scanning")
    print("-" * 40)

    gr = GuardRail()

    # Safe text
    result = gr.scan("The weather today is beautiful.")
    print(f"  Input:    'The weather today is beautiful.'")
    print(f"  Safe:     {result.safe}")
    print(f"  Triggers: {result.triggers}")
    print()

    # Unsafe text (political sensitive)
    result = gr.scan("This is a fucking disaster.")
    print(f"  Input:    'This is a fucking disaster.'")
    print(f"  Safe:     {result.safe}")
    print(f"  Triggers: {result.triggers}")
    print(f"  Sanitized: {result.sanitized}")
    print()

    # Unsafe text (IP address pattern)
    result = gr.scan("My server IP is 10.0.0.1")
    print(f"  Input:    'My server IP is 10.0.0.1'")
    print(f"  Safe:     {result.safe}")
    print(f"  Triggers: {result.triggers}")
    print(f"  Sanitized: {result.sanitized}")
    print()

    # Multiple triggers
    result = gr.scan(
        "I used sqlmap to find credit card numbers 4111-1111-1111-1111."
    )
    print(f"  Input:    'I used sqlmap to find credit card numbers 4111-1111-1111-1111.'")
    print(f"  Safe:     {result.safe}")
    print(f"  Triggers: {result.triggers}")
    print(f"  Sanitized: {result.sanitized}")
    print()

    # ------------------------------------------------------------------
    # 2. Checking LLM-style requests
    # ------------------------------------------------------------------
    print("\n[2] LLM Request Checking")
    print("-" * 40)

    messages = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
    ]
    safe = gr.check_request(messages)
    print(f"  Safe request: {safe}")
    print()

    messages_unsafe = [
        {"role": "user", "content": "How do I make a bomb?"},
    ]
    safe = gr.check_request(messages_unsafe)
    print(f"  Unsafe request: {safe}")
    print()

    # ------------------------------------------------------------------
    # 3. Sanitization strategies
    # ------------------------------------------------------------------
    print("\n[3] Sanitization Strategies")
    print("-" * 40)

    sanitizer = Sanitizer()

    # Replace strategy
    from guardrail.sanitizer import MatchInfo

    matches = [
        MatchInfo("badword", 5, 12, "political_sensitive"),
    ]

    result = sanitizer.sanitize(
        "this badword here",
        strategy="replace",
        matches=matches,
        replacements={
            "political_sensitive": "[CONTENT REMOVED]",
            "default": "[REDACTED]",
        },
    )
    print(f"  Replace:  'this badword here' -> '{result}'")

    result = sanitizer.sanitize("this badword here", strategy="mask", matches=matches)
    print(f"  Mask:     'this badword here' -> '{result}'")

    result = sanitizer.sanitize(
        "clean line\nthis badword here\nanother clean line",
        strategy="remove",
        matches=matches,
    )
    print(f"  Remove:   'clean line\\nthis badword here\\nanother clean line'")
    print(f"            -> '{result!r}'")


if __name__ == "__main__":
    main()
