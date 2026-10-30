---
name: stock-analysis-system
description: Use when analyzing a security or small watchlist with the bundled AKShare/FastAPI technical-analysis service, or running, diagnosing, or extending that service. Supports A/HK/US stocks, ETFs, and LOFs; broad overnight sector research uses us-sector-index-impact-report.
---

# Stock Analysis System

## Overview

Use the imported `NanoAgentCode/stock` project as a reusable local stock-analysis service. The service fetches historical market data, normalizes it into OHLCV form, calculates technical indicators, assigns a 0-100 rule-based score, and returns a structured API response.

The output is for research and learning workflows only. Do not present it as personalized investment advice, a guaranteed signal, or a substitute for risk management.

## Capabilities

- Analyze `A`, `HK`, `US`, `ETF`, and `LOF` symbols.
- Fetch A-share, Hong Kong, U.S., ETF, and LOF data through AKShare primary and fallback interfaces.
- Calculate MA5/MA20/MA60, RSI, MACD, Bollinger bands, volume ratio, ATR, volatility, and ROC.
- Produce trend, momentum, volume, volatility, data-window, and data-freshness fields.
- Generate a 0-100 technical score and a rule-based recommendation.
- Expose FastAPI endpoints for `/health`, `/markets`, `/analyze-stock/`, and `/docs`.
- Support smoke tests for U.S. market retrieval and multi-market API behavior.

## Required Workflow

1. Confirm the analysis target.
   - Require an explicit `market_type`: `A`, `HK`, `US`, `ETF`, or `LOF`.
   - Require a symbol in the format expected by the service: A-share/ETF/LOF 6 digits, Hong Kong 4 digits accepted and padded to 5 digits internally, U.S. ticker text such as `AAPL`.
   - Ask for `start_date` and `end_date` only when the user needs a specific historical period; otherwise use the service default rolling recent-year window ending today.
   - If the user provides a date range, use `YYYYMMDD` and state the exact requested period.

2. Choose the execution mode.
   - For one-off analysis, start the local API and call `/analyze-stock/`.
   - For data-source diagnosis, test the provider path directly or run the smoke test that matches the market.
   - For code changes, read the implementation files first:
     - `scripts/app_modular.py`: preferred FastAPI entrypoint and response assembly.
     - `scripts/modules/models.py`: request/response contracts and validation rules.
     - `scripts/modules/stock_service.py`: market data retrieval, fallbacks, preprocessing, indicators, scoring, recommendations, and metadata.
     - `scripts/modules/config.py`: supported markets, technical parameters, score weights, API settings, and example local tokens.
     - `scripts/main_back.py`: older monolithic reference only.

3. Set up dependencies when running locally.
   - Prefer a virtual environment outside committed files.
   - Install from `scripts/requirements.txt` or `scripts/pyproject.toml`.
   - Expect AKShare and provider endpoints to be network-dependent; failures can come from provider changes, throttling, network restrictions, unsupported symbols, stale dependencies, or code defects.

4. Start the API from the skill script directory.

```powershell
cd .\skills\market-intelligence\stock-analysis-system\scripts
python -m uvicorn app_modular:app --host 0.0.0.0 --port 8000
```

Portable shell:

```bash
cd skills/market-intelligence/stock-analysis-system/scripts
python3 -m uvicorn app_modular:app --host 0.0.0.0 --port 8000
```

If the environment does not expose `python` on Windows, use the repository launcher when running Python scripts:

```powershell
.\scripts\run-python.ps1 .\skills\market-intelligence\stock-analysis-system\scripts\test_us_markets.py
```

5. Verify the service before analysis.
   - Call `/health` to confirm the API is live.
   - Call `/markets` to confirm current market metadata and supported values.
   - Use `scripts/test_us_markets.py` for U.S. market retrieval checks.
   - Use `scripts/test_markets.py` for multi-market API checks after the service is running.

6. Call the analysis endpoint with explicit market and symbol.

```http
POST /analyze-stock/
Authorization: Bearer xue123
Content-Type: application/json

{
  "stock_code": "AAPL",
  "market_type": "US"
}
```

Historical period example:

```json
{
  "stock_code": "000001",
  "market_type": "A",
  "start_date": "20250101",
  "end_date": "20250706"
}
```

7. Interpret the response.
   - Use `report.score`, `report.recommendation`, `report.price`, `report.price_change`, `report.ma_trend`, `report.rsi`, `report.macd_signal`, and `report.volume_status` as the main summary.
   - Use `technical_summary.trend`, `technical_summary.volatility`, `technical_summary.volume_trend`, and `technical_summary.rsi_level` for a compact indicator read.
- Use `report.data_points`, `report.data_start_date`, `report.data_end_date`, `report.latest_data_date`, `report.data_freshness_days`, `report.data_source`, and `report.data_quality_note` to judge data quality and whether a NAV fallback was used.
   - Use `recent_data` only as supporting evidence; do not paste all rows unless the user asks.

## Data Standards

- State the market, symbol, requested date range, actual data range, latest data date, and data freshness in the final answer.
- Do not treat ETF/LOF fallback NAV data as exchange OHLCV without qualification; volume may be zero when the fallback maps NAV to OHLC.
- Do not compare scores across unrelated markets without noting currency, trading-hour, holiday, liquidity, and data-source differences.
- Treat a score as a technical snapshot, not a fundamental valuation or investment suitability conclusion.
- Report whether the result came from a live provider call, a running local API, a smoke test, or code inspection.
- If the latest data is stale because of weekends, holidays, provider delay, or network restrictions, say so explicitly.

## Analysis Structure

For one symbol, return a concise research summary:

- Target: market, symbol, analysis timestamp, requested period, actual data period.
- Data quality: data points, latest data date, freshness, provider limitations.
- Technical score: 0-100 score, recommendation label, and the main reasons behind it.
- Trend and momentum: MA trend, RSI condition, MACD signal, ROC when relevant.
- Volatility and volume: Bollinger/ATR/volatility and volume-ratio read-through.
- Risk notes: stale data, insufficient sample, single-source dependency, ETF/LOF NAV fallback, or overbought/oversold caveats.

For a small watchlist, analyze each symbol with the same fields and sort by score only after confirming all symbols were retrieved on comparable data windows.

## Failure Handling

- If `/health` fails, classify the issue as service startup, dependency, port, or environment.
- If `/markets` fails, inspect app initialization and `StockService`.
- If `/analyze-stock/` returns 400, treat it as an input-contract problem and report the validation detail.
- If `/analyze-stock/` returns 500, inspect provider errors, preprocessing column mappings, data sufficiency, and indicator calculation.
- If AKShare returns empty or fails, report the exact provider function path when known, whether fallback was attempted, and whether the likely cause is symbol, date range, provider, dependency, network, or code.
- If the data has fewer than 60 rows, explain that the service rejects it because long-window indicators need enough observations.

## Configuration And Security

- `scripts/modules/config.py` includes example bearer tokens for local testing. Replace them before any shared deployment.
- Do not commit real API keys or private credentials. If a future source needs credentials, store them in an ignored local config file and document a `config.example` instead.
- The imported app enables broad CORS for local development. Restrict allowed origins before deployment.
- Tushare is listed in older dependency metadata but disabled in the current service code; do not describe it as an active source unless the code is re-enabled.

## Output

For chat-only analysis, summarize the result instead of dumping raw JSON. Include score, recommendation, indicator drivers, data date/freshness, and limitations.

For generated files, write outputs under `output/stock-analysis-system/` unless the user specifies another path.

## Reference

The upstream README from `NanoAgentCode/stock.git` is preserved at [references/upstream-README.md](references/upstream-README.md). Read it only when upstream project context, historical setup, or imported behavior is needed.
