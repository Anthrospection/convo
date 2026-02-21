"""CLI entry point for ConvoFormatter."""

import sys
from pathlib import Path

import click

from convoformat import __version__
from convoformat.parser import Turn, detect_date, detect_title, parse

_FORMAT_EXTENSIONS = {
    "pdf": ".pdf",
    "html": ".html",
    "markdown": ".md",
    "text": ".txt",
}

_THEME_ONLY_FORMATS = {"pdf", "html"}


def _warn(msg: str) -> None:
    print(f"[notice] {msg}", file=sys.stderr)


def _resolve_output(input_path: Path, output_path: Path | None, fmt: str) -> Path:
    if output_path:
        return output_path
    candidate = input_path.with_suffix(_FORMAT_EXTENSIONS[fmt])
    if candidate == input_path:
        # e.g. --output=text on a .txt source — avoid clobbering the original
        candidate = input_path.with_stem(input_path.stem + "_formatted")
    return candidate


def _load_theme(name: str):
    if name == "dark":
        from convoformat.themes.dark import DARK
        return DARK
    from convoformat.themes.light import LIGHT
    return LIGHT


def _render(
    fmt: str,
    turns: list[Turn],
    output_path: Path,
    theme,
    mobile: bool,
    title: str,
    date: str,
    assistant_label: str,
    user_label: str,
) -> None:
    if fmt == "pdf":
        from convoformat.renderers.pdf import render_pdf
        render_pdf(turns, output_path, theme, mobile, title, date, assistant_label, user_label)
    elif fmt == "html":
        from convoformat.renderers.html import render_html
        render_html(turns, output_path, theme, mobile, title, date, assistant_label, user_label)
    elif fmt == "markdown":
        from convoformat.renderers.markdown import render_markdown
        render_markdown(turns, output_path, title, date)
    elif fmt == "text":
        from convoformat.renderers.text import render_text
        render_text(turns, output_path, title, date)


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path), required=False)
@click.option(
    "--output", "-o",
    "fmt",
    type=click.Choice(["pdf", "html", "markdown", "text"]),
    default="pdf",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--theme",
    type=click.Choice(["dark", "light"]),
    default=None,
    help="Visual theme: dark, light (pdf and html only). [default: dark]",
)
@click.option("--mobile", is_flag=True, help="Optimize layout for mobile (~390pt wide).")
@click.option("--private", is_flag=True, help="Apply PII redaction. Always prints a warning.")
@click.option("--title", default=None, help="Override auto-detected title.")
@click.option("--date", default=None, help="Override auto-detected date.")
@click.option(
    "--assistant", "assistant_label",
    default="Assistant",
    show_default=True,
    help="Label for AI speaker turns.",
)
@click.option(
    "--user", "user_label",
    default="User",
    show_default=True,
    help="Label for human speaker turns.",
)
@click.option("--verbose", is_flag=True, help="Include tool calls and scaffolding in output.")
@click.version_option(__version__, prog_name="convoformat")
def main(
    input_file: Path,
    output_file: Path | None,
    fmt: str,
    theme: str,
    mobile: bool,
    private: bool,
    title: str | None,
    date: str | None,
    assistant_label: str,
    user_label: str,
    verbose: bool,
) -> None:
    """Convert a Claude Code conversation transcript to a formatted document.

    INPUT_FILE is the .txt transcript to process.
    OUTPUT_FILE is optional; defaults to INPUT_FILE with the appropriate extension.
    """
    # Warn about inapplicable flags (only when explicitly set)
    if fmt not in _THEME_ONLY_FORMATS:
        if theme is not None:
            _warn(f"--theme has no effect for --output={fmt}")
        if mobile:
            _warn(f"--mobile has no effect for --output={fmt}")
    theme = theme or "dark"  # apply default after warning check

    # Read file once; parse() will also read it but needs the full text
    head = input_file.read_text(encoding="utf-8").splitlines()[:30]
    turns = parse(input_file, assistant_label=assistant_label, user_label=user_label, verbose=verbose)

    if not turns:
        click.echo("No conversation turns found in the input file.", err=True)
        sys.exit(1)

    # Auto-detect title and date if not provided (reuse the already-read head)
    resolved_title = title or detect_title(input_file, turns, head=head)
    resolved_date = date or detect_date(input_file, head=head)

    # Apply PII redaction if requested
    if private:
        from convoformat.privacy import print_privacy_warning, redact_turns
        turns, summary = redact_turns(turns, use_presidio=True)
        print_privacy_warning(summary)

    output_path = _resolve_output(input_file, output_file, fmt)
    loaded_theme = _load_theme(theme)

    _render(
        fmt=fmt,
        turns=turns,
        output_path=output_path,
        theme=loaded_theme,
        mobile=mobile,
        title=resolved_title,
        date=resolved_date,
        assistant_label=assistant_label,
        user_label=user_label,
    )

    click.echo(f"✓ Written to {output_path}")
