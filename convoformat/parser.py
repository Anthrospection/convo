"""Two-pass parser for Claude Code conversation transcripts.

Pass 1: classify each line and group into raw blocks.
Pass 2: assemble blocks into Turn dataclasses, discarding scaffolding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal


class LineType(Enum):
    USER_TURN = "user"
    ASST_TURN = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_OUTPUT = "tool_output"
    PROGRESS = "progress"
    CONTINUATION = "cont"


@dataclass
class Turn:
    speaker: Literal["assistant", "user"]
    paragraphs: list[str]
    speaker_label: str


@dataclass
class _Block:
    lt: LineType
    raw_lines: list[str] = field(default_factory=list)


# Tool calls: CamelCase( patterns, "Read filepath", "Searched for", ctrl+o UI indicator
_TOOL_CALL_RE = re.compile(
    r"^● ("
    r"[A-Z][a-zA-Z]+\("         # CamelCase( e.g. Bash(, Fetch(, Write(
    r"|Read\s"                   # Read <filepath>
    r"|Searched\b"               # Searched for...
    r")"
)
_PROGRESS_RE = re.compile(r"^✻ .+ for \d+")
_TOOL_OUTPUT_RE = re.compile(r"^\s*⎿")


_SLASH_CMD_RE = re.compile(r"^❯ /\w")


def _classify(line: str) -> LineType:
    if line.startswith("❯ "):
        if _SLASH_CMD_RE.match(line):
            return LineType.TOOL_CALL  # /rename, /help, /clear, etc. — treat as noise
        return LineType.USER_TURN
    if line.startswith("● "):
        if _TOOL_CALL_RE.match(line) or "ctrl+o" in line.lower():
            return LineType.TOOL_CALL
        return LineType.ASST_TURN
    if _TOOL_OUTPUT_RE.match(line):
        return LineType.TOOL_OUTPUT
    if _PROGRESS_RE.match(line.strip()):
        return LineType.PROGRESS
    return LineType.CONTINUATION


def _paragraphize(raw_lines: list[str]) -> list[str]:
    """Assemble raw lines into paragraphs, splitting on blank lines.

    Lines are joined with spaces within a paragraph to undo terminal word-wrap.
    '---' divider lines become their own single-item paragraph for renderers to handle.
    """
    paragraphs: list[str] = []
    current: list[str] = []

    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
        elif stripped == "---":
            if current:
                paragraphs.append(" ".join(current))
                current = []
            paragraphs.append("---")
        else:
            current.append(stripped)

    if current:
        paragraphs.append(" ".join(current))

    return [p for p in paragraphs if p]


_NOISE_TYPES = {LineType.TOOL_CALL, LineType.TOOL_OUTPUT, LineType.PROGRESS}
_BLOCK_START_TYPES = {LineType.USER_TURN, LineType.ASST_TURN, LineType.TOOL_CALL}


def parse(
    path: Path,
    assistant_label: str = "Assistant",
    user_label: str = "User",
    verbose: bool = False,
) -> list[Turn]:
    """Parse a Claude Code transcript file into a list of Turn objects.

    Scaffolding (tool calls, tool output, progress) is discarded unless verbose=True.
    Lines before the first speaker turn (ASCII art header) are silently ignored.
    """
    text = path.read_text(encoding="utf-8")
    raw_lines = text.splitlines()

    # Pass 1: group lines into blocks
    blocks: list[_Block] = []
    current: _Block | None = None

    for line in raw_lines:
        lt = _classify(line)

        if lt in _BLOCK_START_TYPES:
            current = _Block(lt=lt, raw_lines=[line[2:]])  # strip "❯ " or "● "
            blocks.append(current)

        elif lt in (LineType.TOOL_OUTPUT, LineType.PROGRESS):
            # Only append to noise blocks (tool calls); discard if attached to a speaker turn
            if current is not None and current.lt in _NOISE_TYPES:
                current.raw_lines.append(line)

        else:  # CONTINUATION
            if current is not None:
                current.raw_lines.append(line)
            # else: pre-conversation header lines — discard

    # Pass 2: assemble into Turn objects
    turns: list[Turn] = []

    for block in blocks:
        if block.lt in _NOISE_TYPES and not verbose:
            continue

        speaker: Literal["assistant", "user"] = (
            "user" if block.lt == LineType.USER_TURN else "assistant"
        )
        label = user_label if speaker == "user" else assistant_label

        paragraphs = _paragraphize(block.raw_lines)
        if paragraphs:
            turns.append(Turn(speaker=speaker, paragraphs=paragraphs, speaker_label=label))

    return turns


def detect_title(path: Path, turns: list[Turn], head: list[str] | None = None) -> str:
    """Infer a title from the transcript, falling back to the filename stem."""
    # Look for a session notes title in the first 30 lines
    text_head = head if head is not None else path.read_text(encoding="utf-8").splitlines()[:30]
    for line in text_head:
        m = re.match(r"^#\s+(.+)", line.strip())
        if m:
            return m.group(1).strip()

    # Fall back to filename stem, title-cased
    stem = path.stem.replace("_", " ").replace("-", " ")
    return stem.title()


def detect_date(path: Path, head: list[str] | None = None) -> str:
    """Extract a date from the transcript, falling back to file modification time."""
    import datetime

    text_head = head if head is not None else path.read_text(encoding="utf-8").splitlines()[:30]

    # ISO date pattern: YYYY-MM-DD
    iso_re = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
    for line in text_head:
        m = iso_re.search(line)
        if m:
            return m.group(1)

    # Written date: "Month DD, YYYY"
    written_re = re.compile(
        r"\b(January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{1,2},?\s+\d{4}\b"
    )
    for line in text_head:
        m = written_re.search(line)
        if m:
            return m.group(0)

    # Fall back to file mtime
    mtime = path.stat().st_mtime
    return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
