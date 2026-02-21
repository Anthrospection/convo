"""YouTube and URL reference extraction and metadata resolution."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass

from convoformat.parser import Turn

# Match YouTube URLs in various forms
_YT_RE = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})"
)


@dataclass
class Reference:
    url: str
    title: str
    channel: str | None = None
    duration: str | None = None
    source: str = "conversation"  # "conversation" or "cli"


def _format_duration(seconds: int | float) -> str:
    """Convert seconds to HH:MM:SS or MM:SS."""
    s = int(seconds)
    h, remainder = divmod(s, 3600)
    m, sec = divmod(remainder, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def extract_youtube_urls(turns: list[Turn]) -> list[str]:
    """Find all YouTube URLs mentioned in conversation turns."""
    seen: set[str] = set()
    urls: list[str] = []
    for turn in turns:
        for para in turn.paragraphs:
            for match in _YT_RE.finditer(para):
                video_id = match.group(1)
                if video_id not in seen:
                    seen.add(video_id)
                    urls.append(match.group(0))
    return urls


def resolve_youtube(url: str) -> Reference:
    """Resolve YouTube URL metadata via yt-dlp --dump-json."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return Reference(
                url=url,
                title=data.get("title", url),
                channel=data.get("channel") or data.get("uploader"),
                duration=_format_duration(data["duration"]) if data.get("duration") else None,
            )
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError, KeyError):
        pass
    # Fallback: return URL as-is
    return Reference(url=url, title=url)


def collect_references(
    turns: list[Turn],
    cli_refs: list[str] | None = None,
) -> list[Reference]:
    """Collect and deduplicate references from conversation + CLI args.

    CLI refs are resolved first (marked source="cli"), then auto-detected
    conversation URLs are added if not already present.
    """
    refs: list[Reference] = []
    seen_ids: set[str] = set()

    def _video_id(url: str) -> str | None:
        m = _YT_RE.search(url)
        return m.group(1) if m else None

    # CLI-provided refs first
    for url in cli_refs or []:
        vid = _video_id(url)
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            ref = resolve_youtube(url)
            ref.source = "cli"
            refs.append(ref)
        elif not vid:
            # Non-YouTube URL, just add as-is
            refs.append(Reference(url=url, title=url, source="cli"))

    # Auto-detected from conversation
    for url in extract_youtube_urls(turns):
        vid = _video_id(url)
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            ref = resolve_youtube(url)
            ref.source = "conversation"
            refs.append(ref)

    return refs
