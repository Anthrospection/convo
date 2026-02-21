"""Plain text renderer."""

from pathlib import Path

from convoformat.parser import Turn


def render_text(
    turns: list[Turn],
    output_path: Path,
    title: str,
    date: str,
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

    output_path.write_text("\n".join(lines), encoding="utf-8")
