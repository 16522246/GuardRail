"""CLI entry point for GuardRail.

Provides two commands:
  - scan:     Scan text or a file for unsafe content.
  - sanitize: Sanitize text using a specified strategy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from guardrail import GuardRail, Sanitizer


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="guardrail",
        description="GuardRail — AI Content Safety Scanner",
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- scan ---
    scan_parser = subparsers.add_parser(
        "scan", help="Scan text for unsafe content"
    )
    input_group = scan_parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--text", "-t", type=str, help="Text string to scan"
    )
    input_group.add_argument(
        "--file", "-f", type=str, help="Path to a text file to scan"
    )
    scan_parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output results as JSON",
    )

    # --- sanitize ---
    sanitize_parser = subparsers.add_parser(
        "sanitize", help="Sanitize text using a strategy"
    )
    input_group2 = sanitize_parser.add_mutually_exclusive_group()
    input_group2.add_argument(
        "--text", "-t", type=str, help="Text string to sanitize"
    )
    input_group2.add_argument(
        "--file", "-f", type=str, help="Path to a text file to sanitize"
    )
    sanitize_parser.add_argument(
        "--strategy",
        "-s",
        type=str,
        default="replace",
        choices=["replace", "mask", "remove"],
        help="Sanitization strategy (default: replace)",
    )
    sanitize_parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output results as JSON",
    )

    return parser


def _read_input(text: str | None, file_path: str | None) -> str:
    """Read input text from a string or a file."""
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    if text:
        return text
    # Read from stdin
    return sys.stdin.read()


def cmd_scan(args: argparse.Namespace) -> None:
    """Handle the ``scan`` command."""
    try:
        content = _read_input(args.text, args.file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    gr = GuardRail()
    result = gr.scan(content)

    if args.json:
        import json

        print(
            json.dumps(
                {
                    "safe": result.safe,
                    "triggers": result.triggers,
                    "sanitized": result.sanitized,
                },
                indent=2,
            )
        )
    else:
        status = "✓ SAFE" if result.safe else "✗ UNSAFE"
        print(f"Status:  {status}")
        print(f"Triggers: {result.triggers or '(none)'}")
        print(f"Sanitized: {result.sanitized}")


def cmd_sanitize(args: argparse.Namespace) -> None:
    """Handle the ``sanitize`` command."""
    try:
        content = _read_input(args.text, args.file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    sanitizer = Sanitizer()
    result = sanitizer.sanitize(content, strategy=args.strategy)

    if args.json:
        import json

        print(json.dumps({"sanitized": result, "strategy": args.strategy}, indent=2))
    else:
        print(f"Strategy: {args.strategy}")
        print(f"Result:\n{result}")


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "sanitize":
        cmd_sanitize(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
