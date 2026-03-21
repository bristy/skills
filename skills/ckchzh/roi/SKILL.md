---
name: roi
version: "1.0.0"
description: "Calculate and compare return on investment across projects using financial models. Use when evaluating investment decisions."
author: BytesAgain
homepage: https://bytesagain.com
source: https://github.com/bytesagain/ai-skills
tags: [roi, investment, finance, returns, analysis, comparison]
---

# ROI — Return on Investment Calculator

Calculate ROI for investments, compare multiple opportunities side-by-side, forecast returns over time, annualize returns for fair comparison, run scenario analysis (best/worst/expected), and maintain an investment history. Essential for investors, business analysts, product managers evaluating feature ROI, and anyone making data-driven investment decisions.

## Prerequisites

- Python 3.8+
- `bash` shell

## Data Storage

All investment records and calculations are stored in `~/.roi/data.jsonl` as newline-delimited JSON. Each record includes investment details, calculation results, scenarios, and timestamps.

Configuration is stored in `~/.roi/config.json`.

## Commands

### `calculate`
Calculate ROI from initial investment and final value (or gain). Returns ROI percentage, net gain, and summary.

```
ROI_INVESTMENT=10000 ROI_RETURN=15000 bash scripts/script.sh calculate
```

### `compare`
Compare ROI across multiple stored investments. Ranks by ROI percentage, annualized return, or absolute gain. Displays a comparison table.

```
ROI_SORT_BY=annualized bash scripts/script.sh compare
```

### `forecast`
Forecast future value of an investment given an expected annual return rate over a specified number of years. Supports simple and compound interest.

```
ROI_INVESTMENT=10000 ROI_RATE=0.08 ROI_YEARS=10 ROI_MODEL=compound bash scripts/script.sh forecast
```

### `annualize`
Convert a total ROI over any holding period into an annualized return rate for fair comparison across investments of different durations.

```
ROI_TOTAL_RETURN=0.45 ROI_YEARS=3.5 bash scripts/script.sh annualize
```

### `project`
Create or update an investment project record. Tracks name, initial investment, current value, start date, and category.

```
ROI_NAME="Tech ETF" ROI_INVESTMENT=5000 ROI_CURRENT_VALUE=6200 ROI_START_DATE="2023-06-01" ROI_CATEGORY="stocks" bash scripts/script.sh project
```

### `scenario`
Run scenario analysis on an investment: best case, worst case, and expected case with configurable parameters.

```
ROI_INVESTMENT=20000 ROI_BEST_RATE=0.15 ROI_WORST_RATE=-0.05 ROI_EXPECTED_RATE=0.08 ROI_YEARS=5 bash scripts/script.sh scenario
```

### `report`
Generate a detailed report for a single investment or the entire portfolio, including ROI, annualized returns, and projections.

```
ROI_PROJECT_ID=<id> ROI_FORMAT=text bash scripts/script.sh report
```

### `history`
View the calculation and valuation history for an investment or all investments. Shows how values changed over time.

```
ROI_PROJECT_ID=<id> bash scripts/script.sh history
```

### `export`
Export investment data, calculations, and reports to JSON or CSV format.

```
ROI_OUTPUT=/tmp/roi-export.json ROI_FORMAT=json bash scripts/script.sh export
```

### `config`
View or update configuration (default currency, compound model, report format, tax rate assumptions).

```
ROI_KEY=currency ROI_VALUE=USD bash scripts/script.sh config
```

### `help`
Show usage information and available commands.

```
bash scripts/script.sh help
```

### `version`
Display the current version of the ROI skill.

```
bash scripts/script.sh version
```

## Examples

```bash
# Quick ROI calculation
ROI_INVESTMENT=10000 ROI_RETURN=13500 bash scripts/script.sh calculate

# Add an investment project
ROI_NAME="Real Estate Fund" ROI_INVESTMENT=50000 ROI_CURRENT_VALUE=58000 ROI_START_DATE="2022-01-15" bash scripts/script.sh project

# Run scenario analysis
ROI_INVESTMENT=50000 ROI_BEST_RATE=0.12 ROI_WORST_RATE=-0.03 ROI_EXPECTED_RATE=0.07 ROI_YEARS=10 bash scripts/script.sh scenario

# Compare all investments
ROI_SORT_BY=roi bash scripts/script.sh compare

# Forecast compound growth
ROI_INVESTMENT=10000 ROI_RATE=0.10 ROI_YEARS=20 ROI_MODEL=compound bash scripts/script.sh forecast
```

## Financial Formulas Used

- **ROI** = (Net Gain / Investment) × 100
- **Annualized ROI** = ((1 + Total Return) ^ (1 / Years)) - 1
- **Compound Growth** = Investment × (1 + Rate) ^ Years
- **Simple Growth** = Investment × (1 + Rate × Years)
- **Net Gain** = Final Value - Initial Investment

## Notes

- All monetary values are stored with 2 decimal precision.
- Compound growth is the default model; set `ROI_MODEL=simple` for simple interest.
- Scenario analysis generates three projections per investment for risk assessment.
- Historical data is immutable — new entries are appended, never overwritten.

---

Powered by BytesAgain | bytesagain.com | hello@bytesagain.com
