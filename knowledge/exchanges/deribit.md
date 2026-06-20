# Deribit (crypto options & futures)

> Concentrated reference. Verify API specifics against the live docs (they drift). Sources:
> [Deribit API v2 docs](https://docs.deribit.com/) ·
> in-repo `src/alphavar/io/exchange/deribit.py` (normalizers, rename maps).

- **API:** Deribit API **v2**, public market-data endpoints over **HTTPS** (REST + WS;
  this project uses REST). Base: `https://www.deribit.com` (testnet:
  `https://test.deribit.com`). Public endpoints need no auth. _Verify rate limits in docs._
- **Instrument naming** (option): `{CURRENCY}-{DDMMMYY}-{STRIKE}-{C|P}`, e.g.
  `BTC-25DEC26-100000-C` (call). Future: `{CURRENCY}-{DDMMMYY}` or perpetual
  `{CURRENCY}-PERPETUAL`. Parse → `instrument_kind`, `strike`, `expiration`, `option_right`.
  _Source: Deribit API instrument naming; confirm against `deribit.py` parser._
- **Key fields → our columns:** venue `mark_price` → `exch_mark_price`; venue
  `creation_timestamp` → `exch_timestamp` (venue time, ms epoch); IV fields → `exch_*_iv`.
  See the rename map in `deribit.py` and dictionary-v2 migration.
- **Snapshot endpoints (typical):** `public/get_book_summary_by_currency`,
  `public/get_instruments`, `public/ticker`. _Confirm exact params/shape in live docs._
- **Gotchas:** ~thousands of instruments per currency per snapshot (vectorize parsing —
  TASKS T20); prices/sizes are in the instrument's currency (currency-conversion handled
  via `_raw` columns).

_TODO: expand with exact endpoint params, pagination, and the full field list as work
touches them._
