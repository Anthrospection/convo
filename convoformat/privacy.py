"""PII redaction for --private mode.

Layer 1 (always runs): regex patterns for API keys, passwords, SSNs, card numbers.
Layer 2 (requires presidio extra): NLP-based entity detection via Microsoft Presidio.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

from convoformat.parser import Turn

# ── Layer 1: regex patterns ────────────────────────────────────────────────

_REGEX_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "[REDACTED_KEY]"),
    (re.compile(r"Bearer [a-zA-Z0-9\-._~+/]+=*"), "[REDACTED_KEY]"),
    (re.compile(r"(?i)password\s*[:=]\s*\S+"), "[REDACTED_PASSWORD]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b"), "[REDACTED_CARD]"),
]

# Presidio entity → replacement token
_PRESIDIO_REPLACEMENTS = {
    "PERSON": "[NAME]",
    "ORG": "[ORGANIZATION]",
    "GPE": "[LOCATION]",
    "LOC": "[LOCATION]",
    "EMAIL_ADDRESS": "[EMAIL]",
    "PHONE_NUMBER": "[PHONE]",
    "CREDIT_CARD": "[REDACTED_CARD]",
    "MEDICAL_LICENSE": "[HEALTH_ID]",
}

_LOW_CONFIDENCE_THRESHOLD = 0.75


@dataclass
class RedactionSummary:
    entity_counts: dict[str, int]
    low_confidence_items: list[tuple[str, str, float]]  # (original, replacement, score)
    regex_count: int


def _apply_regex(text: str) -> tuple[str, int]:
    """Apply regex redaction rules. Returns (redacted_text, match_count)."""
    count = 0
    for pattern, replacement in _REGEX_RULES:
        new_text, n = pattern.subn(replacement, text)
        count += n
        text = new_text
    return text, count


def _load_presidio_engines():
    """Load Presidio engines once. Fails clearly if the [private] extra is not installed."""
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
    except ImportError:
        print(
            "\n⚠  --private requires the 'private' extra:\n"
            "   pip install convoformat[private]\n"
            "   python -m spacy download en_core_web_lg\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return AnalyzerEngine(), AnonymizerEngine()


def _apply_presidio(
    text: str, analyzer, anonymizer
) -> tuple[str, dict[str, int], list[tuple[str, str, float]]]:
    """Apply Presidio NLP redaction using pre-loaded engines."""
    from presidio_anonymizer.entities import OperatorConfig

    entity_types = list(_PRESIDIO_REPLACEMENTS.keys())
    results = analyzer.analyze(text=text, entities=entity_types, language="en")

    if not results:
        return text, {}, []

    entity_counts: dict[str, int] = {}
    low_conf: list[tuple[str, str, float]] = []

    # Build operators dict keyed by entity type (not per-result instance)
    operators = {
        etype: OperatorConfig("replace", {"new_value": _PRESIDIO_REPLACEMENTS.get(etype, "[REDACTED]")})
        for etype in {r.entity_type for r in results}
    }

    for result in results:
        entity_counts[result.entity_type] = entity_counts.get(result.entity_type, 0) + 1
        if result.score < _LOW_CONFIDENCE_THRESHOLD:
            snippet = text[result.start : result.end]
            replacement = _PRESIDIO_REPLACEMENTS.get(result.entity_type, "[REDACTED]")
            low_conf.append((snippet, replacement, result.score))

    anonymized = anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)
    return anonymized.text, entity_counts, low_conf


def redact_turns(
    turns: list[Turn],
    use_presidio: bool = True,
) -> tuple[list[Turn], RedactionSummary]:
    """Redact PII from all turns. Returns new Turn objects and a summary."""
    total_regex = 0
    total_entities: dict[str, int] = {}
    all_low_conf: list[tuple[str, str, float]] = []

    # Load Presidio engines once for the entire run (loading spaCy is expensive)
    analyzer = anonymizer = None
    if use_presidio:
        analyzer, anonymizer = _load_presidio_engines()

    redacted_turns: list[Turn] = []

    for turn in turns:
        new_paragraphs: list[str] = []
        for para in turn.paragraphs:
            # Layer 1: regex
            para, n = _apply_regex(para)
            total_regex += n

            # Layer 2: Presidio NLP
            if use_presidio:
                para, ent_counts, low_conf = _apply_presidio(para, analyzer, anonymizer)
                for ent, count in ent_counts.items():
                    total_entities[ent] = total_entities.get(ent, 0) + count
                all_low_conf.extend(low_conf)

            new_paragraphs.append(para)

        redacted_turns.append(
            Turn(
                speaker=turn.speaker,
                paragraphs=new_paragraphs,
                speaker_label=turn.speaker_label,
            )
        )

    summary = RedactionSummary(
        entity_counts=total_entities,
        low_confidence_items=all_low_conf,
        regex_count=total_regex,
    )
    return redacted_turns, summary


def print_privacy_warning(summary: RedactionSummary) -> None:
    """Print the --private mode warning to stderr."""
    total_nlp = sum(summary.entity_counts.values())
    total = total_nlp + summary.regex_count

    breakdown_parts = []
    for ent, count in sorted(summary.entity_counts.items()):
        breakdown_parts.append(f"{ent} ×{count}")
    if summary.regex_count:
        breakdown_parts.append(f"REGEX ×{summary.regex_count}")
    breakdown = ", ".join(breakdown_parts) if breakdown_parts else "none detected"

    print(
        f"\n⚠  Privacy mode active (--private)\n"
        f"   Redacted entities: {total} ({breakdown})\n"
        f"   Low-confidence items: {len(summary.low_confidence_items)}"
        + (" — manual review recommended" if summary.low_confidence_items else "")
        + "\n"
        "   This tool makes a good-faith effort but cannot guarantee completeness.\n"
        "   Always review output before sharing.\n",
        file=sys.stderr,
    )
