# Binance (crypto — spot / futures / options)

> Concentrated reference. Verify against live docs (drift). Sources:
> [Binance API docs](https://developers.binance.com/docs) ·
> [European Options API](https://developers.binance.com/docs/derivatives/option/general-info) ·
> in-repo `src/alphavar/exchange/binance.py`.

- **APIs (separate base hosts):** spot `https://api.binance.com`, USDⓈ-M futures
  `https://fapi.binance.com`, COIN-M futures `https://dapi.binance.com`, **European
  options** `https://eapi.binance.com`. Public market-data endpoints over HTTPS, no auth;
  weight-based rate limits (`X-MBX-USED-WEIGHT` headers). _Verify in docs._
- **Options:** Binance lists **European-style** options (cash-settled, USDT). Symbol
  scheme e.g. `BTC-241227-100000-C` (`{ASSET}-{YYMMDD}-{STRIKE}-{C|P}`). _Confirm against
  `binance.py`._
- **Role in alphavar:** primarily a spot/underlying price source today; options coverage
  partial. Check `binance.py` for which endpoints are actually wired.
- **Gotchas:** distinct host per product (don't mix), server-time sync for weighted limits,
  symbol filters (tick/lot size) per instrument.

_TODO: expand with the exact endpoints used, the symbol parser, and field→column mapping._
