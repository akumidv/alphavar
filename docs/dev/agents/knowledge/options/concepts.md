# Options — core concepts

↑ Index: [options/](README.md)

> Sources: Hull, *Options, Futures, and Other Derivatives*;
> [Investopedia: Options](https://www.investopedia.com/options-basics-tutorial-4583012);
> in-repo `src/alphavar/options_lib/` (entities, enrichment, chain).

- **Contract:** right (not obligation) to buy (**call**) / sell (**put**) the underlying
  at the **strike** K by/at **expiration**. **European** = exercise only at expiry;
  **American** = any time. Crypto venues here are mostly European, cash-settled.
- **Premium = intrinsic value + time value.**
  - Call intrinsic `= max(0, S − K)`; put intrinsic `= max(0, K − S)` (S = underlying).
  - Time value = premium − intrinsic; decays to 0 at expiry (theta decay).
  - In-repo: `options_lib/enrichment/price.py` (`add_intrinsic_and_time_value`).
- **Moneyness:** ITM / ATM / OTM (call ITM when S>K; put ITM when S<K). In-repo:
  `options_lib/chain/price_status.py`, ATM-strike selection.
- **Option chain / desk:** grid of strikes × expirations for an underlying; the "desk"
  view pairs calls/puts per strike. In-repo: `options_lib/chain/`.
- **Price/IV semantics in alphavar:** `price`/`iv` are *our* normalized model output;
  the venue's raw values are `exch_*` (ARCHITECTURE_REQUIREMENTS R4 / dictionary v2).
