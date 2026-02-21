"""HTML renderer using Jinja2."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from convo.parser import Turn
from convo.themes import Theme

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_html(
    turns: list[Turn],
    output_path: Path,
    theme: Theme,
    mobile: bool,
    title: str,
    date: str,
    assistant_label: str,
    user_label: str,
    references: list | None = None,
) -> None:
    """Render turns to a self-contained HTML file."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
    )
    template = env.get_template("conversation.html.j2")

    html_content = template.render(
        turns=turns,
        theme=theme,
        mobile=mobile,
        title=title,
        date=date,
        assistant_label=assistant_label,
        user_label=user_label,
        references=references,
    )

    output_path.write_text(html_content, encoding="utf-8")
