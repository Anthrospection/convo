# convo

Save conversations as clean, formatted documents.

**convo** converts raw Claude Code conversation transcripts into readable Markdown, HTML, PDF, or plain text — stripping tool calls, progress spinners, and scaffolding noise.

## Install

```bash
# Clone and run with uv (no install needed)
git clone https://github.com/Anthrospection/convo.git
cd convo
uv run convo examples/basic.txt output.md

# Or install globally
pip install .
convo examples/basic.txt output.md
```

## Usage

```bash
# Markdown (default)
convo transcript.txt

# HTML with dark theme
convo transcript.txt output.html -o html

# PDF
convo transcript.txt output.pdf -o pdf

# With custom speaker labels
convo transcript.txt --assistant "Claude" --user "Alex"

# With YouTube references (resolves title, channel, duration)
convo transcript.txt --ref "https://youtube.com/watch?v=VIDEO_ID"

# Skip AI title generation
convo transcript.txt --no-ai
```

## Features

- **Noise stripping**: Tool calls, progress lines (`✻ Baked for 43s`), slash commands, and scaffolding are removed automatically
- **Speaker labels**: Configurable names for AI and human turns
- **YouTube references**: `--ref` flag resolves video metadata via yt-dlp and appends a References section
- **AI title generation**: When no title is provided, generates one using a local Ollama model
- **Themes**: Dark (default) and light themes for HTML and PDF output
- **Mobile layout**: `--mobile` flag optimizes PDF/HTML for phone screens
- **PII redaction**: `--private` flag redacts names, keys, SSNs, and other PII
- **Config file**: Set defaults in `~/.config/convo/config.yaml`

## Config

Create `~/.config/convo/config.yaml` to set defaults:

```yaml
assistant: Claude
user: Alex
output: markdown
theme: dark
```

CLI flags always override config values.

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o`, `--output` | Format: markdown, html, pdf, text | markdown |
| `--theme` | dark or light (html/pdf only) | dark |
| `--mobile` | Mobile-optimized layout | off |
| `--private` | PII redaction | off |
| `--title TEXT` | Override auto-generated title | auto |
| `--date TEXT` | Override auto-detected date | auto |
| `--assistant TEXT` | AI speaker label | Assistant |
| `--user TEXT` | Human speaker label | User |
| `--ref URL` | Add reference URL (repeatable) | none |
| `--no-ai` | Skip local model features | off |
| `--verbose` | Include tool calls in output | off |

## Input Format

convo parses Claude Code terminal output. It expects:
- `❯ ` prefix for user turns
- `● ` prefix for assistant turns
- Standard Claude Code scaffolding (tool calls, progress, etc.)

## Requirements

- Python 3.13+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (for `--ref` YouTube resolution)
- [Ollama](https://ollama.ai) with a model like gemma3:27b (for title generation)

Optional:
```bash
pip install convo[private]  # PII redaction (presidio + spacy)
```

## License

MIT
