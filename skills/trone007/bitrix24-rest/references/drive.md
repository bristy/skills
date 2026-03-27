# Drive and Disk

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation.

Cloud storage for files, folders, and external links. Manages uploads, downloads, and folder hierarchy.

## Endpoints

| Action | Command |
|--------|---------|
| List files | `vibe.py --raw GET /v1/drive/files --json` |
| Get file | `vibe.py --raw GET /v1/drive/files/123 --json` |
| Upload file | `vibe.py --raw POST /v1/drive/files --body '{"folderId":1,"name":"doc.pdf","content":"base64..."}' --confirm-write --json` |
| Get folder | `vibe.py --raw GET /v1/drive/folders/123 --json` |
| Create folder | `vibe.py --raw POST /v1/drive/folders --body '{"parentId":1,"name":"New Folder"}' --confirm-write --json` |

## Key Fields (camelCase)

- `id` — file or folder ID
- `name` — file or folder name
- `folderId` — parent folder ID
- `parentId` — parent folder ID (for folder creation)
- `size` — file size in bytes
- `downloadUrl` — authenticated download link
- `content` — base64-encoded file content (for upload)
- `createdBy` — user ID of creator
- `updatedAt` — last modification timestamp

## Copy-Paste Examples

### List all files

```bash
vibe.py --raw GET /v1/drive/files --json
```

### Get file metadata

```bash
vibe.py --raw GET /v1/drive/files/9043 --json
```

### Upload a file to a folder

```bash
vibe.py --raw POST /v1/drive/files --body '{
  "folderId": 42,
  "name": "report.pdf",
  "content": "base64_encoded_content_here"
}' --confirm-write --json
```

### Browse folder contents

```bash
vibe.py --raw GET /v1/drive/folders/42 --json
```

### Create a subfolder

```bash
vibe.py --raw POST /v1/drive/folders --body '{
  "parentId": 42,
  "name": "Q1 Reports"
}' --confirm-write --json
```

## Common Pitfalls

- `downloadUrl` requires authentication — it is not a public link. Use external link endpoints for sharing.
- File uploads use base64 encoding — large files may hit POST size limits (~30 MB after encoding).
- Always get file metadata before attempting download or move operations.
- Folder IDs from the root level may differ per user — list storages first to find the correct root.
- Deleting files/folders may be permanent — verify before using delete endpoints.
