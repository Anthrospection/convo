# ConvoFormat — Product Requirements Document

**Version**: 1.0  
**Date**: 2026-02-19  
**Author**: Stacey (with Claude)  
**Status**: Ready for Development

---

## Executive Summary

ConvoFormat is a command-line tool that takes a raw conversation transcript (initially targeting Claude Code `.txt` exports, but extensible to other formats) and produces a clean, beautifully formatted output document suitable for reading, archiving, or sharing.

The tool handles two distinct concerns cleanly:

1. **Content cleaning**: Strips scaffolding noise (tool calls, file read confirmations, progress spinners, etc.) and optionally redacts personally identifiable information.
2. **Output formatting**: Renders the cleaned conversation in a chosen format with appropriate visual treatment — dark/light themes, mobile-optimized layouts, speaker labeling, and metadata headers.

The primary use case is an integration specialist and AI power user who generates rich, meaningful conversations with a persistent AI agent (Elliot, a customized Claude Code instance) and wants to archive and share them in a form that does justice to the content — not a raw terminal dump.

---

## Problem Statement

Claude Code conversation exports are plain text files containing the full terminal session: the actual dialogue interspersed with tool invocations, file read confirmations, progress indicators (`✻ Cooked for 40s`), and other scaffolding artifacts. This raw format is:

- Difficult to read on a phone or tablet
- Visually undifferentiated between speaker turns
- Cluttered with noise irrelevant to the conversation itself
- Unsuitable for sharing with others unfamiliar with Claude Code's interface

There is currently no tool that handles this specific cleaning + formatting pipeline in a scriptable, repeatable way with sensible defaults and flexible options.

---

## Target User

**Primary**: A solo technical user (developer/integration specialist) who:
- Generates long, substantive AI conversations worth preserving
- Works across multiple machines (Linux desktop, possibly macOS)
- Is comfortable with CLI tools and Python
- Wants outputs that look good in dark mode on mobile
- May occasionally want to share transcripts with privacy redaction applied
- Runs a local AI setup (Obsidian vault, NAS, Claude Code customizations)

**Secondary** (future): Other Claude Code or AI power users with similar archiving needs.

---

## Core User Journey

```
1. User has a raw conversation .txt file from Claude Code
2. User runs: convoformat input.txt --output=pdf --theme=dark --mobile
3. Tool parses the file, strips noise, applies formatting
4. Tool writes the output file (same name, different extension) or user-specified name
5. User optionally opens, shares, or archives the result
```

---

## Feature Requirements

### MVP Features (Must Have)

| # | Feature | Description | Acceptance Criteria |
|---|---------|-------------|---------------------|
| 1 | **Input parsing** | Read Claude Code `.txt` format; identify speaker turns (Stacey `❯`, Elliot/assistant `●`, system/scaffolding) | All three turn types correctly identified across a full conversation file |
| 2 | **Noise stripping** | Remove tool invocations, `⎿` output lines, progress spinners (`✻ ... for Xs`), file path confirmations, redundant status messages | Cleaned content contains only actual conversation text |
| 3 | **PDF output** | Produce a styled PDF with speaker labels, readable typography, metadata header | PDF renders correctly in iOS/Android PDF viewers |
| 4 | **HTML output** | Produce a self-contained HTML file (single file, no external deps) with equivalent styling | Opens correctly offline in mobile browser |
| 5 | **Markdown output** | Produce clean Markdown with speaker labels and minimal formatting | Valid Markdown, readable in Obsidian |
| 6 | **Plain text output** | Produce clean plain text with speaker labels and line separators | UTF-8, no binary artifacts |
| 7 | **Dark/light theme** | Apply to PDF and HTML. Dark default. Ignored (with notice) for markdown/text | Visual difference clearly apparent between themes |
| 8 | **Mobile layout** | Narrow column width, larger base font, increased line height for PDF and HTML | Comfortable reading on a 390px-wide screen without zooming |
| 9 | **`--private` flag** | Redact/replace PII: full names, employer names, financial info, healthcare info, apparent passwords/API keys. Issue warning with uncertainty disclosure | No obvious PII in output; warning shown if redaction confidence is < 100% |
| 10 | **`--title` override** | Replace auto-generated title with user-specified string | Title appears correctly in output |
| 11 | **`--date` override** | Replace auto-detected date with user-specified value | Date appears correctly in output |
| 12 | **`--assistant` override** | Replace default "Assistant" speaker label with user-specified name (e.g., "Elliot") | Label used consistently throughout output |
| 13 | **`--user` override** | Replace default "User" speaker label with user-specified name (e.g., "Stacey") | Label used consistently throughout output |
| 14 | **Auto-title detection** | If `--title` not specified, attempt to infer a title from first substantive Elliot response or first topic mentioned | Reasonable default title in most cases; graceful fallback to filename stem |
| 15 | **Auto-date detection** | Extract date from conversation content (Claude Code header or first timestamp found); fall back to file mtime | Date present in output header without user needing to specify it |

### Phase 2 Features (Should Have)

| Feature | Description | Why Deferred |
|---------|-------------|--------------|
| `--custom-theme` | Accept a JSON/YAML theme definition (colors, fonts, spacing) | Adds config schema complexity; dark/light covers most cases first |
| Multiple input files | Accept a glob or list of files; batch process | Single-file MVP is the primary use case |
| Session Notes appendix | Auto-generate a brief summary section at the end (what was discussed, key decisions) | Requires LLM call; out of scope for pure formatting tool |
| EPUB output | For longer conversations / reading in e-readers | Niche; lower priority than HTML |
| `--format=auto` detection | Detect input format automatically (Claude Code, ChatGPT export, etc.) | Requires format sniffers; Claude Code format first |
| Config file | `~/.convoformat.toml` for default options | Convenience feature; CLI flags sufficient for MVP |

### Future Considerations (Nice to Have)

- GUI wrapper (drag-and-drop interface)
- Integration as a Claude Code hook (auto-runs after session end)
- Direct Obsidian vault output with frontmatter YAML
- Syntax highlighting for code blocks within conversation
- `--from-stdin` for pipeline usage
- ChatGPT / Gemini export format support

### Explicitly Out of Scope (MVP)

- Real-time / streaming processing
- Web service / API version
- Image or media handling within transcripts
- Actual LLM calls for summarization (this is a formatting tool, not a summarization tool)
- GUI application
- Windows support (Linux and macOS only for now)

---

## Technical Architecture

### Technology Stack

- **Language**: Python 3.10+
- **PDF generation**: `reportlab` (already validated in prototype)
- **HTML generation**: Jinja2 template + inline CSS (single-file output)
- **Markdown/Text**: Standard library string processing
- **PII redaction**: `presidio-analyzer` + `presidio-anonymizer` (Microsoft's open-source NLP-based PII detection), with a custom rule layer for API keys / passwords
- **CLI interface**: `argparse` or `click` (click preferred for cleaner help output)
- **Packaging**: Single installable script; optionally `pip install`-able

### Dependencies

```
click
reportlab
jinja2
presidio-analyzer
presidio-anonymizer
spacy  (required by presidio; en_core_web_lg model)
```

### Project Structure

```
convoformat/
├── convoformat/
│   ├── __init__.py
│   ├── cli.py              # Entry point, argument parsing
│   ├── parser.py           # Input format parsing, noise stripping
│   ├── privacy.py          # PII detection and redaction
│   ├── renderers/
│   │   ├── __init__.py
│   │   ├── pdf.py          # ReportLab PDF renderer
│   │   ├── html.py         # Jinja2 HTML renderer
│   │   ├── markdown.py     # Markdown renderer
│   │   └── text.py         # Plain text renderer
│   ├── themes/
│   │   ├── dark.py         # Dark theme color/font definitions
│   │   └── light.py        # Light theme color/font definitions
│   └── templates/
│       └── conversation.html.j2   # HTML output template
├── tests/
│   ├── test_parser.py
│   ├── test_privacy.py
│   └── fixtures/
│       └── sample_conversation.txt
├── pyproject.toml
└── README.md
```

### Parser Logic

The parser operates in two passes:

**Pass 1 — Line classification**  
Each line is tagged as one of:
- `STACEY_TURN`: lines beginning with `❯ ` 
- `ASSISTANT_TURN`: lines beginning with `● ` (excluding tool invocations)
- `TOOL_CALL`: `● Fetch(`, `● Read `, `● Write(`, `● Update(`, `● Bash(`, `● Web Search(`, `● Searched`, etc.
- `TOOL_OUTPUT`: lines beginning with `⎿`
- `PROGRESS`: lines matching `✻ .+ for \d+[smh]` or `✻ (Cooked|Baked|Brewed|Cogitated|Sautéed|Crunched|Worked) for`
- `SYSTEM`: header/footer art, blank dividers
- `CONTINUATION`: lines belonging to the current open turn

**Pass 2 — Block assembly**  
Contiguous tagged lines are assembled into `Turn` objects:
```python
@dataclass
class Turn:
    speaker: Literal['assistant', 'user', 'system']
    paragraphs: list[str]
    raw_label: str  # e.g., "●", "❯"
```

Scaffolding turns (TOOL_CALL, TOOL_OUTPUT, PROGRESS, SYSTEM) are discarded unless `--verbose` flag is set.

### PII Redaction (--private)

Redaction runs after parsing, before rendering, on the assembled `Turn` objects.

**Detection layers** (in order):
1. **Regex layer**: API keys (`sk-...`, `Bearer ...`), passwords (heuristic patterns), SSNs, credit card numbers
2. **Presidio NLP layer**: Names (PERSON), organizations (ORG), locations (LOC/GPE), dates that could be identifying, medical terms in context, financial account references
3. **Custom rule layer**: Employer names from a small configurable list (e.g., "Emory Healthcare", "Emory" → `[EMPLOYER]`), known location names

**Replacement strategy**:
- PERSON → `[NAME]`
- ORG/EMPLOYER → `[ORGANIZATION]`
- LOC → `[LOCATION]`
- API_KEY → `[REDACTED_KEY]`
- PASSWORD → `[REDACTED_PASSWORD]`
- Medical/health context → `[HEALTH_INFO]`

**Warning behavior**:
- Always print a warning when `--private` is used, regardless of confidence
- If any uncertain redactions occurred (Presidio confidence < 0.75): print a list of the uncertain spans with their replacement
- Suggested warning text:
  ```
  ⚠  Privacy mode active. PII redaction applied.
     Reviewed and redacted: 4 entities (PERSON x2, ORG x1, LOC x1)
     Low-confidence redactions (verify manually): 2 items flagged
     This tool makes a good-faith effort but cannot guarantee completeness.
     Review the output before sharing.
  ```

### Theme Definitions

Each theme is a dataclass of color values, font choices, and spacing constants. Example (dark):

```python
@dataclass
class DarkTheme:
    page_bg = '#0d0d1a'
    assistant_label_color = '#e94560'   # accent red
    user_label_color = '#f5a623'        # gold
    assistant_text_color = '#e0e0e0'
    user_text_color = '#f0f0f0'
    system_text_color = '#555566'
    title_color = '#f5a623'
    hr_color = '#e94560'
    font_body = 'Helvetica'
    font_code = 'Courier'
    font_size_body = 10
    font_size_mobile_body = 11
    line_height = 1.5
```

---

## CLI Interface

### Usage

```
convoformat [OPTIONS] INPUT_FILE [OUTPUT_FILE]
```

If `OUTPUT_FILE` is omitted, the output file is written to the same directory as `INPUT_FILE` with the appropriate extension (e.g., `Conversation.txt` → `Conversation.pdf`).

### Options

```
--output FORMAT     Output format: pdf, html, markdown, text
                    Default: pdf

--theme THEME       Visual theme: dark, light
                    Default: dark
                    Applies to: pdf, html
                    Ignored for: markdown, text (with notice)

--mobile            Optimize layout for mobile screen width (~390pt)
                    Applies to: pdf, html
                    Ignored for: markdown, text (with notice)

--private           Apply PII redaction. Always prints a warning.
                    See Privacy section for details.

--title TEXT        Override auto-detected title

--date TEXT         Override auto-detected date

--assistant TEXT    Label for AI speaker turns
                    Default: "Assistant"

--user TEXT         Label for human speaker turns
                    Default: "User"

--verbose           Include tool calls and scaffolding in output
                    (disabled by default)

--version           Show version and exit
--help              Show this message and exit
```

### Examples

```bash
# Quick PDF with defaults
convoformat Conversation.txt

# Mobile-optimized dark PDF with custom labels
convoformat Conversation.txt \
  --output=pdf --theme=dark --mobile \
  --assistant="Elliot" --user="Stacey" \
  --title="System Cards and Steves"

# Privacy-redacted HTML for sharing
convoformat Conversation.txt \
  --output=html --private \
  --assistant="AI" --user="User"

# Clean Markdown for Obsidian vault
convoformat Conversation.txt \
  --output=markdown \
  --assistant="Elliot" --user="Stacey" \
  --title="System Cards and Steves" \
  --date="2026-02-18"

# Plain text
convoformat Conversation.txt --output=text
```

---

## User Experience

### Design Principles

1. **Sensible defaults**: Running with no options other than the input file should produce a good result — dark theme, mobile-optimized PDF, auto-detected title and date, generic speaker labels.
2. **Noise by default**: Scaffolding is stripped silently. `--verbose` restores it for users who want it.
3. **Honest privacy**: `--private` always warns. It never silently implies success.
4. **Fail gracefully**: Unknown or ambiguous lines are treated as continuation of the current speaker turn, not dropped. A `--debug` flag can expose classification decisions.
5. **Fast**: Should process a 1000-line conversation in under 5 seconds on any modern machine.

### Output Format Behavior Summary

| Flag/Option | PDF | HTML | Markdown | Text |
|-------------|-----|------|----------|------|
| `--theme` | ✅ | ✅ | ❌ notice | ❌ notice |
| `--mobile` | ✅ | ✅ | ❌ notice | ❌ notice |
| `--private` | ✅ | ✅ | ✅ | ✅ |
| `--title` | ✅ | ✅ | ✅ | ✅ |
| `--date` | ✅ | ✅ | ✅ | ✅ |
| `--assistant` | ✅ | ✅ | ✅ | ✅ |
| `--user` | ✅ | ✅ | ✅ | ✅ |

"Notice" = option is acknowledged but silently ignored for that output format, with a brief `[notice]` line printed to stderr.

---

## Data Portability

- **Input**: Plain text `.txt` files (UTF-8). No proprietary formats.
- **Output**: Open formats only (PDF, HTML, Markdown, plain text). No lock-in.
- **No persistent state**: The tool is stateless. No database, no config files required for MVP. Each run is independent.

---

## Development Plan

### Milestone 1 — Core Parser + Text Output
- Input parser with turn classification
- Noise stripping
- Plain text renderer
- CLI skeleton with `--assistant`, `--user`, `--title`, `--date`

### Milestone 2 — Markdown + PDF
- Markdown renderer
- PDF renderer (dark theme, mobile layout)
- `--output`, `--theme`, `--mobile` flags

### Milestone 3 — HTML + Light Theme
- Jinja2 HTML renderer (self-contained, single file)
- Light theme definitions
- Cross-format theme application

### Milestone 4 — Privacy
- Presidio integration
- Regex layer for keys/passwords
- `--private` flag with warning output
- Test suite for redaction accuracy

### Milestone 5 — Polish & Packaging
- `pyproject.toml` + pip installable
- README with usage examples
- Edge case handling (empty files, single-speaker conversations, Unicode)
- Test fixtures from real conversation samples

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Presidio spaCy model size (~500MB) | Slow install, heavy dependency | Make `--private` an optional install extra: `pip install convoformat[private]` |
| ReportLab font rendering on Linux vs macOS | Visual inconsistency | Test on both; fall back to Helvetica/Courier (always available) |
| Claude Code format changes in future versions | Parser breaks | Design parser with explicit format version detection; log unrecognized patterns |
| PII false negatives | User believes output is clean when it isn't | Warning always shown; no claim of completeness |

### Open Questions

1. Should the default output filename follow the input filename stem, or should auto-title detection name the file too?
2. For `--private`, should the original PII text be logged somewhere (encrypted? local only?) or just silently replaced?
3. Long-term: should this be a Claude Code hook that runs automatically at session end?

---

## Appendix

### Glossary

| Term | Definition |
|------|-----------|
| Turn | A single continuous block of text from one speaker |
| Scaffolding | Tool calls, file confirmations, progress spinners — the non-conversational operational output of Claude Code |
| Noise stripping | The process of removing scaffolding from the transcript |
| Speaker label | The name used to identify a turn's author in the output (e.g., "Elliot", "Stacey") |
| PII | Personally Identifiable Information — names, locations, employer names, credentials, health/financial data |

### Reference Materials

- Prototype PDF script: generated during the `System Cards and Steves` conversation formatting session (2026-02-18)
- ReportLab docs: https://www.reportlab.com/docs/reportlab-userguide.pdf
- Presidio docs: https://microsoft.github.io/presidio/
- Sample input: `Conversation.txt` (the System Cards and Steves session)

---

# Claude Code Kickoff Prompt

> Copy everything below this line into a fresh Claude Code session to begin implementation.

---

## ConvoFormat — Development Kickoff

You are building **ConvoFormat**, a Python CLI tool that takes raw Claude Code conversation transcript files (`.txt`) and produces clean, beautifully formatted output documents in PDF, HTML, Markdown, or plain text.

This prompt contains everything you need to implement the MVP autonomously.

---

### What You're Building

A command-line tool invoked as:

```bash
convoformat [OPTIONS] INPUT_FILE [OUTPUT_FILE]
```

It does two things:
1. **Parses and cleans** a Claude Code conversation transcript — stripping tool calls, file operation confirmations, progress spinners, and other scaffolding
2. **Renders** the cleaned conversation in a user-chosen format with visual polish appropriate for reading on a phone or sharing

---

### User's Technical Preferences

- **OS**: Linux (primary), macOS (secondary)
- **Language**: Python 3.10+
- **Style**: Functional where possible, dataclasses for structured data, type hints throughout
- **CLI**: `click` preferred over `argparse`
- **No unnecessary abstraction**: Build what's needed, not a framework
- **Comments**: Inline where non-obvious; docstrings on public functions

---

### Technology Stack

- Runtime: Python 3.10+
- CLI: `click`
- PDF: `reportlab`
- HTML: `jinja2` (single-file output, inline CSS)
- PII redaction: `presidio-analyzer`, `presidio-anonymizer`, `spacy`
- Packaging: `pyproject.toml`

---

### Project Structure

```
convoformat/
├── convoformat/
│   ├── __init__.py
│   ├── cli.py
│   ├── parser.py
│   ├── privacy.py
│   ├── renderers/
│   │   ├── __init__.py
│   │   ├── pdf.py
│   │   ├── html.py
│   │   ├── markdown.py
│   │   └── text.py
│   ├── themes/
│   │   ├── __init__.py
│   │   ├── dark.py
│   │   └── light.py
│   └── templates/
│       └── conversation.html.j2
├── tests/
│   ├── test_parser.py
│   ├── test_privacy.py
│   └── fixtures/
│       └── sample_conversation.txt
├── pyproject.toml
└── README.md
```

---

### CLI Interface

```
--output    FORMAT   pdf | html | markdown | text   (default: pdf)
--theme     THEME    dark | light                   (default: dark, pdf/html only)
--mobile             narrow layout for phone        (pdf/html only)
--private            PII redaction with warning
--title     TEXT     override auto-detected title
--date      TEXT     override auto-detected date
--assistant TEXT     label for AI turns             (default: "Assistant")
--user      TEXT     label for human turns          (default: "User")
--verbose            include scaffolding in output
```

For flags inapplicable to the chosen output format (e.g., `--theme` with `--output=markdown`), print a brief notice to stderr and continue.

---

### Parser: Turn Classification

Classify each line as one of these types:

```python
class LineType(Enum):
    USER_TURN    = "user"        # starts with "❯ "
    ASST_TURN    = "assistant"   # starts with "● " and is NOT a tool call
    TOOL_CALL    = "tool_call"   # "● Fetch(", "● Read ", "● Write(", "● Update(",
                                 # "● Bash(", "● Web Search(", "● Searched",
                                 # "● Found it", "● Got it", "● Done.", etc.
    TOOL_OUTPUT  = "tool_output" # starts with "⎿" or "  ⎿"
    PROGRESS     = "progress"    # matches: ✻ .+ for \d+[smh]
                                 # e.g. "✻ Cooked for 40s", "✻ Cogitated for 1m 46s"
    SYSTEM       = "system"      # ASCII art header, blank structural lines
    CONTINUATION = "cont"        # belongs to current open turn
```

Assemble into `Turn` dataclass:
```python
@dataclass
class Turn:
    speaker: Literal['assistant', 'user']
    paragraphs: list[str]       # split on double-newline within turn
    speaker_label: str          # resolved from --assistant / --user flags
```

Discard TOOL_CALL, TOOL_OUTPUT, PROGRESS, SYSTEM turns unless `--verbose`.

---

### Theme Definitions

**Dark theme** (default):
```python
page_bg            = '#0d0d1a'
assistant_label    = '#e94560'   # red-accent
user_label         = '#f5a623'   # gold
assistant_text     = '#e0e0e0'
user_text          = '#f0f0f0'
system_text        = '#555566'
title_color        = '#f5a623'
hr_color           = '#e94560'
subtitle_color     = '#888888'
```

**Light theme**:
```python
page_bg            = '#ffffff'
assistant_label    = '#c0392b'
user_label         = '#e67e22'
assistant_text     = '#2c3e50'
user_text          = '#1a252f'
system_text        = '#95a5a6'
title_color        = '#2c3e50'
hr_color           = '#c0392b'
subtitle_color     = '#7f8c8d'
```

---

### PDF Renderer

Use `reportlab.platypus`. Mobile layout: `pagesize=(390, 700)` points, margins 12mm. Desktop default: A4 portrait, margins 20mm.

Structure:
1. Title block (title, subtitle "A Conversation", speaker names, date)
2. Horizontal rule
3. Brief italic description block (auto-generated or from first topic)
4. Horizontal rule
5. Conversation turns (speaker label + body paragraphs)
6. Footer rule + closing quote (last memorable line, if detectable)

Turn rendering:
- Assistant label: `"● {assistant_name}"` in accent color, bold, 9pt
- User label: `"❯ {user_name}"` in gold, bold, 9pt
- Body: 10pt (11pt mobile), leading 1.5, appropriate text color
- Spacer between turns

Page background: Use `onFirstPage` / `onLaterPages` canvas hook to fill background color.

---

### HTML Renderer

Single self-contained `.html` file. All CSS inline in `<style>` block. No external dependencies. Mobile-first when `--mobile` flag set (use `max-width: 390px` and `font-size: 16px` base).

Use Jinja2 template at `templates/conversation.html.j2`.

Include:
- Full dark/light CSS variables
- Responsive meta viewport tag
- Same structural layout as PDF (title, hr, turns, footer)
- Speaker labels styled as colored badges/prefixes
- Clean sans-serif typography (system font stack)

---

### Markdown Renderer

```markdown
# {title}

*{date} · {assistant_name} & {user_name}*

---

**❯ {user_name}**

{turn text}

---

**● {assistant_name}**

{turn text}

---
```

No themes, no colors — just clean structure.

---

### Plain Text Renderer

```
=== {title} ===
{date}

[{USER_NAME}]
{turn text}

[{ASSISTANT_NAME}]
{turn text}

---
```

---

### PII Redaction (--private)

Run after parsing, before rendering. Two layers:

**Layer 1 — Regex** (run first):
- API keys: `(sk-[a-zA-Z0-9]{20,})|(Bearer [a-zA-Z0-9\-._~+/]+=*)` → `[REDACTED_KEY]`
- Passwords: `password\s*[:=]\s*\S+` (case-insensitive) → `[REDACTED_PASSWORD]`
- SSN: `\b\d{3}-\d{2}-\d{4}\b` → `[REDACTED_SSN]`

**Layer 2 — Presidio NLP**:
- Entities: PERSON → `[NAME]`, ORG → `[ORGANIZATION]`, GPE/LOC → `[LOCATION]`, CREDIT_CARD → `[REDACTED]`, PHONE_NUMBER → `[PHONE]`, EMAIL_ADDRESS → `[EMAIL]`, MEDICAL_LICENSE → `[HEALTH_ID]`

**Warning output** (always, to stderr):
```
⚠  Privacy mode active (--private)
   Redacted entities: {count} ({breakdown by type})
   Low-confidence items: {n} — manual review recommended
   This tool makes a good-faith effort but cannot guarantee completeness.
   Always review output before sharing.
```

Make presidio an optional install extra:
```toml
[project.optional-dependencies]
private = ["presidio-analyzer", "presidio-anonymizer", "spacy"]
```

If `--private` is used without the extra installed, print a clear error with install instructions.

---

### Auto-detection Logic

**Title detection** (when `--title` not specified):
1. Look for a Claude Code session notes title pattern in the text
2. Extract the first substantive noun phrase from the first assistant turn > 50 chars
3. Fall back to: stem of input filename, title-cased, underscores replaced with spaces

**Date detection** (when `--date` not specified):
1. Look for ISO date patterns in the first 20 lines (`\d{4}-\d{2}-\d{2}`)
2. Look for written dates ("February 18, 2026")
3. Fall back to: file modification time, formatted as `YYYY-MM-DD`

---

### Core Feature Implementation Order

**Milestone 1** — CLI skeleton + parser + text output
- [ ] `pyproject.toml` with dependencies
- [ ] `cli.py` with all flags defined (can be stubs initially)
- [ ] `parser.py` — full turn classification and assembly
- [ ] `renderers/text.py` — plain text output
- [ ] End-to-end: `convoformat input.txt --output=text` works

**Milestone 2** — Markdown + PDF
- [ ] `renderers/markdown.py`
- [ ] `themes/dark.py` and `themes/light.py`
- [ ] `renderers/pdf.py` — dark theme, mobile layout
- [ ] `--mobile`, `--theme`, `--output=pdf/markdown` flags wired up

**Milestone 3** — HTML
- [ ] `templates/conversation.html.j2`
- [ ] `renderers/html.py`
- [ ] Light theme applied to HTML and PDF

**Milestone 4** — Privacy
- [ ] `privacy.py` — regex layer
- [ ] Presidio integration as optional extra
- [ ] `--private` flag wired up with warning output

**Milestone 5** — Polish
- [ ] Auto-title and auto-date detection
- [ ] Edge cases: empty input, single-speaker, Unicode handling
- [ ] `README.md`
- [ ] Test suite with sample fixture

---

### Definition of Done

The MVP is complete when:
- [ ] `convoformat Conversation.txt` produces a dark-theme mobile PDF with stripped scaffolding
- [ ] All four output formats work end-to-end
- [ ] `--private` runs with correct warning output
- [ ] All CLI flags work and inapplicable flags produce notices, not errors
- [ ] Installs cleanly with `pip install -e .` on Linux
- [ ] README documents all flags with examples

---

### Getting Started

1. Create the project structure
2. Write `pyproject.toml`
3. Implement `parser.py` — this is the core; get it right first
4. Wire up `cli.py` with click
5. Implement `renderers/text.py` for a fast first end-to-end test
6. Then proceed through the milestones in order

Begin by creating the project structure and `pyproject.toml`, then implement `parser.py`.
