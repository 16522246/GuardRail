# GuardRail 🛡️

**AI Content Safety Scanner** — Scan, detect, and sanitize unsafe content in AI-generated text.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-orange)](https://github.com/zhangzhiwei610/guardrail)

GuardRail is a lightweight, rule-based content safety library that helps identify and sanitize sensitive or inappropriate content in text. It supports exact-match keyword scanning, regex pattern matching, and multiple sanitization strategies (replace, mask, remove).

## Features

- 🔍 **Keyword Scanning** — Detect trigger words across categories (political, illegal, personal info, hacker tools)
- 🧩 **Regex Pattern Matching** — Identify content patterns like IP addresses, phone numbers, credentials
- 🧹 **Smart Sanitization** — Replace, mask, or remove flagged content
- 🚀 **Lightweight & Fast** — Pure Python, zero heavy dependencies
- 🔌 **Extensible** — Easy to add custom rules and patterns
- 🖥️ **CLI & Python API** — Use from the command line or integrate into your application

## Quick Start

### Installation

```bash
pip install guardrail-safety
```

### Python API

```python
from guardrail import GuardRail, Sanitizer

# Initialize scanner
gr = GuardRail()

# Scan text
result = gr.scan("My IP is 192.168.1.1 and I love cats.")
print(result.safe)       # False
print(result.triggers)   # ['ip_address']
print(result.sanitized)  # "My IP is [REDACTED IP ADDRESS] and I love cats."

# Sanitize with different strategies
sanitizer = Sanitizer()
print(sanitizer.sanitize("Bad content here", strategy="mask"))
# "***"

print(sanitizer.sanitize("Bad content here", strategy="remove"))
# ""
```

### CLI Usage

```bash
# Scan text
guardrail scan --text "Check this IP: 10.0.0.1"

# Scan a file
guardrail scan --file input.txt

# Sanitize with mask strategy
guardrail sanitize --text "Sensitive data here" --strategy mask

# Sanitize with remove strategy
guardrail sanitize --text "Sensitive data here" --strategy remove
```

## Rule Categories

| Category | Description |
|----------|-------------|
| `political_sensitive` | Politically sensitive terms |
| `illegal_content` | Illegal activity references |
| `personal_info` | PII indicators |
| `hacker_tools` | Hacking tool references |

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

**zhangzhiwei610**
