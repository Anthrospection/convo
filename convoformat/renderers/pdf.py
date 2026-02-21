"""PDF renderer using ReportLab."""

import html
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from convoformat.parser import Turn
from convoformat.themes import Theme

# Mobile page dimensions in points (~390px wide, tall enough for reading)
MOBILE_SIZE = (390, 700)

# Helvetica variant names (always available in ReportLab)
_BOLD = "-Bold"


def _hex(color: str) -> HexColor:
    return HexColor(color)


def _hex_dim(color: str) -> HexColor:
    """Return a semi-transparent version of a hex color by appending an alpha byte."""
    return HexColor(color + "44", hasAlpha=True)


def _bg_callback(bg_color: str):
    """Canvas callback that fills the page background before content is drawn."""
    bg = _hex(bg_color)

    def _draw(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(bg)
        canvas.rect(0, 0, *doc.pagesize, fill=1, stroke=0)
        canvas.restoreState()

    return _draw


def _label_style(name: str, color: str, bold_font: str) -> ParagraphStyle:
    return ParagraphStyle(
        name, fontName=bold_font, fontSize=8, textColor=_hex(color),
        leading=11, spaceBefore=14, spaceAfter=2,
    )


def _body_style(name: str, color: str, font: str, size: int, leading: float) -> ParagraphStyle:
    return ParagraphStyle(
        name, fontName=font, fontSize=size, textColor=_hex(color),
        leading=leading, spaceAfter=5,
    )


def _make_styles(theme: Theme, mobile: bool) -> dict[str, ParagraphStyle]:
    body_size = theme.font_size_mobile_body if mobile else theme.font_size_body
    leading = round(body_size * theme.line_height, 1)
    bold_font = theme.font_body + _BOLD

    return {
        "title": ParagraphStyle(
            "CFTitle",
            fontName=bold_font,
            fontSize=18 if mobile else 22,
            textColor=_hex(theme.title_color),
            leading=22 if mobile else 28,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "CFSubtitle",
            fontName=theme.font_body,
            fontSize=9,
            textColor=_hex(theme.subtitle_color),
            leading=13,
            spaceAfter=2,
        ),
        "meta": ParagraphStyle(
            "CFMeta",
            fontName=theme.font_body,
            fontSize=8,
            textColor=_hex(theme.subtitle_color),
            leading=11,
            spaceAfter=10,
        ),
        "asst_label": _label_style("CFAsstLabel", theme.assistant_label, bold_font),
        "user_label": _label_style("CFUserLabel", theme.user_label, bold_font),
        "asst_body":  _body_style("CFAsstBody", theme.assistant_text, theme.font_body, body_size, leading),
        "user_body":  _body_style("CFUserBody", theme.user_text, theme.font_body, body_size, leading),
    }


def render_pdf(
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
    """Render turns to a styled PDF file."""
    pagesize = MOBILE_SIZE if mobile else A4
    margin = 12 * mm if mobile else 20 * mm

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=pagesize,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )

    styles = _make_styles(theme, mobile)
    bg_draw = _bg_callback(theme.page_bg)
    hr_color = _hex(theme.hr_color)
    dim_color = _hex_dim(theme.hr_color)

    story = []

    # ── Title block ──────────────────────────────────────────────────────────
    story.append(Paragraph(html.escape(title), styles["title"]))
    story.append(Paragraph("A Conversation", styles["subtitle"]))
    story.append(
        Paragraph(
            f"{html.escape(assistant_label)} &amp; {html.escape(user_label)} · {html.escape(date)}",
            styles["meta"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=hr_color, spaceAfter=12))

    # ── Conversation turns ────────────────────────────────────────────────────
    for i, turn in enumerate(turns):
        if turn.speaker == "assistant":
            label_style = styles["asst_label"]
            body_style = styles["asst_body"]
            label_text = f"● {html.escape(turn.speaker_label)}"
        else:
            label_style = styles["user_label"]
            body_style = styles["user_body"]
            label_text = f"» {html.escape(turn.speaker_label)}"

        story.append(Paragraph(label_text, label_style))

        for para in turn.paragraphs:
            if para == "---":
                story.append(
                    HRFlowable(
                        width="80%",
                        thickness=0.5,
                        color=dim_color,
                        spaceAfter=4,
                        spaceBefore=4,
                        hAlign="LEFT",
                    )
                )
            else:
                story.append(Paragraph(html.escape(para), body_style))

        # Thin divider between turns (skip after last)
        if i < len(turns) - 1:
            story.append(Spacer(1, 4))
            story.append(
                HRFlowable(width="100%", thickness=0.5, color=dim_color, spaceAfter=2)
            )

    # ── References section ──────────────────────────────────────────────────
    if references:
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=1, color=hr_color, spaceAfter=12))
        story.append(Paragraph("References", styles["title"].clone(
            "CFRefTitle", fontSize=14, leading=18, spaceAfter=8,
        )))
        ref_style = _body_style("CFRef", theme.assistant_text, theme.font_body, 9, 13)
        ref_meta_style = _body_style("CFRefMeta", theme.subtitle_color, theme.font_body, 8, 11)
        for ref in references:
            story.append(Paragraph(html.escape(ref.title), ref_style))
            meta_parts = []
            if ref.channel:
                meta_parts.append(ref.channel)
            if ref.duration:
                meta_parts.append(ref.duration)
            meta_parts.append(ref.url)
            story.append(Paragraph(html.escape(" · ".join(meta_parts)), ref_meta_style))
            story.append(Spacer(1, 6))

    doc.build(story, onFirstPage=bg_draw, onLaterPages=bg_draw)
