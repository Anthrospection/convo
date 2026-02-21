# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ConvoFormatter is a Python CLI tool that converts raw Claude Code conversation transcripts (`.txt`) into clean, formatted documents (PDF, HTML, Markdown, or plain text). It strips scaffolding noise (tool calls, progress spinners, file confirmations) and renders the result in user-friendly formats.

**Status**: Implemented (MVP complete). Package lives under `convoformat/`. See `ConvoFormat_PRD.md` for full requirements.

## Technology Stack

- **Language**: Python 3.13 (pinned via `.python-version`)
- **CLI**: `click`
- **PDF**: `reportlab` + `reportlab.platypus`
- **HTML**: Jinja2 templates (single-file output)
- **PII Redaction**: `presidio-analyzer`, `presidio-anonymizer`, `spacy` (optional extra)
- **Packaging**: `pyproject.toml`

## Commands

A `.venv` is already initialised. Activate it with `source .venv/bin/activate` before running any commands.

```bash
# Install for development
pip install -e .

# Install with optional privacy support
pip install -e ".[private]"

# Install spaCy model (required for --private)
python -m spacy download en_core_web_lg

# Run tests
pytest

# Run a single test file
pytest tests/test_parser.py

# Run linting
ruff check .

# Auto-fix lint issues
ruff check --fix .
```

The `pyproject.toml` starts empty — populate `[project].dependencies` with `click`, `reportlab`, `jinja2` and `[project.optional-dependencies].private` with `presidio-analyzer`, `presidio-anonymizer`, `spacy` before first install.

## CLI Usage

```bash
convoformat [OPTIONS] INPUT_FILE [OUTPUT_FILE]

# Quick PDF with defaults (dark theme, mobile)
convoformat Conversation.txt

# Mobile-optimized dark PDF with custom labels
convoformat Conversation.txt --output=pdf --theme=dark --mobile \
  --assistant="Elliot" --user="Stacey" --title="My Conversation"

# Privacy-redacted HTML
convoformat Conversation.txt --output=html --private --assistant="AI" --user="User"

# Markdown for Obsidian
convoformat Conversation.txt --output=markdown --assistant="Elliot" --user="Stacey"
```

## Planned Architecture

```
convoformat/
├── cli.py          # Entry point, click argument definitions
├── parser.py       # Two-pass input parser, turn classification, noise stripping
├── privacy.py      # PII redaction (regex layer + Presidio NLP layer)
├── renderers/
│   ├── pdf.py      # ReportLab renderer
│   ├── html.py     # Jinja2 renderer
│   ├── markdown.py
│   └── text.py
├── themes/
│   ├── dark.py     # Default theme
│   └── light.py
└── templates/
    └── conversation.html.j2
tests/
├── test_parser.py
├── test_privacy.py
└── fixtures/
    └── sample_conversation.txt
```

## Parser Architecture (Two-Pass)

**Pass 1 — Line Classification**

| Type | Pattern |
|------|---------|
| `USER_TURN` | Starts with `❯ ` |
| `ASST_TURN` | Starts with `● ` (not a tool call) |
| `TOOL_CALL` | Tool invocations: `● Fetch(`, `● Read `, `● Bash(`, etc. |
| `TOOL_OUTPUT` | Starts with `⎿` |
| `PROGRESS` | `✻ Cooked for ...`, `✻ Cogitated for ...` |
| `SYSTEM` | Header/footer ASCII art, structural blanks |
| `CONTINUATION` | Lines belonging to previous speaker |

**Pass 2 — Block Assembly**: Contiguous lines assembled into `Turn` dataclasses. TOOL_CALL, TOOL_OUTPUT, PROGRESS, SYSTEM are discarded unless `--verbose` is set.

```python
@dataclass
class Turn:
    speaker: Literal['assistant', 'user']
    paragraphs: list[str]
    speaker_label: str
```

## Theme Colors

**Dark (default)**:
- `page_bg = '#0d0d1a'`, `assistant_label = '#e94560'`, `user_label = '#f5a623'`
- `assistant_text = '#e0e0e0'`, `user_text = '#f0f0f0'`

**Light**:
- `page_bg = '#ffffff'`, `assistant_label = '#c0392b'`, `user_label = '#e67e22'`
- `assistant_text = '#2c3e50'`, `user_text = '#1a252f'`

## Privacy Mode (`--private`)

Two-layer redaction:
1. **Regex**: API keys (`sk-...`, `Bearer ...`) → `[REDACTED_KEY]`, SSNs, credit cards
2. **Presidio NLP**: PERSON → `[NAME]`, ORG → `[ORGANIZATION]`, LOC → `[LOCATION]`, EMAIL → `[EMAIL]`, PHONE → `[PHONE]`

Always emits a warning to stderr. Presidio is an optional install extra (`pip install convoformat[private]`).

## Development Milestones

1. **Core Parser + Text Output**: Parser, noise stripping, plain text renderer, CLI skeleton
2. **Markdown + PDF**: Both renderers, `--theme`, `--mobile` flags
3. **HTML + Light Theme**: Jinja2 renderer, light theme
4. **Privacy**: Presidio integration, `--private` flag, redaction tests
5. **Polish & Packaging**: `pyproject.toml`, README, edge cases, test fixtures

## Code Style Preferences

- Functional style with dataclasses and type hints throughout
- No unnecessary abstraction
- Inline comments where non-obvious; docstrings on public functions only
- Linux primary target, macOS secondary; Windows out of scope
