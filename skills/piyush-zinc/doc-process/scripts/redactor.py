#!/usr/bin/env python3
"""
redactor.py — PII redaction that preserves the original file format.

Output is always a **copy** of the input with black blocks drawn over
sensitive data (PDF / image) or token-replaced text (plain-text files).
The original file is never modified.

Modes:
  light     Category 1 only (personal identifiers)
  standard  Category 1 + 2  (personal + financial)  [default]
  full      Category 1 + 2 + 3 (all sensitive data)

Usage:
  python redactor.py --file report.pdf
  python redactor.py --file scan.png   --mode full
  python redactor.py --file notes.txt  --output notes_redacted.txt
  python redactor.py --file report.pdf --dry-run
"""

import argparse
import re
import shutil
import sys
from pathlib import Path
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════
# Pattern definitions
# ═══════════════════════════════════════════════════════════════════════════

_PDF_EXTS = {".pdf"}
_IMG_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}


@dataclass
class RedactionRule:
    name: str
    pattern: str
    replacement: str       # text-mode token (may use \\g<1> backrefs)
    category: int          # 1 | 2 | 3
    flags: int = re.IGNORECASE
    priority: int = 100    # lower wins on ties
    value_group: int = 0   # 0 = full match; N = group N is the sensitive value


# ── Category 1 — Personal Identifiers ────────────────────────────────────

_CAT1 = [
    RedactionRule("SSN",       r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b", "[SSN REDACTED]", 1),
    RedactionRule("SIN",       r"\b\d{3}-\d{3}-\d{3}\b",         "[SIN REDACTED]", 1),
    RedactionRule("Passport",  r"\b[A-Z]{1,2}\d{6,9}\b",         "[PASSPORT NUMBER REDACTED]", 1),
    RedactionRule(
        "DL keyword",
        r"(driver'?s?\s+licen[sc]e\s*(?:no\.?|number|#)?\s*:?\s*)([A-Z0-9-]{5,15})",
        r"\g<1>[LICENSE NUMBER REDACTED]", 1, value_group=2,
    ),
    RedactionRule("Email", r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "[EMAIL REDACTED]", 1),
    RedactionRule(
        "Phone",
        r"(?<!\d)(\+?\d{1,3}[\s\-.])?(\(?\d{2,4}\)?[\s\-.]){1,3}\d{3,4}(?!\d)",
        "[PHONE REDACTED]", 1,
    ),
    RedactionRule(
        "DOB keyword",
        r"((?:d\.?o\.?b\.?|date\s+of\s+birth|birth\s+date)\s*:?\s*)(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})",
        r"\g<1>[DATE OF BIRTH REDACTED]", 1, value_group=2,
    ),
    RedactionRule(
        "Street address",
        r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl|Terrace|Ter)\b\.?",
        "[ADDRESS REDACTED]", 1,
    ),
    RedactionRule("ZIP code",  r"\b\d{5}(?:-\d{4})?\b",          "[POSTAL CODE REDACTED]", 1),
    RedactionRule("CA postal", r"\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b",  "[POSTAL CODE REDACTED]", 1),
    RedactionRule("NRIC",      r"\b[STFGM]\d{7}[A-Z]\b",         "[NRIC REDACTED]", 1),
    RedactionRule(
        "MRN keyword",
        r"((?:mrn|medical\s+record\s+(?:no\.?|number|#))\s*:?\s*)([A-Z0-9\-]{4,15})",
        r"\g<1>[MEDICAL ID REDACTED]", 1, value_group=2,
    ),
]

# ── Category 2 — Financial Data ──────────────────────────────────────────

_CAT2 = [
    RedactionRule("Card number", r"\b(?:\d{4}[\s\-]?){3}\d{1,4}\b", "[CARD NUMBER REDACTED]", 2, priority=10),
    RedactionRule(
        "Account keyword",
        r"(account\s*(?:no\.?|number|#|num)\s*:?\s*)(\d[\d\s\-]{6,18}\d)",
        r"\g<1>[ACCOUNT NUMBER REDACTED]", 2, value_group=2,
    ),
    RedactionRule("IBAN", r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b", "[IBAN REDACTED]", 2),
    RedactionRule(
        "ABA routing",
        r"(routing\s*(?:no\.?|number|#)?\s*:?\s*)(\d{9})\b",
        r"\g<1>[ROUTING NUMBER REDACTED]", 2, value_group=2,
    ),
    RedactionRule(
        "SWIFT",
        r"((?:swift|bic)\s*(?:code)?\s*:?\s*)([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b",
        r"\g<1>[SWIFT REDACTED]", 2, value_group=2,
    ),
    RedactionRule(
        "Salary keyword",
        r"((?:salary|compensation|annual\s+pay|base\s+pay|wage)\s*:?\s*[\$£€¥₹]?\s*)(\d[\d,\.]+)",
        r"\g<1>[COMPENSATION REDACTED]", 2, value_group=2,
    ),
]

# ── Category 3 — Legal / Highly Sensitive ────────────────────────────────

_CAT3 = [
    RedactionRule("HIV status",    r"\b(HIV[\-\s]?(?:positive|negative|status)|AIDS\s+diagnosis)\b",    "[HEALTH STATUS REDACTED]", 3),
    RedactionRule("Mental health", r"\b(depression|anxiety\s+disorder|bipolar|schizophrenia|PTSD|borderline\s+personality)\b", "[MENTAL HEALTH INFORMATION REDACTED]", 3),
    RedactionRule("Immigration",   r"\b(undocumented|illegal\s+alien|visa\s+overstay|deportation\s+order|asylum\s+seeker)\b", "[IMMIGRATION STATUS REDACTED]", 3),
    RedactionRule(
        "Minor name",
        r"((?:minor|juvenile|child)\s+(?:named?|called)?\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"\g<1>[MINOR'S NAME REDACTED]", 3, value_group=2,
    ),
    RedactionRule("Privilege", r"(attorney[\-\s]client\s+privilege|privileged\s+and\s+confidential|work\s+product\s+doctrine)", "[PRIVILEGED — REDACTED]", 3),
]

ALL_RULES = _CAT1 + _CAT2 + _CAT3


def _rules_for_mode(mode: str) -> list[RedactionRule]:
    if mode == "light":
        return list(_CAT1)
    if mode == "full":
        return list(ALL_RULES)
    return list(_CAT1) + list(_CAT2)   # standard


# ═══════════════════════════════════════════════════════════════════════════
# Detection engine  (shared across all file types)
# ═══════════════════════════════════════════════════════════════════════════

def _compile_rules(mode: str, custom_patterns: list[str] | None = None):
    rules = _rules_for_mode(mode)
    if custom_patterns:
        for i, p in enumerate(custom_patterns):
            rules.append(RedactionRule(f"Custom-{i+1}", p, "[CUSTOM REDACTED]", 0))
    out = []
    for r in rules:
        try:
            out.append((re.compile(r.pattern, r.flags), r))
        except re.error as e:
            print(f"Warning: invalid regex for '{r.name}': {e}", file=sys.stderr)
    return out


def _detect(text, compiled_rules):
    """Return non-overlapping matches sorted by position (longest / highest-priority wins ties)."""
    cands = []
    for pat, rule in compiled_rules:
        for m in pat.finditer(text):
            cands.append((m.start(), m.end(), m, rule))
    cands.sort(key=lambda x: (x[0], -(x[1] - x[0]), x[3].priority))
    sel, pos = [], 0
    for s, e, m, r in cands:
        if s >= pos:
            sel.append((s, e, m, r))
            pos = e
    return sel


def _sensitive_span(m, rule):
    """Return (start, end) of the portion to black-out.  For keyword rules this
    is group N (the value), not the label."""
    g = rule.value_group
    if g and g <= len(m.groups()):
        return m.start(g), m.end(g)
    return m.start(), m.end()


def _preview(m):
    s = m.group(0)
    return (s[:2] + "…" + s[-2:]) if len(s) > 6 else "…"


# ═══════════════════════════════════════════════════════════════════════════
# Result
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class RedactionResult:
    output_path: Path | None = None
    log: list[dict] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    fmt: str = "text"          # "text" | "pdf" | "image"
    redacted_text: str = ""    # only populated for text-mode output


# ═══════════════════════════════════════════════════════════════════════════
# PDF redaction — black bars on a copy  (requires PyMuPDF)
# ═══════════════════════════════════════════════════════════════════════════

def _redact_pdf(input_path, output_path, compiled_rules):
    import fitz

    # Work on a copy — never touch the original
    shutil.copy2(input_path, output_path)
    doc = fitz.open(str(output_path))

    log, counts = [], {}

    for page_idx, page in enumerate(doc):
        text = page.get_text()
        hits = _detect(text, compiled_rules)

        for _, _, m, rule in hits:
            vs, ve = _sensitive_span(m, rule)
            search = m.group(0)[vs - m.start():ve - m.start()].strip()
            if not search:
                continue

            for rect in page.search_for(search):
                page.add_redact_annot(rect, fill=(0, 0, 0), text_color=(0, 0, 0))

            log.append({"page": page_idx + 1, "rule": rule.name,
                        "category": rule.category, "preview": _preview(m)})
            counts[rule.name] = counts.get(rule.name, 0) + 1

        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    doc.saveIncr()     # save incrementally to the copy
    doc.close()
    return log, counts


# ═══════════════════════════════════════════════════════════════════════════
# Image redaction — black bars on a copy  (Pillow + tesseract)
# ═══════════════════════════════════════════════════════════════════════════

def _redact_image(input_path, output_path, compiled_rules):
    import pytesseract
    from PIL import Image, ImageDraw

    # Work on a copy
    img = Image.open(str(input_path))
    original_mode = img.mode
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    # Build a reconstructed text with word-bbox mapping
    spans, parts, cp = [], [], 0
    for i in range(len(data["text"])):
        w = data["text"][i]
        if not w.strip() or int(data["conf"][i]) < 0:
            continue
        l, t, wd, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        spans.append((cp, cp + len(w), l, t, l + wd, t + h))
        parts.append(w)
        cp += len(w) + 1
    full_text = " ".join(parts)

    hits = _detect(full_text, compiled_rules)
    log, counts = [], {}
    PAD = 2

    for _, _, m, rule in hits:
        gs, ge = _sensitive_span(m, rule)
        boxes = [(x0, y0, x1, y1)
                 for cs, ce, x0, y0, x1, y1 in spans
                 if cs < ge and ce > gs]
        if boxes:
            draw.rectangle([
                min(b[0] for b in boxes) - PAD,
                min(b[1] for b in boxes) - PAD,
                max(b[2] for b in boxes) + PAD,
                max(b[3] for b in boxes) + PAD,
            ], fill=(0, 0, 0))
        log.append({"rule": rule.name, "category": rule.category, "preview": _preview(m)})
        counts[rule.name] = counts.get(rule.name, 0) + 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path))
    return log, counts


# ═══════════════════════════════════════════════════════════════════════════
# Text redaction — token replacement on a copy
# ═══════════════════════════════════════════════════════════════════════════

def _redact_text(text, compiled_rules):
    """Single-pass token replacement.  Returns (redacted_text, log, counts)."""
    log, counts, result_lines = [], {}, []
    for line_no, line in enumerate(text.split("\n"), 1):
        hits = _detect(line, compiled_rules)
        parts, cur = [], 0
        for s, e, m, rule in hits:
            parts.append(line[cur:s])
            parts.append(m.expand(rule.replacement))
            log.append({"line": line_no, "rule": rule.name,
                        "category": rule.category, "preview": _preview(m)})
            counts[rule.name] = counts.get(rule.name, 0) + 1
            cur = e
        parts.append(line[cur:])
        result_lines.append("".join(parts))
    return "\n".join(result_lines), log, counts


# ═══════════════════════════════════════════════════════════════════════════
# Public API — single entry point
# ═══════════════════════════════════════════════════════════════════════════

def redact_file(
    input_path: Path,
    output_path: Path,
    mode: str = "standard",
    custom_patterns: list[str] | None = None,
) -> RedactionResult:
    """
    Produce a redacted **copy** of *input_path* at *output_path*.

    * PDF  → black rectangles drawn over PII, underlying text removed.
    * Image → black rectangles painted over OCR-detected PII.
    * Text → regex token replacement (format preserved).

    The original file is never modified.
    """
    ext = input_path.suffix.lower()
    compiled_rules = _compile_rules(mode, custom_patterns)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if ext in _PDF_EXTS:
        log, counts = _redact_pdf(input_path, output_path, compiled_rules)
        return RedactionResult(output_path=output_path, log=log, counts=counts, fmt="pdf")

    if ext in _IMG_EXTS:
        log, counts = _redact_image(input_path, output_path, compiled_rules)
        return RedactionResult(output_path=output_path, log=log, counts=counts, fmt="image")

    # Text file
    text = _read_text_file(input_path)
    if text is None:
        raise ValueError(
            f"Cannot read '{input_path}' as text. "
            "If the file is password-protected or encrypted, decrypt it first."
        )
    redacted_text, log, counts = _redact_text(text, compiled_rules)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(redacted_text, encoding="utf-8")
    return RedactionResult(
        output_path=output_path, log=log, counts=counts,
        fmt="text", redacted_text=redacted_text,
    )


# Convenience wrapper kept for backward-compat and direct text use
def redact(text: str, mode: str = "standard", custom_patterns: list[str] | None = None) -> RedactionResult:
    """Redact PII in a text string.  Returns result with .redacted_text populated."""
    compiled_rules = _compile_rules(mode, custom_patterns)
    rt, log, counts = _redact_text(text, compiled_rules)
    return RedactionResult(log=log, counts=counts, fmt="text", redacted_text=rt)


# ═══════════════════════════════════════════════════════════════════════════
# Summary formatter
# ═══════════════════════════════════════════════════════════════════════════

_CAT_LABELS = {
    0: "Custom Patterns",
    1: "Category 1 — Personal Identifiers",
    2: "Category 2 — Financial Data",
    3: "Category 3 — Legal / Sensitive",
}


def format_summary(result: RedactionResult, mode: str, input_path: Path) -> str:
    """Return a human-readable summary string."""
    total = sum(result.counts.values())
    rules_map = {r.name: r.category for r in ALL_RULES}

    by_cat: dict[int, dict[str, int]] = {}
    for name, cnt in result.counts.items():
        cat = rules_map.get(name, 0)
        by_cat.setdefault(cat, {})[name] = cnt

    previews: dict[str, list[str]] = {}
    for e in result.log:
        previews.setdefault(e["rule"], []).append(e["preview"])

    lines = [
        "",
        "═" * 60,
        "  REDACTION SUMMARY",
        f"  Mode: {mode}  |  File: {input_path.name}",
        "═" * 60,
    ]
    if total == 0:
        lines.append("  No sensitive data found.")
    else:
        for cat in sorted(by_cat):
            ct = sum(by_cat[cat].values())
            lines.append(f"\n  {_CAT_LABELS.get(cat, f'Category {cat}')}  ({ct} item(s))")
            for name, cnt in sorted(by_cat[cat].items()):
                snips = previews.get(name, [])
                snip = "  ".join(snips[:3]) + ("  …" if len(snips) > 3 else "")
                lines.append(f"    {name:<22} ×{cnt:<3}  {snip}")
    lines += ["", f"  Total: {total} item(s) redacted."]
    if result.output_path:
        lines.append(f"  Output: {result.output_path}")
    lines.append("═" * 60)
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _read_text_file(path: Path) -> str | None:
    for enc in ("utf-8", "latin-1"):
        try:
            text = path.read_text(encoding=enc)
            sample = text[:1000]
            bad = sum(1 for c in sample if ord(c) < 9 or 13 < ord(c) < 32)
            if bad > len(sample) * 0.1:
                return None
            return text
        except UnicodeDecodeError:
            continue
    return None


def _auto_output(input_path: Path) -> Path:
    return input_path.with_stem(input_path.stem + "_redacted")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def build_parser():
    p = argparse.ArgumentParser(
        prog="redactor",
        description="Redact PII from PDFs, images, and text files.",
    )
    p.add_argument("--file", required=True, help="Input file")
    p.add_argument("--output", help="Output path (default: <name>_redacted.<ext>)")
    p.add_argument("--mode", choices=["light", "standard", "full"], default="standard")
    p.add_argument("--custom", action="append", metavar="REGEX",
                   help="Extra regex(es) to redact (repeatable)")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be redacted; don't write a file")
    p.add_argument("--log", action="store_true",
                   help="Append per-item detail to the summary")
    return p


def main() -> int:
    args = build_parser().parse_args()

    in_path = Path(args.file).expanduser().resolve()
    if not in_path.exists():
        print(f"Error: file not found: {in_path}", file=sys.stderr)
        return 1

    out_path = Path(args.output).expanduser().resolve() if args.output else _auto_output(in_path)

    # ── Dry run: detect only ──────────────────────────────────────────────
    if args.dry_run:
        ext = in_path.suffix.lower()
        compiled = _compile_rules(args.mode, args.custom)
        if ext in _PDF_EXTS:
            import fitz
            doc = fitz.open(str(in_path))
            text = "\n".join(p.get_text() for p in doc)
            doc.close()
        elif ext in _IMG_EXTS:
            import pytesseract
            from PIL import Image
            text = pytesseract.image_to_string(Image.open(str(in_path)).convert("RGB"))
        else:
            text = _read_text_file(in_path)
            if text is None:
                print("Error: cannot read file as text.", file=sys.stderr)
                return 1
        _, log, counts = _redact_text(text, compiled)
        result = RedactionResult(log=log, counts=counts)
        summary = format_summary(result, args.mode, in_path)
        print(summary, file=sys.stderr)
        print("  (Dry run — no file written.)", file=sys.stderr)
        return 0

    # ── Full redaction ────────────────────────────────────────────────────
    try:
        result = redact_file(in_path, out_path,
                             mode=args.mode, custom_patterns=args.custom)
    except ImportError as e:
        print(f"Error: missing dependency — {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # ── Always print the summary ──────────────────────────────────────────
    summary = format_summary(result, args.mode, in_path)
    print(summary, file=sys.stderr)

    if args.log and result.log:
        print("\n  Redaction log (first 30):", file=sys.stderr)
        for entry in result.log[:30]:
            loc = f"p.{entry['page']}" if "page" in entry else f"L{entry.get('line', '?')}"
            print(f"    {loc:>6} | {entry['rule']:<22} | {entry['preview']}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
