---
name: us-sector-index-impact-report
description: Use when preparing an overnight U.S. sector review and its Hong Kong/A-share implications as a cited Chinese HTML report. Includes both Nasdaq indices, fundamental drivers, AI capex, geopolitics, dollar policy, and gold; not a generic single-stock analysis.
---

# US Sector Index Impact Report

## Overview

Produce a current, citation-backed Chinese investment research report from overnight U.S. market data, then render it as a polished standalone HTML page. The output should read like a sell-side morning note: concise thesis first, factor and fundamental drivers second, cross-market implications third.

## Required Workflow

1. Confirm the trading session date.
   - Interpret "last night" relative to the user's timezone when available; for China users, this usually means the most recent completed U.S. regular trading session.
   - State the exact U.S. trading date in the report.
   - If the U.S. market was closed, report that clearly and use the most recent completed session only after saying so.

2. Gather fresh data with live sources.
   - Fetch or verify Nasdaq Composite and Nasdaq 100 closes, point changes, and percentage changes.
   - Fetch U.S. sector or industry-index moves. Prefer official exchange/index-provider pages, market-data terminals, or reputable financial media/data sites.
   - Fetch the session's relevant factor drivers: Treasury yields, dollar index, oil, global gold, copper when relevant, major earnings/news catalysts, geopolitical headlines, dollar-policy signals, and AI capex headlines from hyperscalers or semiconductor/AI infrastructure names.
   - Use at least two independent source families when possible: one for headline indices and one for sectors/industries.
   - Record source URL, publisher, retrieval date, and the fields each source supports.

3. Normalize the market table.
   - Include: `name`, `ticker_or_index`, `close`, `change_pct`, `change_points` when available, `rank`, and `source`.
   - Sort industries/sectors by `change_pct` descending.
   - Mark missing point changes as `null`; do not infer exact figures from percentages unless the source supplies prior close.

4. Analyze cross-market transmission.
   - Map U.S. leaders/laggards to Hong Kong sectors: internet platforms, semiconductors, hardware supply chain, biotech, EVs, financials, energy, materials, consumer, and real estate when relevant.
   - Map to A-share sectors: semiconductors, CPO/optical modules, PCB, AI servers, software, robotics, innovative drugs, brokerage, military, new energy, coal/oil, nonferrous metals, consumer, and export chains when relevant.
   - Separate three channels instead of blending them: risk appetite/liquidity, earnings or demand read-through, and supply-chain/order read-through.
   - Distinguish "direct read-through" from "sentiment beta"; for China markets, U.S. tech strength does not automatically mean the same domestic sector outperforms.

5. Add core-factor and fundamental analysis.
   - Identify the top 3-5 drivers behind the session's gains and losses. Do not only restate price moves.
   - Separate macro factors (rates, dollar, liquidity, global gold and commodities), earnings/fundamentals, positioning/valuation, policy/geopolitics, and dollar-policy signals.
   - Give special focus to U.S. AI capital expenditure: hyperscaler capex guidance, data-center buildout, GPU/ASIC demand, power/cooling constraints, networking/optical demand, and depreciation/free-cash-flow pressure.
   - Explain geopolitical impact through risk premium, energy/security shocks, defense spending, export controls, supply-chain restrictions, and China exposure.
   - Explain dollar policy through Fed expectations, Treasury/Fiscal signals, official dollar rhetoric if relevant, DXY move, RMB/HKD transmission, gold, and emerging-market liquidity.
   - Include global gold's session move and explain whether it reflects real-rate pressure, dollar weakness, geopolitical hedging, central-bank demand, or risk-off behavior.
   - Explain whether the session implies AI capex acceleration, sustainability, digestion, or crowding/valuation risk.
   - Link AI capex analysis to beneficiaries and risks in Hong Kong and A-share sectors.

6. Write in investment-bank report structure.
   - Title: include session date and main conclusion.
   - Executive summary: 3-5 bullets, each with a quantified anchor.
   - Market dashboard: Nasdaq Composite, Nasdaq 100, S&P 500 if used, and sector/industry ranking.
   - Core drivers: a factor table explaining the main reasons for gains/losses.
   - AI capex and fundamentals: analyze demand visibility, capex intensity, margins/free cash flow, and supply-chain implications.
   - Geopolitics, dollar policy and gold: summarize geopolitical risk, dollar-policy channel, global gold move, and China-market transmission.
   - U.S. sector interpretation: why leaders and laggards moved.
   - Hong Kong impact: likely beneficiaries, pressure points, and watchlist.
   - A-share impact: likely beneficiaries, pressure points, and watchlist.
   - Risk scenarios: at least bull/base/bear or upside/downside catalysts.
   - Source appendix: cite every data source used.

7. Render a standalone HTML file.
   - Build a JSON payload that follows `references/report-schema.md`.
   - Run `scripts/render_investment_bank_html.py` to create the HTML page.
   - If the user specified an output path, use it. Otherwise write the JSON payload and rendered HTML under the repository root `output/us-sector-index-impact-report/`, for example `output/us-sector-index-impact-report/us-sector-impact-report-YYYY-MM-DD.html`.
   - The renderer rejects incomplete reports: title, session date, both Nasdaq indices, every required analysis section, and traceable sources are mandatory. Treat rejected input as an unfinished research draft, not a deliverable.

## Data Standards

- Use percentage changes from the source exactly as reported, with one or two decimals in narrative text.
- Do not present delayed or preliminary futures data as completed-session data.
- Label gold data clearly as spot gold, gold futures, or gold ETF proxy.
- Do not mix ETF performance with index performance unless the report labels it as a proxy.
- If only ETF proxies are available for a niche industry, label them as proxies and explain the limitation.
- For Hong Kong and A-share implications, use current constituents and policy/holiday status when decision-grade specificity is needed.

## HTML Rendering

Use the bundled renderer:

```powershell
.\scripts\run-python.ps1 .\skills\market-intelligence\us-sector-index-impact-report\scripts\render_investment_bank_html.py `
  --input .\output\us-sector-index-impact-report\report-data.json `
  --output .\output\us-sector-index-impact-report\us-sector-impact-report.html
```

The Windows launcher resolves Python without relying on `python` or `py` being on `PATH`. If it cannot find Python, it reports the missing Python interpreter prerequisite and the checked locations. The renderer has no third-party Python dependencies. Read [references/report-schema.md](references/report-schema.md) before constructing the JSON payload. Read [references/market-analysis-framework.md](references/market-analysis-framework.md) when the cross-market logic needs a checklist.

For a stable local renderer preview, use the checked-in fixture:

```powershell
.\skills\market-intelligence\us-sector-index-impact-report\scripts\preview_sample_report.ps1
```

The preview script renders [fixtures/sample-report.json](fixtures/sample-report.json) to `output/us-sector-index-impact-report-sample.html` by default. Pass `-Open` to launch the rendered file after generation, or `-Output .\path\report.html` to choose another output path. Keep the fixture aligned with [references/report-schema.md](references/report-schema.md) so renderer changes can be compared against a stable example.

## Final Response

Return the generated HTML file path, the exact U.S. session date, and a short note about any data limitations. Do not paste the whole report into chat unless the user asks.
