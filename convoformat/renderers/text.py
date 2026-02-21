"""Plain text renderer."""

from __future__ import annotations

from pathlib import Path

from convoformat.parser import Turn
from convoformat.references import Reference


def render_text(
    turns: list[Turn],
    output_path: Path,
    title: str,
    date: str,
    references: list[Reference] | None = None,
) -> None:
    """Render turns to a plain text file."""
    lines: list[str] = []

    lines.append(f"=== {title} ===")
    lines.append(date)
    lines.append("")

    for turn in turns:
        prefix = f"[{turn.speaker_label.upper()}]"
        lines.append(prefix)
        for para in turn.paragraphs:
            if para == "---":
                lines.append("")
            else:
                lines.append(para)
                lines.append("")
        lines.append("---")
        lines.append("")

    if references:
        lines.append("=== References ===")
        lines.append("")
        for ref in references:
            parts = [ref.title]
            if ref.channel:
                parts.append(f"Channel: {ref.channel}")
            if ref.duration:
                parts.append(f"Duration: {ref.duration}")
            parts.append(ref.url)
            lines.append("  ".join(parts))
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
