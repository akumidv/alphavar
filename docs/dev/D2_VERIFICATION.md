# D2 Verification Ledger

Tracks every change marked `# 4VERIFY (owner)` (D2) until the owner has
verified it. A change is **not "done"** until its row here is ✅ (see
[DEVELOPMENT_REQUIREMENTS.md](DEVELOPMENT_REQUIREMENTS.md) **D2**).

**Types** (how the item is verified):
- **A — provably equivalent.** A characterization/equivalence test pins the new behavior to
  the prior one. Verify = *review the test, then approve*. The agent may add these autonomously
  (the test is the proof, not the agent's opinion).
- **B — behavior change.** Pinned by a test, but the owner must *decide the change is desired*.
- **C — new math.** Needs the owner's domain review of the formula (a numeric brief helps).

**Status:** ⏳ ready for owner review · ❗ needs owner decision · ✅ owner-verified.

## Type A — provably equivalent (verify = review the test)

| Item | What changed | Pinning test | Status |
|---|---|---|---|
| T23.1 resample model | `DEFAULT_RESAMPLE_MODEL` == pre-migration enum map, minus only `mark_price`/`mark_iv` (unused, dropped) | `options/dictionary/migration_equivalence_test::test_resample_model_matches_pre_t23_1_enum`, `…::test_dropped_resample_columns_are_gone` | ⏳ |
| T23.1 column membership | `FUTURES_COLUMN_NAMES`/`SPOT_COLUMN_NAMES` == pre-migration `FuturesColumns`/`SpotColumns` (1:1 by value) | `…migration_equivalence_test::test_{futures,spot}_column_membership_matches_pre_t23_1_enum` | ⏳ |
| T12 cache | `cachetools.TTLCache` rewrite is transparent: memoize + isolated deep copy; `None` never cached | `io/exchange/cache_test` | ⏳ |
| T14 `drop_na_price` | default reproduces the prior silent `dropna(subset=[PRICE])`; flag opts out | `options/option_data_drop_na_test` | ⏳ |
| Term registry rename | `Col`→`Term`, `OptionsCol`→`OptionsTerm`, `_columns.py`→`_terms.py` (627 call sites); reframed R4.3 as a **term** registry (one name per concept, used as column / variable / parameter — not "columns"). String values **identical**; pure identifier+doc rename | full suite green (254) + registry-value assertion (`Term.PRICE=="price"`, …) | ⏳ |

## Type B — behavior change (owner must approve)

| Item | Change & rationale | Pinning test | Status |
|---|---|---|---|
| T11a Deribit `kind` wire token | `DeribitAssetKind.value` is the singular venue token (`option`/`future`), decoupled from `InstrumentKind` (`options`) — fixes a silent HTTP 400 (R2.2). **MOEX audit: clean** — MOEX sends `MoexAssetType.value` (venue-native) on the wire; project enums are used only to normalize responses. | `io/exchange/instrument_kind_mapping_test::test_deribit_asset_kind_values_are_venue_native` | ⏳ |
| T23.1 resample sort columns | latent bug fixed: the prior list mixed a `.nm` string with two bare enum members, so `exch_timestamp`/`request_timestamp` never matched and were dropped from the sort; now all three are real column names (deterministic multi-key sort) | `…migration_equivalence_test::test_resample_sort_columns_include_all_three_timestamps` | ⏳ |
| T23.6 raw column convention | the pre-currency-conversion raw value is now stored as `<col>_raw` (was the `source_<col>` prefix); on load, `rename_legacy_columns` maps legacy names (incl. `source_*`→`*_raw`) to the current dictionary, idempotently | `core/migration/read_shim_test` | ⏳ |
| T23.9b Deribit asset_code/exch_symbol split | the Deribit normalizer now emits `asset_code`=underlying + `exch_symbol`=venue contract (was `asset_code`=contract / `base_code`=underlying), matching the already-split stored schema; `deribit_etl` routes by `asset_code` | `io/exchange/deribit_market_test`, `options/etl/deribit_etl_test` | ⏳ |
| T23.9b MOEX asset_code/exch_symbol split + BASE_CODE elimination | MOEX normalizer/join/ETL aligned to the canon (`asset_code`=underlying, `exch_symbol`=contract); the underlying-future merge re-keyed onto the contract; `base_code` eliminated from the live pipeline (both venues), `timeframe_resample` multi-asset grouping → `asset_code` | `io/exchange/moex_test` (book-summary now hermetic), `moex_options_test`, `options/etl/moex_etl_test`, `…/timeframe_resample_test` | ⏳ |
| T23.6 exch_price / interim price (R4.2) | `fill_option_price` → `exch_price` (venue traded); Deribit currency-converts it (+`exch_price_raw`); our `price` mirrored from `exch_price` via `source_interim_price` (interim until smile-fit). Behavior-preserving (same value still in `price`); `exch_iv` left nullable | `options/lib/normalization/price_normalization_test`, `io/exchange/deribit_market_test` (price/exch_price populated) | ⏳ |
| T23.5 schema nullability + boundary validation | entity schemas relaxed to match reality (`price`, `iv`, futures `expiration_date` → nullable; greeks already optional); `validate_book_data` checks each kind (`OptionsHistory`/`FuturesHistory`/`SpotHistory`) at the exchange→storage seam in both ETLs, gated by `ALPHAVAR_VALIDATE` | `options/etl/validate_book_data_test`; committed fixtures + live deribit/moex frames validate | ⏳ |
| T25 reference split (inc.1) | `split_reference`/`apply_reference` factor per-instrument constants (asset-level → `AssetMeta`; contract-level → deduped frame keyed by `(expiration,strike,option_right)`, **only columns constant per key**) out of a quote frame, losslessly; −26% memory on the BTC fixture | `options/lib/reference/split_test` (lossless round-trip + extraction + reject cases) | ⏳ |
| T25 reference SCD (inc.2) | SCD Type 2: `as_of` (version valid at a date, `valid_from` <= t < `valid_to`) + `append_on_change` (new key → open; changed attr → close prior + open new; unchanged → no-op; missing key left open) | `options/lib/reference/scd_test` (6 cases incl. exclusive-`valid_to` boundary) | ⏳ |
| T25 reference storage (inc.3) | on-disk reference layout: `AssetMeta`→`_asset.json` + contract SCD history→`_meta.parquet` at the asset root (beside `{kind}/{timeframe}/{year}.parquet`); `read_reference`/`write_reference` round-trip (timestamps stored at ms resolution by convention — same instants); absent → `(None, empty)` to start fresh | `options/lib/reference/store_test` (absent→fresh, AssetMeta + tz-aware SCD round-trip, placement, append-rewrite) | ⏳ |
| T25 reference read-wiring (inc.4A) | additive read-side: `Provider.load_reference` (default `(None, empty)`; file provider reads the asset-root reference), `OptionsData.reference`/`.reference_history`/`reapply_reference` (idempotent asset-level broadcast, no-op when absent), `Option.reference`. Existing `df_hist`/`df_fut` load path unchanged — behavior preserved (reference `None` pre-migration) | `io/provider/file_provider_test` (absent→None, round-trip), `options/option_data_class_test` (no-op, broadcast, no-overwrite) | ⏳ |
| T25 reference migration (inc.5) | extract-only wide→sidecars: `extract_reference(df, when)` (split + seed one open contract version at the earliest observed `when`) + `options/etl/reference_migration` driver (dry-run/`--apply`/CLI, per-asset, writes `_asset.json`+`_meta.parquet`). **Wide series files left untouched** (additive; slimming deferred to the as-of rejoin). Dry-run on the BTC fixture: 838 contracts | `options/lib/reference/migration_test` (asset-meta + one-open-per-contract, empty, sidecars-written + series-untouched, skip-no-options) | ⏳ |
| T25 reference ETL fold (inc.4B) | `EtlHistory._fold_reference` folds the options reference into the SCD-2 sidecar after each history write (gated `update_reference=True`, `when`=batch's latest obs): `split_reference`→`append_on_change` (new→open / changed→close+open / unchanged→no-op). Options-only, additive (sidecar only, never the series), guarded (failure logged, never aborts the write) | `options/etl/etl_reference_fold_test` (writes sidecar, append-on-change, unchanged no-op, skip-non-options) | ⏳ |
| T25 series slimming | load: `join_reference_asof` (per-row interval as-of join) + `OptionsData._restore_reference` reattach reference, **absent columns only** → slim & legacy-wide read identically. write: `EtlHistory._to_stored_series` writes `split_reference().quotes` — opt-in `slim_series=False`, gated on `update_reference` (reversible). Keystone: wide→slim+sidecar→load round-trip is lossless through the real `OptionsData` path | `options/lib/reference/slim_roundtrip_test` (lossless round-trip), `scd_test` (as-of per-row time / unmatched NaN / no-overwrite), `etl_reference_fold_test` (slim gated) | ⏳ |

## Type C — new math (owner domain review)

| Item | What | Evidence | Status |
|---|---|---|---|
| T14b payoff `_calc_premium_profile` | new mark-to-market per-strike P&L for `RISK_PNL_PREMIUM` (was `NotImplementedError`); aggregation sums it alongside `RISK_PNL` | `options/lib/analytic/risk/risk_payoff_test` (30 pass); prior version preserved commented in `payoff.py` | ❗ needs numeric brief + owner review |
| T21 Black-76 pricer | new `options/lib/pricer` (Black-76 forward price, vega, bisection implied-vol) + df helpers (`add_model_iv`/`add_fair_price`, ACT/365 tenor, `F`=underlying_price) + `OptionsPricer` facade | `options/lib/pricer/black_scholes_test` (ATM ref, parity, round-trip IV, intrinsic, NaN bracket), `…/enrich_test` | ❗ owner review of the model/conventions (forward model, rate=0, ACT/365) |

## How to clear an item
1. Owner reviews the pinning test (Type A/B) or the math + numeric brief (Type C).
2. On approval: set the row to ✅ here, drop the `# 4VERIFY` marker in the code, and mark
   the task **Done** (not "pending owner verification") in `agents/_dev/TASKS.md`.
