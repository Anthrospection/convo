"""Markdown renderer."""

from pathlib import Path

from convoformat.parser import Turn


def render_markdown(
    turns: list[Turn],
    output_path: Path,
    title: str,
    date: str,
) -> None:
    """Render turns to a Markdown file suitable for Obsidian."""
    lines: list[str] = []

    asst_name = next((t.speaker_label for t in turns if t.speaker == "assistant"), "Assistant")
    user_name = next((t.speaker_label for t in turns if t.speaker == "user"), "User")

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"*{date} · {asst_name} & {user_name}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    for turn in turns:
        if turn.speaker == "assistant":
            lines.append(f"**● {turn.speaker_label}**")
        else:
            lines.append(f"**❯ {turn.speaker_label}**")
        lines.append("")

        for para in turn.paragraphs:
            lines.append(para)
            lines.append("")

        lines.append("---")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
