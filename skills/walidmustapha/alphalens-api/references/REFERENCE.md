# AlphaLens API Reference

**Note:** This skill requires an active [AlphaLens subscription](https://alphalens.ai) with API access.

## Authentication

Default to API key authentication:

```http
API-Key: <ALPHALENS_API_KEY>
```

Bearer auth exists in the API, but API key auth is the preferred default for agent workflows.

## Base URLs

- Production: `https://api-production.alphalens.ai`
- Public docs: `https://api-production.alphalens.ai/docs`
- Public OpenAPI: `https://api-production.alphalens.ai/openapi.json`

## General Guidance

- Start with the public OpenAPI when you need contract details.
- Prefer narrow reads before writes.
- If the user already provides a known company or domain, resolve the company and use the similar organizations endpoint.
- If the question is product-led, prefer product endpoints. Product search usually yields better precision than organization search for detailed categories, features, and use cases.
- Similarity endpoints are ID-anchored; resolve the source entity before calling them.
- Searches, reads, and enrichment can be credit- and policy-gated. Avoid repeated or unnecessary requests.

## Which Endpoint Does What

- `GET /api/v1/entities/organizations/search-by-name/{organization_name}`
  resolves a company name into candidate organizations
- `GET /api/v1/entities/organizations/by-domain/{domain}`
  resolves a known company domain into a specific organization
- `GET /api/v1/entities/organizations/{organization_id}`
  fetches full organization details
- `GET /api/v1/search/organizations/{organization_id}/similar`
  finds organizations similar to a known reference organization
- `GET /api/v1/search/organizations/search`
  performs free-text organization discovery by description
- `GET /api/v1/search/organizations/search-customers`
  performs organization discovery by customer-base description
- `GET /api/v1/search/products/search`
  performs free-text product discovery by product description
- `GET /api/v1/search/products/search-customers`
  performs product discovery by customer-base or target-user description
- `GET /api/v1/search/products/{product_id}/similar`
  finds products similar to a known reference product
- `GET /api/v1/pipelines/{pipeline_id}/organizations`
  adds an organization to a pipeline
- `GET /api/v1/pipelines/{pipeline_id}/items`
  lists pipeline items with values
- `GET /api/v1/pipelines/{pipeline_id}/items/{pipeline_item_id}/status`
  checks if pipeline item values are ready
- `GET /api/v1/pipelines/{pipeline_id}/items/{pipeline_item_id}/values`
  reads final pipeline item values

## Search Strategy

### Use direct similarity when the reference company is known

Good examples:

- "Find companies similar to Ramp"
- "Show competitors to Brex"
- "Find companies like Rippling"

Recommended flow:

1. Resolve the company by domain or name
2. Call `GET /api/v1/search/organizations/{organization_id}/similar`

### Prefer product search for precise market mapping

Product search is usually the better choice when the user is really asking about:

- product categories
- feature sets
- workflows
- target users
- competitive products

Examples:

- "Find products similar to Gong for mid-market sales teams"
- "Find AP automation products for finance teams"
- "Find developer tools for LLM observability"

If the end goal is still a company list, you can search products first and then roll results up to their organizations.

## Core Read Workflows

### 1. Resolve organizations before ID-anchored searches

Useful endpoints:

- `GET /api/v1/entities/organizations/search-by-name/{organization_name}`
- `GET /api/v1/entities/organizations/by-domain/{domain}`
- `GET /api/v1/entities/organizations/{organization_id}`

Use these when a user gives you a company name or domain and you need an `organization_id`.

### 2. Resolve products or fetch product detail

Useful endpoints:

- `GET /api/v1/entities/products/{product_id}`
- `GET /api/v1/entities/products/by-domain/{domain}`

Use these when you need a product detail fetch or product list for a known company domain.

## Search Endpoints

All search endpoints support filters for location, company age/size, product categories, and funding. See `EXAMPLES.md` for the full filter reference.

### Organization discovery

- Description search:
  `GET /api/v1/search/organizations/search`
- Customer-base search:
  `GET /api/v1/search/organizations/search-customers`
- Similar organizations:
  `GET /api/v1/search/organizations/{organization_id}/similar`
- Location suggestions:
  `GET /api/v1/search/locations/suggest`
- Location metadata:
  `GET /api/v1/search/locations/metadata`

### Product discovery

- Description search:
  `GET /api/v1/search/products/search`
- Customer-base search:
  `GET /api/v1/search/products/search-customers`
- Similar products:
  `GET /api/v1/search/products/{product_id}/similar`

## Pipeline Workflows

Use pipelines for list building, enrichment, and async processing.

### Add organizations to a pipeline

1. Use `POST /api/v1/pipelines/{pipeline_id}/organizations` to add an organization:

```http
POST /api/v1/pipelines/{pipeline_id}/organizations
API-Key: <ALPHALENS_API_KEY>
Content-Type: application/json

{
  "organization_id": 123
}
```

### Read pipeline items

1. List pipeline items:
   `GET /api/v1/pipelines/{pipeline_id}/items`

2. Poll readiness:
   `GET /api/v1/pipelines/{pipeline_id}/items/{pipeline_item_id}/status`

3. Read values when ready:
   `GET /api/v1/pipelines/{pipeline_id}/items/{pipeline_item_id}/values`

### Pipeline item readiness

- Do not assume item values are ready immediately after adding an organization.
- Poll the item status endpoint until `is_ready` is true before treating values as final.

## Heuristics

- If the user asks "find companies like X", resolve `X` to an organization, then use the similar organizations endpoint.
- If the user asks for a competitive landscape around a known company, use direct similarity.
- If the user asks "find products for this market", use the product search endpoints.
- If the user's wording is product-led, prefer product search over organization search.
- If the user gives a domain, prefer by-domain resolution over fuzzy name matching.