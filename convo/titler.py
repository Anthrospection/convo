"""Title generation using a local Ollama model."""

from __future__ import annotations

import json
import subprocess

from convo.parser import Turn

_DEFAULT_MODEL = "gemma3:27b"

_PROMPT = """You are a title generator. Given the opening of a conversation, produce a short,
descriptive title (3-8 words). The title should capture the main topic or theme,
not be generic. Do not use quotes. Do not explain. Just output the title.

Conversation:
{conversation}

Title:"""


def _turns_to_text(turns: list[Turn], max_chars: int = 3000) -> str:
    """Convert turns to plain text, truncated to max_chars."""
    lines: list[str] = []
    total = 0
    for turn in turns:
        label = turn.speaker_label
        for para in turn.paragraphs:
            if para == "---":
                continue
            line = f"{label}: {para}"
            if total + len(line) > max_chars:
                return "\n".join(lines)
            lines.append(line)
            total += len(line)
    return "\n".join(lines)


def generate_title(
    turns: list[Turn],
    model: str = _DEFAULT_MODEL,
) -> str | None:
    """Generate a title from conversation turns using Ollama.

    Returns the generated title, or None if generation fails.
    """
    conversation = _turns_to_text(turns)
    if not conversation.strip():
        return None

    prompt = _PROMPT.format(conversation=conversation)

    try:
        result = subprocess.run(
            [
                "ollama", "run", model,
                "--nowordwrap",
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            title = result.stdout.strip()
            # Clean up: remove quotes, trailing periods, extra whitespace
            title = title.strip('"\'').strip(".").strip()
            # Take only the first line if model got chatty
            title = title.split("\n")[0].strip()
            if title:
                return title
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None
