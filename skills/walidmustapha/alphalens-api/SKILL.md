---
name: alphalens-api
description: Use the AlphaLens API for organization and product discovery and pipeline workflows. Use when the user wants to query AlphaLens data, find similar companies or products, build target lists, enrich pipeline items, or integrate against the AlphaLens API. Requires an AlphaLens subscription with API access.
metadata:
  {
    "openclaw":
      {
        "requires": { "env": ["ALPHALENS_API_KEY"] },
        "primaryEnv": "ALPHALENS_API_KEY",
        "homepage": "https://alphalens.ai"
      }
  }
---

# AlphaLens API

**Note:** This skill requires an active [AlphaLens subscription](https://alphalens.ai) with API access. Contact sales@alphalens.ai for enterprise pricing.

## Authentication

- Prefer API key auth.
- Expect `ALPHALENS_API_KEY` to be available.
- Send `API-Key: <value>` on requests.
- Bearer auth also exists, but use API keys unless the user explicitly asks for bearer tokens.

## Base URLs

- Production: `https://api-production.alphalens.ai`
- Public OpenAPI: `https://api-production.alphalens.ai/openapi.json`
- Public docs: `https://api-production.alphalens.ai/docs`

## Working Rules

- Treat the live OpenAPI and endpoint responses as the source of truth.
- If the user already gives a known company, resolve the company first, then use the similar organizations endpoint.
- If the user already gives a known domain, prefer by-domain resolution over free-text search.
- Product-level search usually performs better than organization-level search for precise market/category matching. Prefer product search when the user is asking about products, use cases, features, or competitive product landscapes.
- Resolve company names or domains before ID-anchored similarity searches.
- Be careful with policy-, quota-, and credit-gated endpoints. Avoid broad fan-out without a clear reason.

## Choose The Right Search Path

- Known company or domain:
  resolve the organization, then call `GET /api/v1/search/organizations/{organization_id}/similar`.
- Known product or product-led market thesis:
  prefer the product search endpoints, especially `GET /api/v1/search/products/search` or `GET /api/v1/search/products/{product_id}/similar`.
- Free-text market discovery:
  use `GET /api/v1/search/organizations/search` or `GET /api/v1/search/products/search`.
- Do not turn "Find companies similar to Ramp" into a free-text search if you can resolve Ramp directly.

## Default Workflow

### Research companies similar to a known company

1. If the user gives a domain, call `GET /api/v1/entities/organizations/by-domain/{domain}`.
2. If the user gives a name, call `GET /api/v1/entities/organizations/search-by-name/{organization_name}` and choose the best match.
3. Use the resolved `organization_id` with `GET /api/v1/search/organizations/{organization_id}/similar`.
4. Use detail endpoints only for shortlisted results.

### Research products from a prompt

1. Prefer product search if the user's intent is product-led, even if the end goal is a company list.
2. Use the product search endpoints:
   - `GET /api/v1/search/products/search`
   - `GET /api/v1/search/products/search-customers`
   - `GET /api/v1/search/products/{product_id}/similar`
3. Fetch product details only when needed.

### Build or enrich a pipeline

1. Use `GET /api/v1/pipelines/{pipeline_id}/items` to inspect existing pipeline items.
2. Add organizations to a pipeline with `POST /api/v1/pipelines/{pipeline_id}/organizations`.
3. Poll pipeline item status with `GET /api/v1/pipelines/{pipeline_id}/items/{pipeline_item_id}/status`.
4. Read final values with `GET /api/v1/pipelines/{pipeline_id}/items/{pipeline_item_id}/values`.

## Endpoint Priorities

- Use direct resolution plus similarity for known companies.
- Use product search first when the question is really about products, categories, features, or use cases.
- Use public search endpoints for discovery.
- Use entity endpoints for detail fetches.
- Use pipeline endpoints for enrichment workflows.

## References

- For endpoint mapping and workflow details, see [references/REFERENCE.md](references/REFERENCE.md).
- For example prompts and request shapes, see [references/EXAMPLES.md](references/EXAMPLES.md).