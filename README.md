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

## Quick start

Install all dependencies for development and testing with Poetry:

```bash
poetry install --with etl,dev,test
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

Guidance for AI coding agents (Claude Code, Copilot, etc.) is in
[AGENTS.md](AGENTS.md). [CLAUDE.md](CLAUDE.md) points to the same file.
