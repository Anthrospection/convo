# CLAUDE.md

Project guidance for Claude Code when working in this repository.

## Overview

**convo** is a Python CLI tool that converts raw Claude Code conversation transcripts into formatted documents (PDF, HTML, Markdown, plain text). It strips scaffolding noise and renders clean, readable output.

## Stack

- **Language**: Python 3.13+
- **CLI**: click
- **PDF**: reportlab
- **HTML**: Jinja2 templates (single-file, self-contained)
- **PII**: presidio (optional extra)
- **Config**: PyYAML
- **Packaging**: pyproject.toml + hatchling

## Commands

```bash
# Run without installing
uv run convo INPUT_FILE [OUTPUT_FILE] [OPTIONS]

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

## Architecture

```
convo/
├── cli.py          # Click entry point, config loading
├── parser.py       # Two-pass transcript parser
├── references.py   # YouTube URL extraction + yt-dlp metadata
├── titler.py       # Ollama-based title generation
├── privacy.py      # PII redaction (regex + presidio)
├── renderers/
│   ├── pdf.py      # ReportLab
│   ├── html.py     # Jinja2
│   ├── markdown.py
│   └── text.py
├── themes/
│   ├── dark.py
│   └── light.py
└── templates/
    └── conversation.html.j2
```

## Parser

Two-pass design:
1. **Classify** each line (USER_TURN, ASST_TURN, TOOL_CALL, TOOL_OUTPUT, PROGRESS, CONTINUATION)
2. **Assemble** into Turn dataclasses, discarding noise unless `--verbose`

## Code Style

- Type hints throughout
- Minimal abstraction
- No unnecessary comments
- Linux primary, macOS secondary
