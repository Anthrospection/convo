# ConvoFormat — Fixes from First Test Run

Input file: `input/sample1.txt` (excerpt from "Saturday Rules Apply to Turtles" session)

---

## What's Working Well

Great first pass. The core pipeline is solid:

- **Noise stripping works** — tool calls, file reads, system reminders, and most scaffolding are cleanly removed. The conversation reads naturally without the terminal clutter.
- **Dark theme HTML looks good** — color scheme, typography, and layout all work. The speaker labels are visually distinct and the overall feel is readable and polished.
- **Turn detection is accurate** — speaker turns are correctly identified and attributed throughout a long, multi-topic conversation with lots of tone shifts.
- **PDF output exists and is readable** — for a first build, having a styled PDF with background color, speaker labels, and proper text flow is impressive.
- **All four output formats generated** — TXT, HTML, MD, and PDF all produced without errors.

This is a strong foundation. The issues below are polish, not structural.

---

## Bugs

### 1. Markdown renderer ignores --assistant and --user flags
**Severity**: Low
**Details**: PDF and HTML correctly use "Stacey" and "Elliot" as speaker labels. Markdown output still shows "Assistant" and "User". The markdown renderer likely has hardcoded defaults instead of reading from the speaker label config passed via CLI.
**Fix**: Wire up the same speaker_label values that PDF/HTML use.

### 2. Progress line leaking through noise filter
**Severity**: Low
**Details**: Line `✻ Baked for 43s` appears in the output (visible in markdown around line 53). The parser should be stripping all progress lines matching the `✻ .+ for \d+[smh]` pattern.
**Fix**: Check the regex — may not be matching multi-word durations like "1m 46s" or may have an edge case with this specific line. Verify against all cooking verbs.

### 3. /rename command leaking through as user turn
**Severity**: Medium
**Details**: The `/rename` slash command and its output (`Session renamed to: Saturday Rules Apply to Turtles`) appear as a user turn in the output. These are system/scaffolding and should be stripped.
**Fix**: Add `/rename`, `/help`, `/clear`, and other slash commands to the SYSTEM or TOOL_CALL classification. Pattern: lines starting with `/` followed by a command word. Also strip the `⎿  Session renamed to:` response line.

### 4. ❯ symbol not rendering in PDF
**Severity**: Medium
**Details**: The ❯ (U+276F, Heavy Right-Pointing Angle Quotation Mark Ornament) character before "Stacey" renders fine in HTML but is invisible/missing in the PDF. The ● (U+25CF) before "Elliot" renders fine. This is a ReportLab font issue — Helvetica doesn't include ❯.
**Fix**: Either embed a Unicode-capable font (DejaVu Sans, Noto Sans), or replace ❯ with a simpler character in the PDF renderer (e.g., `>` or `»` or `▸`). The HTML renderer can keep ❯ since browsers handle it fine.

### 5. Title defaults to filename stem
**Severity**: Low
**Details**: Output titled "Sample1" because input file was `sample1.txt` and no `--title` was passed. The auto-title detection from the PRD (extract first substantive topic from conversation) doesn't appear to be implemented yet.
**Fix**: Implement auto-title detection per PRD spec, or at minimum clean up the filename stem (title-case, replace underscores/hyphens with spaces).

### 6. Mobile PDF layout is default
**Severity**: Low
**Details**: PDF output used mobile-width format (390pt) without `--mobile` flag being passed. Per PRD, default should be A4 portrait with `--mobile` as an opt-in flag.
**Fix**: Check default page size in pdf.py. Should be A4 unless `--mobile` is explicitly passed.

---

## Enhancement Requests (not bugs, just observations)

### A. No YouTube video reference in output
The conversation heavily discusses a specific YouTube video (Blaise Agüera y Arcas, "What If Intelligence Didn't Evolve?"). The source URL doesn't appear anywhere because it was in tool calls that got stripped. Consider: a metadata/references section at the end, or a way to pass `--reference "URL"` that gets appended.

### B. Sharing mode considerations
For sharing with wider audiences, it would be useful to have a `--redact-names` flag (separate from full `--private`) that just swaps speaker names and strips obviously personal references (roommate names, medical details, wardrobe specifics) while keeping the intellectual content intact. Different from full PII scrubbing — more like "make this presentable to strangers."

---

## Test Command for Verification
After fixes, re-run against the same input:
```bash
convoformat input/sample1.txt --output=pdf --title="Saturday Rules Apply to Turtles" --assistant="Elliot" --user="Stacey"
convoformat input/sample1.txt --output=html --title="Saturday Rules Apply to Turtles" --assistant="Elliot" --user="Stacey"
convoformat input/sample1.txt --output=markdown --title="Saturday Rules Apply to Turtles" --assistant="Elliot" --user="Stacey"
```

---

## Bottom Line

Really solid v1. The conversation is genuinely enjoyable to read in the formatted output — which is the whole point. The fixes above are all straightforward and none require rethinking the architecture. Nice work.
