# ConvoFormatter

Convert raw Claude Code conversation transcripts (`.txt`) into clean, formatted documents — PDF, HTML, Markdown, or plain text. Strips tool calls, progress spinners, and other scaffolding noise automatically.

## Install

```bash
# Activate the existing virtualenv first
source .venv/bin/activate

# Install
pip install -e .

# With optional privacy/PII redaction support
pip install -e ".[private]"
python -m spacy download en_core_web_lg
```

## Usage

```
convoformat [OPTIONS] INPUT_FILE [OUTPUT_FILE]
```

If `OUTPUT_FILE` is omitted the result is written next to `INPUT_FILE` with the appropriate extension.

```bash
# Dark-theme mobile PDF (default)
convoformat Conversation.txt

# All options
convoformat Conversation.txt output/Conversation.pdf \
  --output=pdf \
  --theme=dark \
  --mobile \
  --assistant="Elliot" \
  --user="Stacey" \
  --title="Steves All the Way Down" \
  --date="2026-02-18"

# HTML for sharing
convoformat Conversation.txt --output=html --theme=dark

# Markdown for Obsidian
convoformat Conversation.txt --output=markdown --assistant="Elliot" --user="Stacey"

# Plain text
convoformat Conversation.txt --output=text

# Privacy-redacted (requires [private] extra)
convoformat Conversation.txt --output=html --private
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output`, `-o` | `pdf` | Output format: `pdf`, `html`, `markdown`, `text` |
| `--theme` | `dark` | Visual theme: `dark`, `light` (pdf and html only) |
| `--mobile` | off | Optimize layout for ~390pt mobile width |
| `--private` | off | Apply PII redaction (always prints a warning) |
| `--title` | auto | Override auto-detected title |
| `--date` | auto | Override auto-detected date |
| `--assistant` | `Assistant` | Label for AI speaker turns |
| `--user` | `User` | Label for human speaker turns |
| `--verbose` | off | Include tool calls and scaffolding in output |

`--theme` and `--mobile` are silently ignored for `markdown` and `text` formats (a notice is printed to stderr).

## Privacy Mode

`--private` runs two layers of redaction:
1. **Regex**: API keys, Bearer tokens, passwords, SSNs, credit card numbers
2. **Presidio NLP** (requires `[private]` extra): names, organizations, locations, emails, phone numbers

A warning with a redaction summary is always printed to stderr. Redaction is best-effort — always review output before sharing.

## Development

```bash
# Run tests
pytest

# Run a single test file
pytest tests/test_parser.py

# Lint
ruff check .
ruff check --fix .
```

## Architecture

```
convoformat/
├── cli.py          # Click entry point, orchestrates parse → redact → render
├── parser.py       # Two-pass parser: line classification → Turn assembly
├── privacy.py      # Regex + Presidio PII redaction
├── renderers/
│   ├── pdf.py      # ReportLab PDF with background color and styled turns
│   ├── html.py     # Jinja2 single-file HTML
│   ├── markdown.py # Plain Markdown
│   └── text.py     # Plain text
├── themes/
│   ├── dark.py     # Default dark theme
│   └── light.py    # Light theme
└── templates/
    └── conversation.html.j2
```

The parser produces `Turn(speaker, paragraphs, speaker_label)` objects. Scaffolding (tool calls, `⎿` output, `✻ ... for Xs` progress) is discarded in normal mode and included in `--verbose` mode.
