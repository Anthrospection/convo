"""Theme definitions for ConvoFormatter output renderers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    page_bg: str
    assistant_label: str
    user_label: str
    assistant_text: str
    user_text: str
    system_text: str
    title_color: str
    hr_color: str
    subtitle_color: str
    font_body: str = "Helvetica"
    font_code: str = "Courier"
    font_size_body: int = 10
    font_size_mobile_body: int = 11
    line_height: float = 1.5
