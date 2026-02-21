"""CLI entry point for ConvoFormatter."""

import sys
from pathlib import Path

import click
import yaml

from convo import __version__
from convo.parser import Turn, detect_date, detect_title, parse
from convo.references import Reference, collect_references

_CONFIG_PATHS = [
    Path.home() / ".config" / "convo" / "config.yaml",
    Path.home() / ".convoformat.yaml",  # legacy fallback
]


_CONFIG_KEY_MAP = {
    "assistant": "assistant_label",
    "user": "user_label",
    "output": "fmt",
}


def _load_config() -> dict:
    """Load config from the first existing config file.

    Config keys use the friendly CLI names (assistant, user, output).
    They're mapped to click parameter names internally.
    """
    for path in _CONFIG_PATHS:
        if path.exists():
            try:
                with open(path) as f:
                    raw = yaml.safe_load(f)
                if not isinstance(raw, dict):
                    return {}
                return {_CONFIG_KEY_MAP.get(k, k): v for k, v in raw.items()}
            except Exception:
                return {}
    return {}

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
        from convo.themes.dark import DARK
        return DARK
    from convo.themes.light import LIGHT
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
    references: list[Reference] | None = None,
) -> None:
    if fmt == "pdf":
        from convo.renderers.pdf import render_pdf
        render_pdf(turns, output_path, theme, mobile, title, date, assistant_label, user_label, references=references)
    elif fmt == "html":
        from convo.renderers.html import render_html
        render_html(turns, output_path, theme, mobile, title, date, assistant_label, user_label, references=references)
    elif fmt == "markdown":
        from convo.renderers.markdown import render_markdown
        render_markdown(turns, output_path, title, date, references=references)
    elif fmt == "text":
        from convo.renderers.text import render_text
        render_text(turns, output_path, title, date, references=references)


@click.command(context_settings={"default_map": _load_config()})
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
@click.option(
    "--ref", "refs",
    multiple=True,
    help="Add a reference URL (repeatable). YouTube URLs resolve metadata automatically.",
)
@click.option("--no-ai", is_flag=True, help="Skip local model features (title generation).")
@click.option("--verbose", is_flag=True, help="Include tool calls and scaffolding in output.")
@click.version_option(__version__, prog_name="convo")
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
    refs: tuple[str, ...],
    no_ai: bool,
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

    # If title is just a filename fallback, try generating one with Ollama
    stem_title = input_file.stem.replace("_", " ").replace("-", " ").title()
    if resolved_title == stem_title and turns and not no_ai:
        from convo.titler import generate_title
        _warn("Generating title with local model...")
        generated = generate_title(turns)
        if generated:
            resolved_title = generated
            _warn(f"Title: {resolved_title}")

    # Apply PII redaction if requested
    if private:
        from convo.privacy import print_privacy_warning, redact_turns
        turns, summary = redact_turns(turns, use_presidio=True)
        print_privacy_warning(summary)

    # Collect references (auto-detect from conversation + CLI --ref args)
    references = collect_references(turns, list(refs) if refs else None)
    if references:
        _warn(f"Resolved {len(references)} reference(s)")

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
        references=references or None,
    )

    click.echo(f"✓ Written to {output_path}")
