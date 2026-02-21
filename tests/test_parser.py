"""Tests for the parser module."""

from pathlib import Path

import pytest

from convo.parser import Turn, _classify, _paragraphize, detect_date, detect_title, parse
from convo.parser import LineType

FIXTURE = Path(__file__).parent / "fixtures" / "sample_conversation.txt"


# ── _classify ───────────────────────────────────────────────────────────────

class TestClassify:
    def test_user_turn(self):
        assert _classify("❯ Hello there") == LineType.USER_TURN

    def test_asst_turn(self):
        assert _classify("● Hello there") == LineType.ASST_TURN

    def test_tool_call_camelcase(self):
        assert _classify("● Bash(echo hello)") == LineType.TOOL_CALL

    def test_tool_call_read(self):
        assert _classify("● Read /path/to/file.py") == LineType.TOOL_CALL

    def test_tool_call_searched(self):
        assert _classify("● Searched for 2 patterns, read 1 file (ctrl+o to expand)") == LineType.TOOL_CALL

    def test_tool_call_ctrl_o(self):
        assert _classify("● Read 3 files, wrote 1 file (ctrl+o to expand)") == LineType.TOOL_CALL

    def test_tool_output(self):
        assert _classify("⎿ some output") == LineType.TOOL_OUTPUT

    def test_tool_output_indented(self):
        assert _classify("  ⎿ some output") == LineType.TOOL_OUTPUT

    def test_progress(self):
        assert _classify("✻ Baked for 43s") == LineType.PROGRESS

    def test_progress_minutes(self):
        assert _classify("✻ Cogitated for 1m 46s") == LineType.PROGRESS

    def test_continuation_blank(self):
        assert _classify("") == LineType.CONTINUATION

    def test_continuation_indented(self):
        assert _classify("  some continuation text") == LineType.CONTINUATION

    def test_asst_not_tool_lowercase(self):
        # "quiet laugh" starts with lowercase after ● — should be ASST_TURN
        assert _classify("● quiet laugh") == LineType.ASST_TURN

    def test_asst_not_tool_short(self):
        assert _classify("● grinning") == LineType.ASST_TURN


# ── _paragraphize ────────────────────────────────────────────────────────────

class TestParagraphize:
    def test_single_paragraph(self):
        lines = ["Hello world", "this continues"]
        assert _paragraphize(lines) == ["Hello world this continues"]

    def test_split_on_blank(self):
        lines = ["First paragraph.", "", "Second paragraph."]
        assert _paragraphize(lines) == ["First paragraph.", "Second paragraph."]

    def test_dash_separator_becomes_own_paragraph(self):
        lines = ["Before", "---", "After"]
        result = _paragraphize(lines)
        assert result == ["Before", "---", "After"]

    def test_strips_leading_whitespace(self):
        lines = ["  indented line", "  also indented"]
        assert _paragraphize(lines) == ["indented line also indented"]

    def test_empty_lines_ignored(self):
        lines = ["", "", "Content", ""]
        assert _paragraphize(lines) == ["Content"]

    def test_multiple_blank_lines(self):
        lines = ["A", "", "", "B"]
        assert _paragraphize(lines) == ["A", "B"]


# ── parse ────────────────────────────────────────────────────────────────────

class TestParse:
    def test_returns_turns(self):
        turns = parse(FIXTURE)
        assert len(turns) > 0
        assert all(isinstance(t, Turn) for t in turns)

    def test_strips_tool_calls(self):
        turns = parse(FIXTURE)
        # Tool call content should not appear in any paragraph
        all_text = " ".join(p for t in turns for p in t.paragraphs)
        assert "echo" not in all_text  # from Bash(echo "hello")

    def test_strips_progress(self):
        turns = parse(FIXTURE)
        all_text = " ".join(p for t in turns for p in t.paragraphs)
        assert "Baked for" not in all_text

    def test_strips_tool_output(self):
        turns = parse(FIXTURE)
        all_text = " ".join(p for t in turns for p in t.paragraphs)
        # The ⎿ hello output should not appear
        assert "⎿" not in all_text

    def test_speaker_classification(self):
        turns = parse(FIXTURE)
        speakers = [t.speaker for t in turns]
        assert "user" in speakers
        assert "assistant" in speakers

    def test_default_labels(self):
        turns = parse(FIXTURE)
        for turn in turns:
            if turn.speaker == "user":
                assert turn.speaker_label == "User"
            else:
                assert turn.speaker_label == "Assistant"

    def test_custom_labels(self):
        turns = parse(FIXTURE, assistant_label="Claude", user_label="Alex")
        for turn in turns:
            if turn.speaker == "user":
                assert turn.speaker_label == "Alex"
            else:
                assert turn.speaker_label == "Claude"

    def test_verbose_includes_tool_calls(self):
        turns_normal = parse(FIXTURE, verbose=False)
        turns_verbose = parse(FIXTURE, verbose=True)
        assert len(turns_verbose) > len(turns_normal)

    def test_multiline_user_turn(self):
        turns = parse(FIXTURE)
        user_turns = [t for t in turns if t.speaker == "user"]
        # Second user turn has a follow-up question on a continuation line
        assert any("follow-up" in " ".join(t.paragraphs) for t in user_turns)

    def test_header_ignored(self):
        turns = parse(FIXTURE)
        all_text = " ".join(p for t in turns for p in t.paragraphs)
        # ASCII art should not appear
        assert "Claude Code" not in all_text
        assert "▟█▙" not in all_text

    def test_dash_separator_preserved(self):
        turns = parse(FIXTURE)
        asst_turns = [t for t in turns if t.speaker == "assistant"]
        # One assistant turn has '---' in it
        all_paras = [p for t in asst_turns for p in t.paragraphs]
        assert "---" in all_paras

    def test_empty_file(self, tmp_path):
        empty = tmp_path / "empty.txt"
        empty.write_text("")
        assert parse(empty) == []


# ── detect_title / detect_date ────────────────────────────────────────────────

class TestAutoDetect:
    def test_detect_title_fallback_to_stem(self):
        title = detect_title(FIXTURE, [])
        # Fixture filename is "sample_conversation" → "Sample Conversation"
        assert title == "Sample Conversation"

    def test_detect_date_fallback_to_mtime(self):
        date = detect_date(FIXTURE)
        # Should return a YYYY-MM-DD string
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2}", date)

    def test_detect_date_from_iso(self, tmp_path):
        f = tmp_path / "convo.txt"
        f.write_text("❯ Hello\n● This was on 2026-01-15 when things happened.\n")
        assert detect_date(f) == "2026-01-15"
