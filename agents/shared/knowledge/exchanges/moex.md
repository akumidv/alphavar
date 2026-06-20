# MOEX (Moscow Exchange — FORTS options & futures)

> Concentrated reference. Verify against the live ISS docs (drift). Sources:
> [MOEX ISS reference](https://iss.moex.com/iss/reference/) ·
> [ISS dev guide (PDF)](https://fs.moex.com/files/6523) ·
> in-repo `src/alphavar/io/exchange/moex.py`.

- **API:** MOEX **ISS** (Informational & Statistical Server), public REST over HTTPS,
  base `https://iss.moex.com/iss`. Responses as JSON (`?iss.meta=off&iss.json=extended`)
  or CSV. Derivatives live on the **FORTS** market (`engine=futures`, markets
  `forts`/`options`). _Verify board codes in the reference._
- **Instruments:** futures + options on FORTS. Underlyings include index/FX/equity
  futures (e.g. `SI` = USD/RUB futures, `RI` = RTS index). Option series reference the
  underlying future. _Confirm symbol scheme against `moex.py`._
- **Key fields → our columns:** venue `theorprice` (theoretical price) → `exch_mark_price`;
  venue `updatetime` → `exch_timestamp`. See the rename map in `moex.py`.
- **Spot vs derivative codes:** the project distinguishes underlying `base_asset_code`
  (e.g. `SI`, `YDEX`) from the per-row instrument; ETL groups book updates by
  `base_asset_code` (options/futures) — see TASKS note on the moex SPOT grouping key.
- **Gotchas:** Russian-language field labels in some endpoints; pagination via
  `start`; market data availability/auth may differ for delayed vs real-time.

_TODO: expand with exact ISS paths (e.g. `/engines/futures/markets/options/securities`),
params, and the full field list._
