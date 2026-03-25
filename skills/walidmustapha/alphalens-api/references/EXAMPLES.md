# AlphaLens API Examples

**Note:** This skill requires an active [AlphaLens subscription](https://alphalens.ai) with API access.

## Example Prompts

- `Research the competitive landscape around zoominfo.com using AlphaLens.`
- `Find vertical SaaS companies serving private equity firms.`
- `Find products similar to Gong for mid-market sales teams.`
- `Build a target list of AI procurement startups and enrich it in a pipeline.`
- `Resolve Ramp by domain, find similar companies, and summarize the overlap.`

## Organization Search Examples

Use free-text search for open-ended market discovery prompts:

- `Find fintech infrastructure companies in the US founded after 2019.`
- `Find AI procurement startups in Europe.`
- `Find products for finance teams that automate AP workflows.`

```http
GET /api/v1/search/organizations/search?description=fintech%20infrastructure&year_founded_min=2020&country_keys=US
API-Key: <ALPHALENS_API_KEY>
```

## Known-Company Similarity Example

If the user already gives a known company, direct similarity is the best approach.

Example prompt:

- `Find companies similar to Ramp.`

Recommended flow:

1. Resolve the company directly:

```http
GET /api/v1/entities/organizations/by-domain/ramp.com
API-Key: <ALPHALENS_API_KEY>
```

2. Use the returned `organization_id`:

```http
GET /api/v1/search/organizations/123/similar
API-Key: <ALPHALENS_API_KEY>
```

## Product-Led Search Example

Product-level search usually performs better for precise category, feature, and use-case mapping.

Example prompt:

- `AI for retinal scanning to detect cancer`

Recommended path:

```http
GET /api/v1/search/products/search?description=AI%20for%20retinal%20scanning%20to%20detect%20cancer
API-Key: <ALPHALENS_API_KEY>
```

If you already have a known `product_id`, use:

```http
GET /api/v1/search/products/123/similar
API-Key: <ALPHALENS_API_KEY>
```

## Search Filters

All search endpoints (`/api/v1/search/organizations/search`, `/api/v1/search/organizations/search-customers`, `/api/v1/search/products/search`, `/api/v1/search/products/search-customers`, and similarity endpoints) support the following filters:

### Location Filters

| Parameter | Type | Description |
|-----------|------|-------------|
| `country_keys` | string[] | Country codes (ISO 3166-1 alpha-2). Example: `["US", "GB"]` |
| `region_keys` | string[] | States/regions. Example: `["NEW_YORK-US", "CALIFORNIA-US"]` |
| `is_headquarters` | boolean | Filter for headquarters locations only (default: true) |

### Company Age & Size Filters

| Parameter | Type | Description |
|-----------|------|-------------|
| `year_founded_min` | integer | Minimum year founded |
| `year_founded_max` | integer | Maximum year founded |
| `employee_count_range_min` | integer | Minimum employee count |
| `employee_count_range_max` | integer | Maximum employee count |

### Product & Funding Filters

| Parameter | Type | Description |
|-----------|------|-------------|
| `product_categories` | enum[] | Filter by product categories: `goods`, `services`, `software`, `hardware` |
| `latest_funding_round` | enum[] | Filter by funding stages: `pre_seed/angel`, `seed`, `series_a`, `series_b`, `series_c`, `series_d`, `series_e`, `series_f`, `series_g`, `series_h`, `series_i`, `series_j`, `series_other`, `convertible_note`, `corporate_round`, `debt_financing`, `crowdfunding`, `grant_equity`, `grant_other`, `post_ipo`, `private_equity`, `secondary_market`, `initial_coin_offering`, `other` |
| `has_funding` | boolean | Filter by whether the entity has received any funding |
| `raised_date_from` | date | Filter funding rounds raised on or after this date (ISO format: YYYY-MM-DD) |
| `raised_date_to` | date | Filter funding rounds raised on or before this date (ISO format: YYYY-MM-DD) |

### Pagination

| Parameter | Type | Description |
|-----------|------|-------------|
| `skip` | integer | Starting offset for pagination (default: 0) |
| `limit` | integer | Number of records to return. Maximum page size is 100 (default: 24) |

## Example Similar Organization Flow

1. Resolve the source company:

```http
GET /api/v1/entities/organizations/by-domain/ramp.com
API-Key: <ALPHALENS_API_KEY>
```

2. Use the returned `organization_id`:

```http
GET /api/v1/search/organizations/123/similar
API-Key: <ALPHALENS_API_KEY>
```

## Example Pipeline Flow

1. Add an organization to a pipeline:

```http
POST /api/v1/pipelines/42/organizations
API-Key: <ALPHALENS_API_KEY>
Content-Type: application/json
```

```json
{
  "organization_id": 123
}
```

2. Poll readiness:

```http
GET /api/v1/pipelines/42/items/999/status
API-Key: <ALPHALENS_API_KEY>
```

3. Read final values:

```http
GET /api/v1/pipelines/42/items/999/values
API-Key: <ALPHALENS_API_KEY>
```