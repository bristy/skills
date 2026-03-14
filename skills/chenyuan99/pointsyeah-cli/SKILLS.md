# Skills / Usage

This repo provides a small CLI called **`pointsyeah`** that generates **PointsYeah** search URLs for flights and hotels.

It does **not** scrape PointsYeah and does **not** call a private API; it only produces a best-effort deep link you can open in a browser.

## Install (uv)

```bash
uv pip install -e .
```

Or install as a tool:

```bash
uv tool install -e .
```

## Commands

### Flights

```bash
pointsyeah flights JFK LAX --date 2026-04-10
pointsyeah flights JFK LAX --date 2026-04-10 --return 2026-04-15 --adults 2 --cabin business
pointsyeah flights JFK LAX --date 2026-04-10 --open
```

### Hotels

```bash
pointsyeah hotels "Jersey City" --checkin 2026-04-10 --checkout 2026-04-12
pointsyeah hotels "Boston" --checkin 2026-05-01 --checkout 2026-05-05 --guests 2 --rooms 1 --open
```

## Development

Run tests:

```bash
uv pip install -e .
uv pip install pytest
pytest -q
```
