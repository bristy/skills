---
name: doc-process
description: >
  Multi-purpose document intelligence skill: categorize documents, autofill forms, analyze contracts (risks/red flags),
  scan receipts and invoices, analyze bank statements (subscriptions/anomalies/tax deductions), parse resumes/CVs,
  scan IDs and passports (MRZ decoding), summarize medical records, redact PII and sensitive data (light/standard/full modes),
  extract meeting minutes and action items, extract tables to CSV/JSON, translate documents, and scan/dewarp document photos.
  Trigger: fill this form, autofill, review this contract, red flags, scan this receipt, log this expense,
  analyze my bank statement, subscriptions, parse this resume, scan my passport, read my id, summarize this lab report,
  redact this document, remove pii, anonymize, extract meeting minutes, action items, extract table, table to csv,
  translate this document, scan this photo, make this look scanned, what is this document, analyze this.
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Doc-Process — Document Intelligence Skill

## How Features Are Implemented

Most features in this skill are implemented entirely through Claude's own vision and language capabilities — **no external libraries or scripts are involved**. A small number of optional modes delegate to Python scripts that have declared third-party dependencies.

### Feature → Implementation Map

| Feature | How it works | External libraries needed? |
|---|---|---|
| OCR / reading images | Claude's built-in vision (multimodal) | **None** |
| MRZ decoding (passport/ID) | Claude reads MRZ visually, applies ICAO algorithm | **None** |
| PDF reading | Claude reads PDF text layer or visually | **None** |
| Form autofill | Claude reads form fields, outputs fill table | **None** |
| Contract analysis | Claude reads document, applies reference rules | **None** |
| Receipt scanning | Claude reads image/PDF | **None** |
| Bank statement analysis (PDF) | Claude reads PDF pages | **None** |
| Bank statement analysis (CSV) | `statement_parser.py` — pure stdlib | **None** |
| Expense logging | `expense_logger.py` — pure stdlib | **None** |
| Bank report generation | `report_generator.py` — pure stdlib | **None** |
| Resume / CV parsing | Claude reads document | **None** |
| Medical summarizer | Claude reads document | **None** |
| Legal redaction (display) | Claude marks up output | **None** |
| Legal redaction (file output) | `redactor.py` — pure stdlib | **None** |
| Meeting minutes (text/PDF) | Claude reads document | **None** |
| Translation | Claude's multilingual capabilities | **None** |
| Document categorizer | Claude reads first 1–2 pages (with consent gate) | **None** |
| Timeline logging | `timeline_manager.py` — pure stdlib | **None** |
| **Table extraction from PDF** | `table_extractor.py` | **pdfplumber** (declared) |
| **Audio transcription** | `audio_transcriber.py` | **openai-whisper + ffmpeg** (declared); whisper downloads model files from the internet on first run |
| **Doc scan / image dewarping** | `doc_scanner.py` (doc-scan skill) | **opencv-python-headless, Pillow, numpy** (declared); img2pdf optional |

---

## Dependencies & Install Spec

### No installation required for core functionality
All document reading, analysis, form filling, contract review, receipt scanning, bank statement analysis (PDF), resume parsing, ID scanning, medical summarizing, redaction markup, meeting minutes extraction, and translation run on Claude's native capabilities. No Python packages need to be installed.

### Optional dependencies (for script-assisted modes only)

Install these only if you intend to use the listed scripts:

```bash
# Table extraction from PDFs (table_extractor.py)
pip install pdfplumber>=0.11

# Audio transcription of meeting recordings (audio_transcriber.py)
# Also requires ffmpeg — install separately: https://ffmpeg.org/download.html
pip install openai-whisper>=20231117

# Doc scan / perspective correction (doc_scanner.py in the doc-scan skill)
pip install opencv-python-headless>=4.9 Pillow>=10.0 numpy>=1.24
pip install img2pdf>=0.5  # optional — for PDF output; Pillow fallback used if absent
```

All dependencies are also listed in `requirements.txt` at the repository root.

### Binary dependencies

| Binary | Required by | How to install |
|---|---|---|
| `ffmpeg` | `audio_transcriber.py` | `brew install ffmpeg` / `apt install ffmpeg` / https://ffmpeg.org/download.html |

### Network access during setup

- **`openai-whisper`** downloads model files from the internet on **first run only** (from OpenAI/HuggingFace servers). Subsequent runs use the cached model at `~/.cache/whisper/`. No network access after that.
- All other scripts and features are fully local after installation.

### Script import verification

| Script | Imports | Third-party? | Network? |
|---|---|---|---|
| `timeline_manager.py` | argparse, json, sys, datetime, pathlib, uuid, collections | None | Never |
| `redactor.py` | argparse, re, sys, pathlib, dataclasses | None | Never |
| `expense_logger.py` | argparse, csv, json, sys, pathlib | None | Never |
| `statement_parser.py` | argparse, csv, json, re, sys, collections, datetime, pathlib | None | Never |
| `report_generator.py` | argparse, json, sys, collections, pathlib | None | Never |
| `utils.py` | re, unicodedata, datetime, pathlib | None | Never |
| `audio_transcriber.py` | argparse, sys, pathlib + **whisper** | **openai-whisper** | First-run model download only |
| `table_extractor.py` | argparse, csv, io, json, sys, pathlib + **pdfplumber** | **pdfplumber** | Never |
| `doc_scanner.py` | argparse, json, sys, time, pathlib + **cv2, numpy, PIL** | **opencv, Pillow, numpy** | Never |

You can verify any script by saying "show me the source of [script name]" — the full file will be displayed.

---

## Privacy & Data Handling

| Aspect | What this skill does |
|---|---|
| **Document content** | Read locally within this session only. Not stored, indexed, or transmitted. |
| **Personal data for form autofill** | Used only to complete the current form. Not written to any file. Not retained after session. |
| **Timeline log** | Opt-in only. You are asked before any entry is written. Entries contain no raw document content — only category-level summaries. |
| **Redacted output files** | Written only to a path you explicitly confirm. |
| **Audio transcripts** | Written to a local file you specify. Model downloads on first Whisper use only. |
| **No telemetry** | This skill has no analytics, usage reporting, or call-home behavior. |

---

## Step 1 — Identify the Mode

### Explicit Mode Selection
If the user clearly states what they want, go directly to the matching mode:

| Mode | User Intent Signals | Typical File Types |
|---|---|---|
| **Document Categorizer** | "process this", "what is this?", "analyze this", "help with this", no clear intent | Any |
| Form Autofill | fill, autofill, fill out, complete this form | PDF form, image, screenshot |
| Contract Analyzer | review, summarize, contract, agreement, risks, red flags | PDF, text |
| Receipt Scanner | receipt, invoice, log expense, scan this bill | Photo, image, PDF |
| Bank Statement Analyzer | bank statement, transactions, subscriptions, categorize spending | PDF, CSV |
| Resume / CV Parser | parse resume, extract cv, what's on this resume, scan resume | PDF, image, text |
| ID & Passport Scanner | scan id, read passport, extract from id card, scan my passport | Photo, image, PDF |
| Medical Summarizer | lab report, blood test, prescription, discharge summary, medical results | PDF, image, text |
| Legal Redactor | redact, remove pii, anonymize, censor sensitive info | PDF, text, image |
| Meeting Minutes | meeting minutes, action items, summarize meeting, transcribe meeting | Text, PDF, image, audio |
| Table Extractor | extract table, table to csv, get data from pdf, table to json | PDF, image, text |
| Document Translator | translate this, translate to [language], document translation | Any document |
| Document Timeline | show my timeline, document history, what have I processed, save timeline | — |
| Doc Scan | scan this photo, make this look scanned, correct perspective, clean this scan | Photo, image |

### Ambiguous Intent → Document Categorizer (with consent gate)

If the user uploads a file without a clear mode signal, **do not read the document yet**. First ask:

> "I can classify this document automatically to suggest the best processing mode — that requires me to read the first 1–2 pages. Alternatively, you can choose directly:
>
> | Option | Best for |
> |---|---|
> | Form Autofill | Forms with fill-in fields |
> | Contract Analyzer | Agreements, NDAs, leases |
> | Receipt Scanner | Receipts, invoices |
> | Bank Statement Analyzer | Bank/credit card statements |
> | Resume Parser | CVs, resumes |
> | ID Scanner | Passports, IDs, driver's licenses |
> | Medical Summarizer | Lab reports, prescriptions, imaging |
> | Legal Redactor | Any document with PII to remove |
> | Meeting Minutes | Notes or recordings |
> | Table Extractor | Documents with data tables |
> | Translator | Non-English documents |
>
> Shall I classify it automatically, or which mode would you like?"

Only read the document after the user says "classify it" / "figure it out" / chooses a mode.

---

## Step 2 — Read the Document

Use the `Read` tool on the uploaded file. For images, read them visually. For PDFs over 10 pages, read in page ranges.

**For audio files (meeting minutes mode only):** confirm before running — this requires `openai-whisper` and downloads a model on first run:

> "Transcribing this audio file requires the `openai-whisper` library. On first use it will download a model file (~140 MB for the default 'base' model) from OpenAI's servers. Is that OK?"

If yes:
```bash
python skills/doc-process/scripts/audio_transcriber.py --file <path> --output transcript.txt
```

If no: ask if the user can provide a text transcript instead.

---

## Step 3 — Execute the Mode

Load and follow the matching reference file in full:

- Document Categorizer → `references/document-categorizer.md`
- Form Autofill → `references/form-autofill.md`
- Contract Analyzer → `references/contract-analyzer.md`
- Receipt Scanner → `references/receipt-scanner.md`
- Bank Statement Analyzer → `references/bank-statement-analyzer.md`
- Resume / CV Parser → `references/resume-parser.md`
- ID & Passport Scanner → `references/id-scanner.md`
- Medical Summarizer → `references/medical-summarizer.md`
- Legal Redactor → `references/legal-redactor.md`
- Meeting Minutes → `references/meeting-minutes.md`
- Table Extractor → `references/table-extractor.md`
- Document Translator → `references/document-translator.md`
- Document Timeline → `references/document-timeline.md`
- Doc Scan → handled by the `doc-scan` skill (separate skill)

---

## Step 4 — Use Helper Scripts

| Script | Deps | Purpose | Example |
|---|---|---|---|
| `scripts/expense_logger.py` | None | Add/list/summarize/edit/delete expense CSV entries | `python scripts/expense_logger.py add --date 2024-03-15 --merchant "Starbucks" --amount 13.12 --file expenses.csv` |
| `scripts/statement_parser.py` | None | Parse a bank CSV export and categorize transactions | `python scripts/statement_parser.py --file statement.csv --output categorized.json` |
| `scripts/report_generator.py` | None | Format categorized JSON into a markdown report | `python scripts/report_generator.py --file categorized.json --type bank` |
| `scripts/redactor.py` | None | Regex-based PII redaction on text files | `python scripts/redactor.py --file document.txt --output redacted.txt --mode full` |
| `scripts/timeline_manager.py` | None | Manage the opt-in document processing timeline | `python scripts/timeline_manager.py show` |
| `scripts/audio_transcriber.py` | **openai-whisper, ffmpeg** | Transcribe audio files to text | `python scripts/audio_transcriber.py --file meeting.mp3 --output transcript.txt` |
| `scripts/table_extractor.py` | **pdfplumber** | Extract tables from PDFs to CSV or JSON | `python scripts/table_extractor.py --file document.pdf --output data.csv` |

Scripts with no declared deps use only Python stdlib. Scripts with declared deps check for the library at import time and print a clear install instruction if it is missing.

---

## Step 5 — Document Timeline (Opt-In)

The timeline is off by default. Do not run `timeline_manager.py add` until the user has explicitly said yes to the consent prompt.

### Consent prompt (first document in a session)
After completing the first document task, ask once:

> "Would you like me to keep a processing log for this session? It records document type, filename, and a category-level summary (no raw content, no personal data) to `~/.doc-process-timeline.json` on your local machine. Entirely optional — yes or no."

- **Yes** → confirm "Timeline logging is on." Log the current document and subsequent ones. Announce each with "Logged to your timeline."
- **No** → confirm "No log will be kept." Do not run any timeline script. Do not ask again this session.
- **No response / unsure** → treat as no.

### Summary rules (enforced)
The `--summary` argument must not contain names, ID numbers, dates of birth, addresses, account numbers, card numbers, medical values, or any data that could identify a person. Use category-level descriptions only.

---

## Step 6 — Deliver Output

Present output in clean tables with section headers as specified in each reference file. Always end with an action prompt relevant to the mode.

---

## General Principles

- **Categorize before asking** — but only after confirming the user wants auto-classification.
- **Never hallucinate field values.** Unknown values are marked [MISSING] or [UNREADABLE].
- **Flag risks conservatively**: when in doubt, include it.
- **Keep summaries scannable** with tables and bullets.
- **Do not echo sensitive data** beyond what is necessary for the immediate task.
- **Always include relevant disclaimers** (medical, legal, privacy) where required by the reference guide.
- **Timeline is opt-in per session.** Never log without confirmed consent.
- **Personal data for form autofill is session-only.** Never write it to a file.
- **Before running any script with third-party deps**, confirm the user has the library installed or is willing to install it.
