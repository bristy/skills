---
name: baidu-doc-parser
description: Parse documents using Baidu Document Parser API. Supports PDF, Word, Excel, PowerPoint, images and 18+ formats. Extracts text, tables, layout analysis, OCR, and document chunks for RAG. Use when users need to parse documents, extract text/tables, analyze document structure, or process scanned documents. Trigger words: document parsing, PDF parsing, Word parsing, table extraction, OCR, document analysis, extract text, document structure.
license: MIT
---

# Baidu Document Parser Skill

Parse documents using Baidu Intelligent Document Analysis Platform API.

## Overview

This skill provides document parsing capabilities through Baidu's Document Parser API, supporting:
- 18+ document formats (PDF, Word, Excel, PowerPoint, images, etc.)
- Text extraction
- Table recognition and extraction
- Layout analysis (titles, paragraphs, headers/footers, etc.)
- OCR for scanned documents
- Document chunking for RAG applications
- Multi-language support (Chinese, English, Japanese, Korean, French, German, etc.)

## When to Use

Use this skill when users need to:
- Parse PDF, Word, Excel, or other document formats
- Extract text content from documents
- Recognize and extract tables
- Analyze document structure (titles, sections, layout)
- Process scanned documents with OCR
- Chunk documents for RAG applications

## API Configuration

### Environment Variables (Required)

Set these before using the skill:

```bash
export BAIDU_DOC_AI_API_KEY="your_api_key"
export BAIDU_DOC_AI_SECRET_KEY="your_secret_key"
```

### Authentication

The skill uses OAuth 2.0 to obtain an access token automatically. Token is valid for 30 days.

## Supported Formats

**Documents**: pdf, doc, docx, xls, xlsx, ppt, pptx, wps, et, dps, csv, txt, html, mhtml, ofd

**Images**: jpg, jpeg, png, bmp, tiff, tif

**Total**: 18+ formats

## Supported Languages

Chinese, English, Japanese, Korean, French, German, Italian, Portuguese, Spanish, Russian, Dutch, Swedish, Finnish, Danish, Norwegian, Hungarian, Turkish, Polish, Czech, Greek, and more (20+ languages)

## Usage

### Basic Usage

```bash
python3 scripts/baidu_doc_parser.py --file_data <文件的base64编码> 
python3 scripts/baidu_doc_parser.py --file_url <文件数据URL> 
```

## API Parameters

### File Parameters (Required, choose one)

- `file_url` (string): Document URL (publicly accessible)
- `file_data` (string): Base64-encoded file data
- `file_name` (string, required): File name with extension

### Core Function Parameters

- `recognize_formula` (bool): Recognize formulas in documents (default: false)
- `analysis_chart` (bool): Parse statistical charts (default: false)
- `angle_adjust` (bool): Auto-rotate images (default: false)
- `parse_image_layout` (bool): Return image position info (default: false)

### Language and Format Parameters

- `language_type` (string): Recognition language (default: "CHN_ENG")
  - Options: CHN_ENG, JAP, KOR, FRE, SPA, POR, GER, ITA, RUS, DAN, DUT, MAL, SWE, IND, POL, ROM, TUR, GRE, HUN, THA, VIE, ARA, HIN
- `switch_digital_width` (string): Convert number width (default: "auto")
  - Options: "auto" (no conversion), "half" (half-width), "full" (full-width)
- `html_table_format` (bool): Return tables in HTML format (default: true)

### Advanced Parameters

- `version` (string): API version (default: "v2")
- `need_inner_image_data` (bool): Include internal image data
- `merge_tables` (bool): Merge related tables
- `relevel_titles` (bool): Restructure title hierarchy
- `recognize_seal` (bool): Recognize document seals/stamps
- `return_span_boxes` (bool): Return span bounding boxes

### Document Chunking Parameters

- `return_doc_chunks` (dict): Document chunking configuration
  - `switch` (bool): Enable chunking (default: false)
  - `split_type` (string): Chunking method - "chunk" (by size) or "mark" (by punctuation)
  - `separators` (list): Punctuation marks for splitting (default: ['。', '；', '！', '？', ';', '!', '?'])
  - `chunk_size` (int): Chunk size in characters (default: -1 for auto)

## Return Structure

### Page Object

Each page contains:
- `page_id`: Page identifier
- `page_num`: Page number
- `text`: All text content on the page
- `layouts`: Layout elements (titles, paragraphs, tables, images, etc.)
- `tables`: Extracted tables
- `images`: Extracted images

### Layout Types

- `title`: Title (with sub_type: title_1, title_2, title_3, etc.)
- `para`: Paragraph
- `table`: Table
- `image`: Image
- `head_tail`: Header/footer
- `contents`: Table of contents
- `seal`: Seal/stamp
- `formula`: Mathematical formula

### Table Object

- `layout_id`: Table identifier
- `markdown`: Table content in Markdown format
- `position`: Bounding box [x, y, width, height]
- `cells`: Cell information
- `matrix`: Cell index matrix (for merged cells)

### Chunk Object

- `chunk_id`: Chunk identifier
- `content`: Chunk content
- `type`: Chunk type ("text" or "table")
- `meta`: Metadata (titles, position, page number)

## API Characteristics

### Asynchronous Processing

Document parsing is asynchronous:
1. Submit request → Get `task_id`
2. Poll for results using `task_id`

### Polling Recommendations

- Start polling 5-10 seconds after submission
- Polling interval: 5 seconds
- Maximum polling time: 300 seconds

### QPS Limits

- Submit request API: 2 QPS
- Query result API: 10 QPS

## File Limits

- **File size**:
  - URL mode: PDF up to 300MB, others up to 50MB
  - Base64 mode: Up to 50MB
- **Page limit**: Up to 2000 pages for PDF, 200 for others
- **Formats**: 18+ supported formats

## Error Handling

Common error codes:

| Code | Message | Solution |
|------|---------|----------|
| 110/111 | Access token invalid/expired | Re-obtain access token |
| 216200 | Empty file or URL | Provide file_data or file_url |
| 216201 | File format error | Check file format |
| 216202 | File size error | Reduce file size |
| 282000 | Internal error | Retry or contact support |
| 282003 | Missing parameters | Check required parameters |
| 282007 | Task not exist | Check task_id |
| 282018 | Service busy | Reduce request frequency |

For complete error codes, see `references/error_codes.md`

## Scripts

The skill includes Python scripts for document parsing:

- `scripts/baidu_doc_parser.py`: Main client library
- Command-line interface for quick testing

## References

- `references/api_reference.md`: Complete API documentation
- `references/error_codes.md`: Full error code reference

## Related Links

- [Official API Documentation](https://ai.baidu.com/ai-doc/OCR/llxst5nn0)
- [Baidu Cloud Console](https://console.bce.baidu.com/ai/)