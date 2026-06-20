# Domain knowledge base (for AI agents + humans)

Concentrated, **sourced** domain knowledge needed to develop `alphavar`: exchanges and
their APIs, options theory, risk, portfolio management, and adjacent topics. The goal is
to give an assistant enough context to work **without re-researching from scratch**, and a
**source for every non-trivial fact** so it can be re-queried/verified when the note is
insufficient or possibly stale.

This is reference knowledge (the problem domain). It is distinct from `../memory/` (how we
work on *this* project) and from the formal rules in `../../ARCHITECTURE_REQUIREMENTS.md` /
`../../DEVELOPMENT_REQUIREMENTS.md`.

## Structure — a multi-level model, not flat files

Knowledge is organized as a **hierarchy of folders → sub-areas → entities**, so it can be
grown in place without reshuffling:

```
knowledge/
  <domain>/                 # exchanges, options, risk, portfolio, …
    README.md               # index of this domain (links up + to children)
    <sub-area>/             # e.g. options/payoffs, options/strategies, risk/var
      README.md             # index of the sub-area
      <entity>.md           # one concrete entity (a payoff, a strategy, a VaR method…)
```

**Hierarchical indexes (required):** every folder has a `README.md` that
- links **up** to its parent index, and
- lists its **immediate children** (subfolders + files), each with a one-line hook.

So the indexes form a navigable tree from this file down to every leaf. When you add an
entity file or subfolder, **update its parent README** in the same change.

## Conventions

- **Concentrated:** short, factual bullets — not prose. Optimize for an assistant skimming
  it into context (token-efficient, see DEVELOPMENT_REQUIREMENTS D4).
- **Every non-obvious fact carries a source** inline: `[short label](url)` to the
  authoritative origin (official API docs, exchange spec, a textbook/paper, or the
  in-repo implementation that encodes it, e.g. `src/alphavar/io/exchange/deribit.py`).
- **Mark confidence/recency:** specifics drift — note "as of <date>" and link the live
  source. If unsure, say so and link the source rather than guess.
- **Re-query path:** when a note is missing detail, follow its source link (or fetch the
  official doc / search) and then *expand the note* with the new sourced fact.
- **One entity per leaf file**; granularity grows by adding files/subfolders, not by
  bloating a file.

## Domains (top-level index)

- [`exchanges/`](exchanges/) — venues & their APIs (Deribit, MOEX, Binance).
- [`options/`](options/) — options theory: concepts, pricing/Greeks/IV, payoffs, strategies.
- [`risk/`](risk/) — payoff profiles, VaR family, risk-adjusted ratios (Sharpe, Sortino).
- [`portfolio/`](portfolio/) — portfolio construction, sizing, risk budgeting.

_Seeded as a skeleton — expand with sourced entity files as the work touches each area._
