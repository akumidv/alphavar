# Exchanges & their APIs

Per-venue knowledge: how each exchange's market-data API is shaped, the instrument naming,
and how `alphavar` maps it. In-repo source of truth: `src/alphavar/exchange/<venue>.py`
(normalizers + rename maps) and `_abstract_exchange.py` (the common contract).

Each venue file should capture, concisely and with sources:
- Base URL(s), public vs authenticated endpoints, HTTPS-only, rate limits / 429 behavior.
- Instrument-naming scheme (how to parse option/future symbols → kind/strike/expiry).
- The fields used for our columns (e.g. venue `mark_price`/`theorprice` → `exch_mark_price`)
  and timestamp semantics (venue time vs request time).
- Quirks/gotchas observed in the implementation.

Files: [deribit.md](deribit.md), [moex.md](moex.md), [binance.md](binance.md).
