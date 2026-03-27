# File Uploads

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation.

File upload strategies for Vibe Platform. The approach depends on the target entity and file size.

## Upload Strategies

| Strategy | Use Case | How |
|----------|----------|-----|
| Base64 inline | Small files for CRM attachments | Encode file as base64, pass in request body |
| Disk upload + attach | Task files, chat files | Upload to Drive first, then attach by file ID |
| Multipart upload | Large files (if supported) | Send as multipart/form-data |

## Strategy 1: Base64 Inline (CRM Attachments)

Best for small files attached to CRM entities (leads, deals, contacts, companies).

### Encode and attach to a CRM entity

```bash
# Encode file to base64
B64=$(python3 -c "import base64, sys; print(base64.b64encode(open(sys.argv[1],'rb').read()).decode())" /path/to/photo.jpg)

# Attach to a contact
vibe.py --raw POST /v1/crm/contacts/123 --body "{
  \"photo\": [\"photo.jpg\", \"$B64\"]
}" --confirm-write --json
```

### Multiple files in a user field

Use `--body` with a JSON file for complex payloads:

```json
{
  "fields": {
    "ufCrmFiles": [
      ["doc1.pdf", "<base64>"],
      ["doc2.pdf", "<base64>"]
    ]
  }
}
```

## Strategy 2: Disk Upload + Attach (Tasks)

Tasks do not accept base64 directly. Upload to Drive first, then attach the file ID.

### Step 1: Upload file to Drive

```bash
B64=$(python3 -c "import base64, sys; print(base64.b64encode(open(sys.argv[1],'rb').read()).decode())" /path/to/report.pdf)

vibe.py --raw POST /v1/drive/files --body "{
  \"folderId\": 42,
  \"name\": \"report.pdf\",
  \"content\": \"$B64\"
}" --confirm-write --json
```

The response contains the file object with `id`.

### Step 2: Attach to task

```bash
vibe.py --raw POST /v1/tasks/456/files --body '{
  "fileId": 789
}' --confirm-write --json
```

## Strategy 3: Multipart Upload (If Supported)

For large files, multipart/form-data may be supported. This avoids base64 overhead (33% size increase).

```bash
# Check if multipart is supported at runtime
# Conceptual — verify actual endpoint and content-type support
curl -X POST /v1/drive/files \
  -F "folderId=42" \
  -F "file=@/path/to/large-file.zip"
```

## When to Use Which Strategy

| Entity | Strategy | Notes |
|--------|----------|-------|
| CRM lead/deal/contact/company | Base64 inline | Pass `["name", "base64"]` in field |
| Task | Disk + attach | Upload to Drive, then attach file ID |
| Chat message | Disk + commit | Upload to Drive, then send in chat |
| Feed post | Disk + attach | Upload first, reference Drive file ID |

## Key Fields (camelCase)

- `folderId` — target folder for Drive uploads
- `name` — filename with extension
- `content` — base64-encoded file content
- `fileId` — Drive file ID (for attaching)

## Common Pitfalls

- Base64 encoding adds ~33% size overhead — a 30 MB file becomes ~40 MB encoded.
- POST size limits apply: typically ~30 MB after encoding for inline uploads.
- Tasks reject inline base64 — always use the two-step Disk upload approach.
- Always include the file extension in the `name` field for correct MIME detection.
- Portal disk quota applies to all uploads — check available space for large batches.
