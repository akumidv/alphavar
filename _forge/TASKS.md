# Tasks — alphavar (active + planned)

> Active and planned work. **Completed** refactoring/remediation is archived in
> [TASKS_ARCHIVE.md](TASKS_ARCHIVE.md). Architecture/domain constraints:
> [ARCHITECTURE_REQUIREMENTS.md](../docs/dev/ARCHITECTURE_REQUIREMENTS.md) (R0…R8).
> Dev rules: [DEVELOPMENT_REQUIREMENTS.md](DEVELOPMENT_REQUIREMENTS.md)
> (D1…D6). Verification for every task: `pytest` + `ruff` green, plus **D2 owner
> verification** for any math/DataFrame/architecture change.

## Status (2026-06-19)

Suite **394 passed, 1 skipped, 1 xfailed / ruff clean**. The 2026-06-13 review backlog
(P0/P1, Blocks A/B/C, R0, T19–T24, T21 pricer/smile/validation, T22) is **complete and
archived** → [TASKS_ARCHIVE.md](TASKS_ARCHIVE.md). Every committed math/DataFrame/architecture
change is **not "Done" until owner-verified** — see the [D2 ledger](D2_VERIFICATION.md).

**In flight:**
- **T27 `forecast`** — iterations 1 (price) + 2 (vol) + 3 (smile) + 4 (surface, + smile maturity B)
  + **5 (price: endogenous/model-free)** **code-complete, D2-pending**. Remaining: it.5 **factor-
  conditional** `factor_linear`/`var` (deferred — need the [ADR 0003](../docs/dev/decisions/0003-composable-result-chain.md)
  exogenous-factor input contract) and it.6 (historical-analogue model).
- **T28** — unify the provider ↔ exchange normalization path (planned; needs an ADR).

**Planned new functionality (P4):** T29 surface fitting · T30 sparse/live smile-shift · T31 spot ·
T32 bonds · T33 portfolio · T35 risk · T34 (this split — done).

**Operational (owner-run, tooling ready):** T23.6(c) stored-parquet column migration;
T25 flip `slim_series` on to shrink stored files (both archived for detail).

---

## P3 — in flight

### T27. `forecast` facade component — model factory (resolves the T21 forecast placeholder)
**Status:** iterations 1 (price) + 2 (vol) + 3 (smile) + 4 (surface, + smile maturity B) + 5 (price:
endogenous/model-free) **code complete — pending owner verification (D2)**. Remaining = the
factor-conditional price models (deferred to ADR 0003) and the historical-analogue model. Owner-scoped 2026-06-19.
**Iteration 1 outcome (2026-06-19):** `options/lib/forecast/` factory live (Target × Process ×
Engine) + facade `OptionsForecast` → `Option.forecast`. Price models `random_walk`/`gbm`/`garch`,
engines `analytic`/`montecarlo`; planned names raise `NotImplementedError`. Math pending D2 — ledger
row **"T27 forecast price models (it.1)"** (Type C, ❗); `4VERIFY` in `_stats`/`_base`/`price/*`/`_series`.
**Iteration 2 outcome (2026-06-19):** vol target — `vol/{realized,ewma,garch,har}.py` + facade
`OptionsForecast.vol(...)`. GARCH(1,1) MLE factored into shared `_garch.py` (reused by price + vol).
`DegenerateTerminal` (point forecast as a distribution) + target-named `to_frame` column. **pytest
362 / ruff clean** (forecast suite 29). Math pending D2 — ledger row **"T27 forecast vol models (it.2)"**
(Type C, ❗); `4VERIFY` in `_garch`/`vol/*`.
**Iteration 3 outcome (2026-06-19):** smile target — `options/lib/forecast/smile/` forecasts the
calibrated SVI θ=(a,b,ρ,m,σ) of one expiration over history and decodes the terminal θ back to a
smile at target tenor τ=E−(as_of+H). Models `param_rw` (driftless multivariate RW, **default**) /
`param_var` (mean-reverting VAR(1), OLS, driftless-RW fallback when under-identified) / `param_pca`
(RW on the top-k PCA modes of the θ increments) — all reduce to a Gaussian terminal on θ (mean+cov).
Engines `analytic` (expected smile) / `montecarlo` (PSD-safe MVN θ draws → σ(k) quantile bands).
Result type `SmileForecast` (expected_smile / iv_quantiles bands / scenario_smiles / to_frame /
is_butterfly_free). Own sibling factory `make_smile_forecast_model` (parameter-vector state +
distinct result ⇒ separate from the scalar `make_forecast_model`, which now redirects SMILE); facade
`OptionsForecast.smile(...)` → `Option.forecast`. **Maturity convention: A `fixed_expiration` built**
(models one expiration's θ, mixes tenors across history — `4VERIFY`); **B `constant_maturity`**
(interpolate to a fixed tenor before modelling — the *correct* dynamics) **raises NotImplementedError,
deferred to iteration 4 (surface)** because it needs the cross-expiration interpolation built there
(`MaturityConvention` enum + `resolve_maturity`). **pytest 375 / ruff clean** (forecast suite 42,
smile 13). Math pending D2 — ledger row **"T27 forecast smile models (it.3)"** (Type C, ❗);
`4VERIFY` in `smile/{_base,_decode,_theta,param_rw,param_var,param_pca}.py`.
**Iteration 4 outcome (2026-06-19):** surface target — `options/lib/forecast/surface/`. State = SVI θ
stacked across **constant-maturity tenor nodes** (default 1w/2w/1m/2m/3m): per timestamp fit a smile
per expiration, interpolate total variance across expirations to each node (`interp_total_variance`:
linear-in-w + flat-`w/τ` T-extrapolation), refit SVI per node → stacked θ history. Dynamics **reuse
the verified smile θ-models** on the longer vector — `svi_surface` (RW, default) / `svi_surface_var`
(VAR(1)) / `pca_factor` (PCA). Engines `analytic`/`montecarlo` → `SurfaceForecast` (expected surface
+ scenario σ(k,τ) bands via `decode_surface`; butterfly per node + **calendar** no-arb). Facade
`OptionsForecast.surface(...)`. **This unlocked smile maturity convention B**: `constant_maturity`
(single CM node at the target tenor) is now built and selectable alongside A `fixed_expiration`
(`resolve_maturity` no longer raises). **pytest 385 / ruff clean** (forecast suite 52, surface 10).
Math pending D2 — ledger row **"T27 forecast surface models (it.4)"** (Type C, ❗); `4VERIFY` in
`surface/{_interpolate,_nodes,_base}.py`.
**Iteration 5 outcome (2026-06-19):** price target — *endogenous/model-free* processes built.
`price/ar1.py` (OLS AR(1) on log-price → mean-reverting **log-normal** terminal: `meanlog=μ+φ^n(x_T−μ)`,
`var=σ_ε²(1−φ^{2n})/(1−φ²)`, φ clipped to ±0.9999; analytic + MC via `LogNormalPrice`) +
`price/empirical.py` (model-free: terminal = `S₀·exp(Σ of n resampled historical log-returns)`; no
analytic form). New **`bootstrap` engine** (`engine/bootstrap.py`) via a `FittedProcess.bootstrap_terminal`
hook — `empirical` resamples i.i.d. under `montecarlo` vs **moving-block** (wrap-around, block≈n^{1/3})
under `bootstrap`; parametric models expose no series ⇒ clear raise. New **`front` source**
(`_series.front_price_series`): rolled continuous front contract (nearest expiry ≥ now+roll_buffer)
with **proportional back-adjustment** anchored at the latest leg. Facade `OptionsForecast.price`
exposes `model='ar1'|'empirical'`, `engine='bootstrap'`, `source='front'`. **pytest 394 / ruff clean**
(forecast suite 61). Math pending D2 — ledger row **"T27 forecast price models (it.5)"** (Type C, ❗);
`4VERIFY` in `price/{ar1,empirical}.py`, `_series.py` (front), `_base.py` (bootstrap hook).
**Still planned (catalogued, not built) — owner-scoped 2026-06-19, from the review:**
- **Price target — factor-conditional processes (it.5 remainder):** *exogenous* `factor_linear`
  (returns regressed on external factors: rates, futures-spot basis, realized vol, macro) + `var`
  (vector-autoregression over (price, rates, …) jointly) — each needs the factor series **and** a
  horizon factor scenario (assumed or itself a forecast → composable). **Deferred behind the
  composable result-chain ([ADR 0003](../docs/dev/decisions/0003-composable-result-chain.md))**,
  which is their input contract; they still raise `NotImplementedError` via the factory.
- **Historical-analogue / pattern-matching model (new, it.6 — applies to price/vol/smile/surface):**
  forecast by **searching history for a market situation similar to the present** (by the vol level,
  the smile shape, or the whole surface for the instrument) and projecting its **subsequent realized
  evolution** forward over the required horizon — the forecast is "history repeats". Fits the factory
  as a `Process` (`analogue`/`pattern_match`): the state is a window descriptor (recent vol/smile-θ/
  surface-θ trajectory); fit = a distance/similarity search over the instrument's history (k-NN on the
  descriptor); the engine = the empirical distribution of the matched windows' forward paths (so
  `montecarlo`/`bootstrap` give scenarios, `analytic` the matched-mean path). Cross-target: a `price`
  analogue uses the return-window descriptor; a `smile`/`surface` analogue uses the θ-trajectory
  descriptor + decode (reuse `decode_smile`/`decode_surface`). Owner to confirm the descriptor /
  distance metric / window length / # neighbours before build.
**Goal:** a `forecast` capability area (R3 facade over `OptionsData`, R5 pure lib) that produces a
**distribution** of a target at a future horizon — feeding VaR/CVaR. Factory of models along three
**orthogonal axes**, not one "approach" knob:
- **Target** (what) — the forecast state vector + its observable mapping.
- **Process / Model** (dynamics + how params are estimated from history).
- **Engine** (inference) — how the fitted process becomes a distribution.

**Design (owner-verified architecture — route math to D2):**
- Horizon is **calendar ACT/365** (`h_years`, same convention as `SmileResult.t_years` /
  `years_to_expiry`). `Horizon = pd.Timedelta | float(days) | pd.Timestamp(expiration)`;
  a `Timestamp` auto-computes `h_years = (expiration − as_of)/365d`, `as_of` = last history ts.
  Trading-time (≈252) scaling = later option, not iteration 1.
- `ForecastResult` is **distributional**: `point()`, `quantiles(qs)`, `scenarios(n)` (empirical
  sample or an analytic `Distribution`). Default engine = `montecarlo` (universal); `analytic` =
  closed-form fast path where it exists.
- smile/surface are **not** special-cased: their state is the calibrated SVI/SABR **parameter
  vector** (reuse `make_smile_model`); the same Process × Engine axes apply.
- Pure-numpy only (no scipy — repo convention); optimizers via existing `minimize_nelder_mead`;
  inverse-normal CDF hand-rolled (Acklam) for analytic quantiles.

**Layout:** `options/lib/forecast/` (`_base.py`, `_stats.py`, `_factory.py`, `engine/`,
`price/ vol/ smile/ surface/`) + facade `options/forecast_class.py` → `Option.forecast` (R3).

**Catalog (опись максимального набора — `[x]` = build in iteration 1, `[ ]` = planned):**

Engines (`engine/`):
- [x] `analytic` — closed-form distribution → quantiles.
- [x] `montecarlo` — simulate paths → empirical distribution (default).
- [x] `bootstrap` — resample historical residuals/returns (model-free empirical; moving-block, it.5).

Target `price` (state = log-price). Output **view** (not a separate model): `ForecastResult`
exposes both the level `S_{t+h}` and the change `ΔS = S_{t+h} − S₀` (`.change()` / ΔS quantiles)
— iteration 1. Two Process families:
- *endogenous* (price from its own history) — iteration 1:
  - [x] `random_walk` — driftless log RW baseline; analytic (lognormal) + MC.
  - [x] `gbm` — drift + vol from log returns; analytic (lognormal) + MC.
  - [x] `garch` — GARCH(1,1) Gaussian-MLE vol dynamics; MC (analytic price terminal n/a).
  - [x] `ar1` — mean-reverting AR(1) on log-price → log-normal terminal (analytic + MC); it.5.
  - [x] `empirical` — historical/bootstrap return distribution (pairs with `bootstrap`); it.5.
- *exogenous / factor-conditional* (price driven by external factors — rates, futures-spot basis,
  realized vol, macro) — **planned**; needs the factor series in **and** a factor scenario at the
  horizon (assumed, or itself a forecast → composable). **Deferred behind [ADR 0003](../docs/dev/decisions/0003-composable-result-chain.md)**
  (the composable result-chain = their input contract). `rate` is a *pricing* input today
  (Black-76), distinct from a forecast driver.
  - [ ] `factor_linear` — regression of returns on exogenous factors (incl. rates).
  - [ ] `var` — vector-autoregression over (price, rates, …) jointly.

Price series **source** (facade `source=` param — which series feeds the model; orthogonal to
the model choice):
- [x] `future` — a single future series from `df_fut` selected by `expiration_date` (default =
  front), fallback to `underlying_price`.
- [x] `underlying` — per-timestamp `underlying_price` from `df_hist` (dedup to one value/ts).
- [x] `front` — continuous front-contract series (roll + proportional back-adjustment); it.5.

Target `vol` (iteration 2 — **done**): [x] `ewma` (RiskMetrics λ=0.94, flat term structure) ·
[x] `garch` (variance term structure analytic + realized-vol MC) · [x] `har` (HAR-RV, RV=r² proxy,
d/w/m=1/5/22) · [x] `realized` (trailing annualized). Observable = annualized vol over the horizon;
point models analytic-only, `garch` adds `montecarlo`. `spot` = trailing realized vol (change ref).
Target `smile` (iteration 3): state = SVI θ=(a,b,ρ,m,σ) history per expiration (fit via
`make_smile_model`); result type **`SmileForecast`** (expected smile + σ(k) quantile bands +
scenario smiles + `to_frame`). Models — **all three built, none cut**: [x] `param_rw` (driftless
multivariate RW on θ) · [x] `param_var` (VAR(1), mean-reverting) · [x] `param_pca` (PCA-reduced RW).
Engines: `analytic` (expected smile from mean θ) / `montecarlo` (MVN θ draws → σ(k) bands). Decode
θ→smile with clamp (b≥0, |ρ|<1, σ>0) reusing SVI `_raw_w`; no-arb via `is_butterfly_free`.
Maturity convention (**both recorded**; A built, B planned):
- [x] **A `fixed_expiration`** — model θ of one expiration, present the forecast smile at target
  tenor τ = (E − (as_of+h)); iteration-3 baseline (mixes tenors across history — flagged `4VERIFY`).
- [x] **B `constant_maturity`** — interpolate to a fixed tenor τ before modeling (correct dynamics);
  **built with iteration 4** (single constant-maturity node at the target tenor), selectable alongside A.
Target `surface` (iteration 4 — **done**): [x] `svi_surface` (stacked-θ RW across constant-maturity
nodes, + flat-`w/τ` T-extrapolation) · [x] `svi_surface_var` (VAR(1)) · [x] `pca_factor` (PCA-reduced).
State = SVI θ stacked across CM tenor nodes (`interp_total_variance` cross-expiration); engines
`analytic`/`montecarlo` → `SurfaceForecast` (σ(k,τ) bands; butterfly + calendar no-arb).
Target `analogue` (planned, it.6 — applies to every target): forecast = **history repeats** — search
the instrument's past for a window similar to the present (by vol / smile-θ / surface-θ descriptor),
project the matched windows' realized forward evolution over the horizon (k-NN descriptor search as
the `Process`; empirical/`bootstrap` engine over the matched forward paths). Descriptor / distance /
window / # neighbours owner-scoped before build.

**Decisions locked (2026-06-19 session — owner-approved):**
- Output = `ForecastResult` object (level **and** change view `ΔS=S_{t+h}−S₀` + `.to_frame(quantiles)`),
  not a bare DataFrame. `point()/quantiles(q)/scenarios(n)/change()/change_quantiles(q)`.
- Horizon ACT/365; `as_of` = last timestamp of the chosen series; `float` horizon = calendar **days**,
  `pd.Timedelta` = delta, `pd.Timestamp` = expiration date. `dt_years` auto = **median** ts spacing.
- `montecarlo` is the default engine; `seed: int|None` for reproducibility (tests use a fixed seed).
- Price-series **source** = facade param: `future` (a `df_fut` series by `expiration`, **default =
  the most-populated expiration** = de-facto front; fallback to `underlying` when `df_fut` empty) ·
  `underlying` (per-ts `underlying_price` deduped) · `front` = **planned** (raises NotImplementedError).
- Endogenous price models: `random_walk`/`gbm` → `LogNormalTerminal` (analytic + MC); log-drift
  ν = mean(r)/dt for `gbm`, ν = 0 for `random_walk`; σ²_ann = var(r)/dt; sdlog = σ√H,
  meanlog = lnS₀ + ν·H. `garch` = GARCH(1,1) Gaussian-MLE via `minimize_nelder_mead` (unconstrained
  reparam: ω = exp(·), persistence φ & α-share via sigmoids ⇒ ω>0, α,β≥0, α+β<1); **MC only**
  (terminal not lognormal — `analytic` raises), simulates `round(H/dt)` steps, <10 returns ⇒
  constant-variance fallback.
- Layout: `options/lib/forecast/{_stats,_base,_factory,_series}.py`, `engine/{analytic,montecarlo}.py`,
  `price/{random_walk,gbm,garch}.py`; facade `options/forecast_class.py` → `Option.forecast`.

**Plan (iteration 1 — price) — all landed:**
- [x] 1. `_base.py` (axes ABCs + `to_horizon_years` + `ForecastResult`) + `_stats.py` (`norm_ppf`
  Acklam + `LogNormalTerminal`).
- [x] 2. `engine/analytic.py` + `engine/montecarlo.py`; `_factory.py` (`make_forecast_model`/
  `make_engine`, `supports` capability flags; planned names → `NotImplementedError`).
- [x] 3. `price/{random_walk,gbm,garch}.py` (+ shared `price/_lognormal.py`).
- [x] 4. `_series.py` + facade `OptionsForecast.price(...)`; wired `Option.forecast`.
- [x] 5. Tests `tests/unit/options/lib/forecast/` (21, green).
**Acceptance check:** `uv run pytest -q tests/unit/options/lib/forecast_test` green +
`uv run ruff check src tests` clean; analytic vs MC gbm quantiles agree within MC error.
**Notes:** Architecture decision durably recorded in **[ADR 0002](../docs/dev/decisions/0002-forecast-model-factory-axes.md)**
(target × process × engine axes) + R3 model-factory pattern + PROJECT_OVERVIEW §12. R3 (facade) +
R5 (pure lib) — mirrors the `lib/pricer/smile/` factory. Math (GBM/GARCH
estimators, multi-step variance, lognormal quantiles, `norm_ppf`) is **D2 owner-verify** — add
`4VERIFY` headers + a D2 ledger row before "done". Resolves the T21 `forecast` placeholder.

### T28. Unify provider ↔ exchange data path (single normalization contract)
**Status:** planned (owner-scoped 2026-06-19)
**Goal:** the *same* logical data (options/futures history, books) can arrive **live from an
exchange** or **stored via a file provider**; today both must yield a schema-identical DataFrame
but the normalization/column-mapping is split between the exchange layer (`RAW_SUFFIX`,
`INSTRUMENT_KIND_MAP`, `resolve_instrument_kind`, snapshot) and the file providers, with no single
place that pins "any source → one canonical frame". Consolidate that contract so callers stay
source-agnostic (the R1/R2 promise: *new source = new provider, no caller changes*).
**Touches binding invariants R1/R2 → requires an ADR** (`docs/dev/decisions/`) before code.
**Plan:**
- [ ] 1. Audit the two paths: what `AbstractExchange` normalizes vs what file providers assume
  already-normalized; list every column-mapping / dtype / tz / currency-raw (`_raw`) step and
  where it currently lives. Document the present `AbstractExchange(AbstractProvider)` relationship.
- [ ] 2. ADR: where the canonical-normalization boundary belongs (shared normalizer in
  `core`/`io` consumed by both source kinds vs. exchange-only) + the source taxonomy
  (`DataSource.LOCAL/S3/API` × engine) it implies.
- [ ] 3. Extract the shared normalization into one contract/module; exchanges and file providers
  both route through it; remove the duplicated/implicit mapping.
- [ ] 4. Characterization tests: a recorded exchange snapshot and a stored parquet of the same
  asset/period produce **identical** canonical frames (column set, dtypes, tz, ordering).
**Acceptance check:** `uv run pytest -q tests/unit/io` green + the equivalence test (exchange vs
file → identical frame) + `ruff` clean; ADR merged.
**Notes:** architecture change → **D2 owner-verify** + ADR. Keep R2.1/R2.2 (identity & wire-format
translation stay at the exchange boundary) and R4 (columns only via dictionary enums) intact.

---

---

## P4 — planned new functionality (owner-scoped 2026-06-19; not started)

> These are forward-looking feature blocks, distinct from the refactoring/remediation backlog
> (T1–T28) that is largely done. Each needs an owner scoping pass (and, where it touches R1/R2/R4
> invariants or adds an entity, an ADR) before code. See **T34** — the TASKS file will be split into
> an archive (done refactoring) + this active feature plan.

### T29. Surface **fitting** model (pricer-side, R5 — extends T21 smile fit)
**Status:** planned. Distinct from T27 it.4 (which *forecasts* the surface): this is *calibrating* a
whole vol **surface** to a market snapshot, not just independent per-slice smiles.
**Goal:** a `make_surface_model` in `options/lib/pricer/` (sibling of `make_smile_model`) that fits
all expirations **jointly** with a calendar-no-arbitrage coupling (total variance non-decreasing in
τ), e.g. an SVI-surface (SSVI / θ-interpolated raw-SVI) parametrization. Reuse the constant-maturity
total-variance interpolation already built for the forecast (`forecast.surface._interpolate` — likely
promote it to a shared `pricer` location). Output a `SurfaceFit` that yields `iv(k, τ)` anywhere +
butterfly (per slice) **and** calendar no-arb checks. Facade: `OptionsPricer.fit_surface(...)` →
writes a smooth, arbitrage-consistent `iv`/`price` across the whole board (vs the per-slice
`fit_smile`). **Notes:** math → D2 (Type C); SSVI is the natural first parametrization.

### T30. Smile fit on **sparse / live data** via smile-shift (pricer-side, R5)
**Status:** planned. **Problem:** intraday/live we often have only a handful of quotes for an
expiration — too few to recalibrate a full SVI smile (which needs ~5 points). **Idea (owner):** take
the **last well-calibrated smile** (e.g. yesterday's EOD fit) and **translate / shift** it to the new
state instead of refitting from scratch: recompute log-moneyness `k = ln(K/F)` against the **new
underlying** F and the **new TTE** τ (so the curve re-anchors to today's forward and tenor), then
apply a small **shift** solved from the **few live points available** — a low-DoF correction of the
prior smile rather than a free fit.
**Decided (owner 2026-06-19) — both, combined:**
- **Work in total-variance space.** The shift is **additive in total variance** `w = σ²·τ` (not in σ):
  natural for the no-arb checks and for re-anchoring to the new TTE (when τ changes, holding `w` and
  recomputing `σ = √(w/τ)` is the correct reparametrization). The re-anchor step recomputes `k =
  ln(K/F)` against the **new forward F** and reads the prior at the **new τ** in `w`-space first.
- **Adaptive degrees of freedom by live-point count:** 1 point → **parallel** `w`-level shift;
  2 → **level + slope** (skew); ≥3 → **level + slope + light curvature** — solved by least squares on
  the live residuals; never more DoF than points (so a sparse slice can't over-fit).
**Plan (sketch):** `options/lib/pricer/smile/_shift.py` — `shift_smile(prior: SmileResult, live_points,
new_forward, new_tte) → SmileResult`: (1) re-anchor the prior into the new `(k, τ)` frame in `w`-space,
(2) solve the additive-`w` shift (DoF = min(point-count rule, n_points)) by LS on the live residuals,
(3) keep the butterfly no-arb check. Facade hook on `OptionsPricer` (e.g. `fit_smile(...,
fallback='shift', prior=...)`) so a sparse slice degrades gracefully to a shifted prior.
**Open questions (owner — to lock before build):**
1. **Prior source** — where does the prior smile come from? Options: (a) last EOD `fit_smile` result
   persisted to the reference sidecar (`_meta.parquet`/a new `_smile.parquet`, per T25); (b) refit
   on-the-fly from the last full slice in `df_hist`; (c) caller-supplied `prior=`. Default?
2. **Staleness guard** — max age of the prior before a shift is refused (raise / warn / fall back to
   a flat-vol guess)? E.g. reject if prior older than N sessions / the underlying moved > X%.
3. **Minimum live points** — is 1 point enough to act on (parallel shift), or require ≥2? And a
   guard when live points are all on one wing (e.g. only OTM puts) — cap DoF / widen the prior weight?
4. **DoF→shift mapping confirm** — slope/curvature in `w`-space as a low-order polynomial in `k`
   (level = `c₀`, slope = `c₁·k`, curvature = `c₂·k²`)? Any cap on the curvature term to stay no-arb?
5. **Re-anchor when τ is unchanged** (same-day intraday) — skip the TTE recompute and shift only on
   the forward move, or always re-evaluate in the new frame?
**Notes:** math → D2 (Type C). Composes with T27 (a shifted live smile can seed the forecast θ; and
pairs with the analogue model it.6).

### T31. **Spot** domain (R4.3 / R4.5 — neutral-core reuse)
**Status:** planned. The core vocabulary/classification split (T26) already separated a neutral core
(`Term`, `InstrumentKind`, `AssetClass`) from the options extensions, **so a spot domain can be
added without dragging in derivatives terms.** **Goal:** a `spot` capability area parallel to
`options` — an `alphavar.spot` package (entities + lib + a `Spot` facade over a `SpotData`) for cash
instruments (no expiration / strike / greeks). Reuses: the `Col` registry + neutral `Term`, the
provider/exchange data path (R1/R2), reference-vs-series (T25, asset-level `AssetMeta`), the forecast
**price**/**vol** targets (no smile/surface). **Plan:** define the spot entity/schema (identity +
OHLC/price/volume, no contract layer), wire a provider, add `SpotForecast` (price/vol only). **Notes:**
new domain → confirm the neutral-core boundary holds (no options leakage); ADR if it reshapes R4.

### T32. **Bonds** domain (R4.3 / R4.5)
**Status:** planned. **Goal:** a `bonds` capability area — `alphavar.bonds` (entities + lib + facade)
for fixed-income instruments: identity + coupon schedule, day-count, yield/price/duration/convexity,
and a **rates / yield-curve** layer (the curve is the bond analogue of the vol surface). Reuses the
neutral core (T26) + provider path (R1/R2) + reference-vs-series (T25, schedule/credit as reference).
New domain math (yield↔price, accrued interest, curve bootstrap/interpolation) → its own pure lib
(R5, pure-numpy per repo convention). Forecast targets: `price`/`yield`, and a `curve` target
analogous to `surface` (reuse the constant-maturity interpolation idea on the yield curve). **Notes:**
needs an ADR (new asset class + rates entity); confirm what is shared vs bond-specific in core.

### T33. **Portfolio** management (cross-domain)
**Status:** planned. **Goal:** position/portfolio aggregation, P&L, and **risk (VaR/CVaR)** fed by the
forecast distributions (T27) across instruments. **Owner split (2026-06-19):**
- **Options portfolios** — likely **based in `options` itself** (the existing chain/leg/payoff machinery
  — `analytic/risk/payoff` — already models multi-leg option structures; a portfolio is the natural
  extension of a strategy/desk). Build the options-portfolio layer where that lives.
- **General portfolio management** (for **bonds** + **spot**, and ultimately mixed books) — a
  **cross-domain** portfolio layer that holds positions across asset classes, aggregates exposure, and
  computes portfolio VaR/CVaR by combining per-instrument forecast distributions (correlations across
  assets). Likely a new top-level `alphavar.portfolio` (depends on the domain packages, not vice-versa).
**Plan:** start from the options side (reuse payoff/greeks aggregation), then lift the
asset-class-neutral pieces (position book, exposure roll-up, distributional VaR/CVaR) into the shared
portfolio layer as the spot/bonds domains land. **Notes:** depends on T27 (distributions) + T31/T32
(domains); ADR for the cross-domain portfolio boundary.

### T35. **Risk** domain / layer (cross-domain, consumes forecasts)
**Status:** planned (owner-added 2026-06-19). A dedicated **risk** capability area — distinct from
**portfolio** (T33, which holds positions / aggregates exposure): risk *measures* the loss
distribution. The existing `options/lib/analytic/risk` (payoff / P&L profiles) is the seed; this
lifts risk into a first-class, asset-class-neutral layer that turns **forecast distributions (T27)**
into risk numbers.
**Goal:** a `risk` layer (likely `alphavar.risk`, neutral; or `options/lib/risk` first, then lifted)
computing, from a position/portfolio + the per-instrument forecast distributions:
- **VaR / CVaR (expected shortfall)** at a confidence + horizon — analytic (from the lognormal /
  parametric terminal) **and** empirical (from MC / bootstrap scenarios, reusing `ForecastResult.
  scenarios` / `SmileForecast` / `SurfaceForecast` draws). Pure-numpy quantiles (repo convention).
- **Scenario / stress** — revalue under shifted forecast inputs (spot ±, vol ±, smile/surface shift —
  composes with T30's smile-shift) and report the P&L distribution; greeks-based (delta/vega/gamma)
  **and** full-reval modes.
- **Aggregation** — combine instrument distributions with a **correlation / copula** assumption across
  assets (the cross-asset coupling that portfolio VaR needs); marginal vs component VaR.
**Plan (sketch):** `risk/_measures.py` (`var`, `cvar`, `expected_shortfall` over a distribution or a
scenario array), `risk/_scenario.py` (stress grid → reval via the pricer/payoff), `risk/_aggregate.py`
(correlated scenario combination); facade `OptionsRisk(OptionsData)` → `Option.risk` for the
single-instrument case, lifted to the portfolio layer (T33) for books. **Notes:** depends on T27
(distributions) and pairs with T33 (portfolio) — keep the **measure** (risk) and the **position book**
(portfolio) as separate concerns. Math → D2 (Type C); ADR if it introduces a cross-asset correlation
entity.

### T34. Split the TASKS file: archive (done) vs active plan
**Done (2026-06-19):** moved the completed refactoring/remediation backlog (Closed P0/P1, Blocks
A/B/C, R0, T19–T24, and the done P3 tasks T21/T22) to
[TASKS_ARCHIVE.md](TASKS_ARCHIVE.md); this active file now carries only the in-flight work (T27
forecast, T28) + the P4 feature plan + a fresh status, with the [D2 ledger] pointer kept and a link
to the archive. No task lost; the D2 ledger stays the source of truth for the D2-pending backlog.

### T36. Implement the planned `knowledge/` concepts that have no code yet
**Status:** planned (owner-confirmed 2026-06-20). **Context:** `agents/shared/knowledge/` was lifted
to the root `knowledge/` layer (keystone three-layer model: knowledge → `src/` → USAGE `skills/`).
Concepts whose code exists got a `knowledge/` leaf + a USAGE skill (chain, pricing/IV, smile, payoff,
exchanges). The concepts below are **planned but not yet coded**, so per the keystone rule
([keystone README §3b](keystone/README.md)) they stay in `knowledge/` **with this task** and get
**no** USAGE skill until the code lands. For each: implement under `src/alphavar/...`, point the
`knowledge/` leaf **down** to it, then add a `concept → function` USAGE skill. **D2 owner-verify the
math** for each.

- **Full Greeks** — `knowledge/options/pricing/greeks.md`. Only `bs_vega` exists; add delta `∂V/∂S`,
  gamma `∂²V/∂S²`, theta `∂V/∂t`, rho `∂V/∂r` (closed-form Black-76). Source: Hull.
- **Sortino ratio** — `knowledge/risk/ratios/sortino.md`. `(Rp − T)/DD`, downside deviation
  `DD = sqrt(mean(min(0, Rᵢ − T)²))`. Source: Sortino & Price (1994).

> **VaR / CVaR** (`knowledge/risk/var/methods.md`, `cvar-expected-shortfall.md`) are **already
> planned** under **T31/T32/T33** (the risk / portfolio domain). Do not duplicate here — when those
> land, point those `knowledge/` leaves down to the new code and add the USAGE skills.

Until coded, mark each affected `knowledge/` leaf "**planned — not yet implemented (T36 / T31–T33)**"
so the knowledge↔impl chain stays honest.
