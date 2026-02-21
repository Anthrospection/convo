"""Tests for the privacy / PII redaction module."""

from convo.parser import Turn
from convo.privacy import _apply_regex, redact_turns


def _turn(text: str, speaker: str = "assistant") -> Turn:
    return Turn(speaker=speaker, paragraphs=[text], speaker_label="Assistant")


# ── Regex layer ───────────────────────────────────────────────────────────────

class TestRegexRedaction:
    def test_redacts_api_key(self):
        text = "Use this key: sk-abc123def456ghi789jkl0"
        result, count = _apply_regex(text)
        assert "[REDACTED_KEY]" in result
        assert "sk-abc123def456ghi789jkl0" not in result
        assert count == 1

    def test_redacts_bearer_token(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.abc"
        result, count = _apply_regex(text)
        assert "[REDACTED_KEY]" in result
        assert count == 1

    def test_redacts_ssn(self):
        text = "SSN is 123-45-6789"
        result, count = _apply_regex(text)
        assert "[REDACTED_SSN]" in result
        assert "123-45-6789" not in result

    def test_redacts_password(self):
        text = "password: mysecretpass123"
        result, count = _apply_regex(text)
        assert "[REDACTED_PASSWORD]" in result

    def test_redacts_credit_card(self):
        text = "Card: 4111 1111 1111 1111"
        result, count = _apply_regex(text)
        assert "[REDACTED_CARD]" in result

    def test_no_false_positive_normal_text(self):
        text = "The weather today is nice."
        result, count = _apply_regex(text)
        assert result == text
        assert count == 0

    def test_multiple_matches(self):
        text = "sk-key1abc123def456ghi7 and sk-key2abc123def456ghi8"
        result, count = _apply_regex(text)
        assert count == 2
        assert result.count("[REDACTED_KEY]") == 2


# ── redact_turns (regex only, no presidio) ────────────────────────────────────

class TestRedactTurns:
    def test_redacts_api_key_in_turn(self):
        turns = [_turn("My key is sk-supersecretkey123456789")]
        redacted, summary = redact_turns(turns, use_presidio=False)
        assert "[REDACTED_KEY]" in redacted[0].paragraphs[0]
        assert summary.regex_count == 1

    def test_preserves_clean_content(self):
        turns = [_turn("This is perfectly safe text with no PII.")]
        redacted, summary = redact_turns(turns, use_presidio=False)
        assert redacted[0].paragraphs[0] == "This is perfectly safe text with no PII."
        assert summary.regex_count == 0

    def test_multiple_turns(self):
        turns = [
            _turn("Safe paragraph one.", speaker="user"),
            _turn("key: sk-abc123def456ghi789jklm", speaker="assistant"),
            _turn("Safe paragraph three.", speaker="user"),
        ]
        redacted, summary = redact_turns(turns, use_presidio=False)
        assert redacted[0].paragraphs[0] == "Safe paragraph one."
        assert "[REDACTED_KEY]" in redacted[1].paragraphs[0]
        assert redacted[2].paragraphs[0] == "Safe paragraph three."
        assert summary.regex_count == 1

    def test_preserves_speaker_metadata(self):
        turns = [_turn("text", speaker="user")]
        turns[0] = Turn(speaker="user", paragraphs=["text"], speaker_label="Alex")
        redacted, _ = redact_turns(turns, use_presidio=False)
        assert redacted[0].speaker == "user"
        assert redacted[0].speaker_label == "Alex"

    def test_empty_turns(self):
        redacted, summary = redact_turns([], use_presidio=False)
        assert redacted == []
        assert summary.regex_count == 0
