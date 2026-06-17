# alphavar

**alphavar** is a Python library for options (and futures) analysis and visualization.

The name reads as **alpha + VaR** — *alpha* (returns above the market) combined with
*Value-at-Risk* — reflecting the project's focus: turning raw options data into
risk-aware analytics. It gives you a single interface to fetch options/futures data from
different providers, enrich it with computed metrics, work with option chains, analyze
risk (payoff profiles) and time value, and visualize the results.

> **NB:** Early stage of development — the API may change.
>
> A parallel implementation in Rust is in progress (with a large delay):
> [alphavar-rust](https://github.com/akumidv/alphavar-rust).

## What it does

- **Data** — retrieve options/futures data from exchange APIs (Deribit, MOEX, …) or local files.
- **Enrichment** — add computed metrics: intrinsic/time value, ATM/ITM/OTM, Greeks.
- **Chains** — build and select option chains, assemble option "desks".
- **Analytics** — risk/payoff profiles for option combinations, time-value analysis.
- **Charts** — visualization via Plotly / matplotlib.
- **ETL** — accumulate historical snapshots of quotes.

The library follows a provider pattern: different data sources plug in through the
`AbstractProvider` interface. The main entry point is the `Option` class in
[src/alphavar/option_class.py](src/alphavar/option_class.py).

## Ecosystem & roadmap

`alphavar` is the analysis core of a wider **alpha-extraction ecosystem** for financial
markets — options and derivatives today, with **equities** (fundamental analysis) and
**bonds**, plus broad market/macro context, on the roadmap. Alongside the library the
ecosystem includes the [`catcher-bot`](https://github.com/akumidv/catcher-bot) trading bot,
so together they cover both **analysis and trading**. As domains mature, general entities
(e.g. `options`) are expected to graduate into git submodules.

The ecosystem is **built and operated through AI agents** (locally now, server-side later),
split into two classes:

- a **build agent** — develops this codebase;
- **operate ("desk") agents** — use the library + bot on the market: options/history
  analysis, investment analysis, strategy backtesting, fundamental analysis for equity/bond
  forecasts, and trading — coordinated by an orchestrator.

Agents share one domain knowledge base (destined for an **MCP** server) and improve the
system via a learn loop routed through the build agent. How to work in either mode is in
[AGENTS.md](AGENTS.md); the full agent operating model is in
[agents/README.md](agents/README.md).

## Quick start

Install all dependencies for development and testing with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --all-extras
```

```python
from alphavar import Option
```

## Demo

The easiest way to see how to use alphavar is to open the Jupyter notebooks in the
`demo/` folder on Google Colab:

1. Open [Google Colab](https://colab.research.google.com/).
2. Click `File / Open notebook`.
3. In the popup, select **GitHub** and paste the repository URL:
   [alphavar](https://github.com/akumidv/alphavar.git).
4. Verify `alphavar` is selected in the Repository dropdown.
5. The list of notebooks appears below — pick one, e.g.
   [Options for Smart Investor](https://github.com/akumidv/alphavar/blob/main/demo/books_and_articles_reproducing/Options%20for%20Smart%20Investor.ipynb).

ETL examples for different exchanges (Deribit, MOEX) are in `demo/etl_example/`.

## Data

The easiest way to get sample data is to download it from the shared
[Google Drive folder](https://drive.google.com/drive/folders/1NJNxkkUYzCfADIlPHyaZQ0jrfW9WJn2I?usp=sharing).
Save the files into a data folder and point `DATA_PATH` (in `test.env`) at it.

The `demo/` notebooks also include `gdrive` snippets showing how to download the data.

## Documentation

User-facing documentation is a Next.js (Markdoc) site in the `docs/` folder.
With Node.js installed:

```bash
cd ./docs
npm install
npm run dev
```

Then open the link printed in the console.

> The docs are still minimal. In the future they may be deployed via Vercel or Netlify.

Architecture, design decisions, and development notes live in
[docs/dev/PROJECT_OVERVIEW.md](docs/dev/PROJECT_OVERVIEW.md).

## For AI agents

This project is **built and operated through AI agents**, and the repo supports two usage
models:

- **As a library** — import `alphavar` and drive the `Option` facade yourself (see *Quick
  start* and the demo notebooks).
- **Through agents** — let an assistant operate the ecosystem. The canonical, vendor-neutral
  entry point is [AGENTS.md](AGENTS.md) ([CLAUDE.md](CLAUDE.md) points to it); the full
  operating model (skills, tools, knowledge, guardrails, learn loop) is in
  [agents/README.md](agents/README.md).

Agents are split by **what they act on**, and a session runs in one of two **modes** —
switch by a plain-text signal, **DESK is the default**:

- **DEV / BUILD** → [`agents/_dev/`](agents/_dev/) — the build agent: develops this codebase
  (bound by the R#/D# requirements).
- **DESK (operate)** → [`agents/desk/`](agents/desk/) — agents that work the market/data,
  bound by runtime guardrails (**G#** — e.g. read-only by default; only the trader may place
  orders, gated):
  - **options-analyst** — mispricing / IV-surface scan *(seeded)*;
  - **investment-analyst** — cross-asset allocation views *(planned)*;
  - **strategy-tester** — backtest strategies *(planned)*;
  - **fundamental-analyst** — company fundamentals → equity/bond forecast *(planned)*;
  - **trader** — places orders via `catcher-bot` *(planned)*;
  - **orchestrator** — routes work, enforces separation of duties, consolidates results
    *(planned)*.

Domain knowledge is shared across agents ([`agents/shared/`](agents/shared/), → MCP); desk
findings become code/skills/tools through the build agent (the learn loop).
