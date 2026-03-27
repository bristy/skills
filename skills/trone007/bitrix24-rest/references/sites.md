# Landing Pages and Sites

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation.

Creating and managing Bitrix24 sites and landing pages, including page management and publishing.

## Endpoints

| Action | Command |
|--------|---------|
| List sites | `vibe.py --raw GET /v1/sites --json` |
| Get site | `vibe.py --raw GET /v1/sites/123 --json` |
| Get pages | `vibe.py --raw GET /v1/sites/123/pages --json` |
| Publish | `vibe.py --raw POST /v1/sites/123/publish --confirm-write --json` |

## Key Fields (camelCase)

Site fields:

- `id` — site ID
- `title` — site title
- `code` — URL slug
- `domainId` — associated domain ID
- `publicUrl` — published URL
- `active` — whether the site is published

Page fields:

- `id` — page ID
- `siteId` — parent site ID
- `title` — page title
- `code` — URL slug for the page
- `active` — whether the page is published

## Copy-Paste Examples

### List all sites

```bash
vibe.py --raw GET /v1/sites --json
```

### Get site details

```bash
vibe.py --raw GET /v1/sites/292 --json
```

### Get pages of a site

```bash
vibe.py --raw GET /v1/sites/292/pages --json
```

### Publish a site

```bash
vibe.py --raw POST /v1/sites/292/publish --confirm-write --json
```

## Common Pitfalls

- Publishing affects the live site immediately — verify content before publishing.
- Site pages are managed under the site's `/pages` sub-resource.
- Block-level editing (adding/updating visual blocks on pages) may require separate endpoints — verify at runtime.
- Domain configuration is separate from site creation — check domain settings first.
- Unpublishing may require a separate endpoint or method — verify at runtime.
