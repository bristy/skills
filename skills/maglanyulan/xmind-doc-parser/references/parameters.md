# Baidu Document Parser Parameters Detail

## Overview

Baidu Document Parser API supports parsing of 18+ document formats including PDF, Word, Excel, PowerPoint, and images. It extracts text, tables, layout information, and supports OCR for scanned documents.

## API Endpoints

### Submit Task
```
POST https://aip.baidubce.com/rest/2.0/brain/online/v2/parser/task?access_token={access_token}
```

### Query Task
```
POST https://aip.baidubce.com/rest/2.0/brain/online/v2/parser/task/query?access_token={access_token}
```

## Request Parameters

### File Parameters (Required, choose one)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_url | string | No* | Document URL (publicly accessible, max 1024 bytes) |
| file_data | string | No* | Base64-encoded file data |
| file_name | string | Yes | File name with extension |

*Must provide one of file_url or file_data

### Core Function Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| recognize_formula | bool | false | Recognize formulas in documents |
| analysis_chart | bool | false | Parse statistical charts |
| angle_adjust | bool | false | Auto-rotate images |
| parse_image_layout | bool | false | Return image position information |

### Language and Format Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| language_type | string | CHN_ENG | Recognition language |
| switch_digital_width | string | auto | Number width conversion (auto/half/full) |
| html_table_format | bool | true | Return tables in HTML format |

### Language Types

Supported languages:
- CHN_ENG: Chinese and English
- JAP: Japanese
- KOR: Korean
- FRE: French
- SPA: Spanish
- POR: Portuguese
- GER: German
- ITA: Italian
- RUS: Russian
- DAN: Danish
- DUT: Dutch
- MAL: Malay
- SWE: Swedish
- IND: Indonesian
- POL: Polish
- ROM: Romanian
- TUR: Turkish
- GRE: Greek
- HUN: Hungarian
- THA: Thai
- VIE: Vietnamese
- ARA: Arabic
- HIN: Hindi

### Advanced Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| version | string | v2 | API version |
| need_inner_image_data | bool | false | Include internal image data |
| merge_tables | bool | false | Merge related tables |
| relevel_titles | bool | false | Restructure title hierarchy |
| recognize_seal | bool | false | Recognize document seals |
| return_span_boxes | bool | false | Return span bounding boxes |

### Document Chunking Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| return_doc_chunks | object | null | Document chunking configuration |
| return_doc_chunks.switch | bool | false | Enable chunking |
| return_doc_chunks.split_type | string | chunk | Chunking method (chunk/mark) |
| return_doc_chunks.separators | array | ['。', '；', ...] | Punctuation for splitting |
| return_doc_chunks.chunk_size | int | -1 | Chunk size (-1 for auto) |

## Response Structure

### Submit Task Response

```json
{
  "error_code": 0,
  "error_msg": "",
  "result": {
    "task_id": "task-xxxxx"
  }
}
```

### Query Task Response

```json
{
  "error_code": 0,
  "error_msg": "",
  "result": {
    "task_id": "task-xxxxx",
    "status": "success",
    "file_name": "document.pdf",
    "file_id": "file-xxxxx",
    "pages": [...],
    "chunks": [...],
    "parse_result_url": "https://...",
    "markdown_url": "https://..."
  }
}
```

### Status Values

- `running`: Task is processing
- `success`: Task completed successfully
- `failed`: Task failed

### Page Object

```json
{
  "page_id": "page-xxxxx",
  "page_num": 1,
  "text": "All text content on this page",
  "layouts": [...],
  "tables": [...],
  "images": [...]
}
```

### Layout Types

- `title`: Title (with sub_type: title_1, title_2, title_3, etc.)
- `para`: Paragraph
- `table`: Table
- `image`: Image
- `head_tail`: Header/footer
- `contents`: Table of contents
- `seal`: Seal/stamp
- `formula`: Mathematical formula

## File Limits

- **URL mode**: PDF up to 300MB, others up to 50MB
- **Base64 mode**: Up to 50MB
- **Page limit**: PDF up to 2000 pages, others up to 200 pages
- **URL length**: Max 1024 bytes

## QPS Limits

- Submit request: 2 QPS
- Query result: 10 QPS

## Polling Recommendations

- Start polling 5-10 seconds after submission
- Polling interval: 5 seconds
- Maximum polling time: 300 seconds

## Related Documentation

- [Official API Documentation](https://ai.baidu.com/ai-doc/OCR/llxst5nn0)
- [Error Codes Reference](error_codes.md)