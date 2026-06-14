# Tool: exchange-fixtures (record + trim)

Builds the hermetic HTTP fixtures the exchange tests replay, so the suite never hits a
live API (D1, T11). Two pieces by nature:

- **record** — an AI/dev tool that hits live APIs; code lives here: `tools/exchange_fixtures/`.
- **trim + mock** — test infrastructure (offline); code lives in `tests/utils/exchange_fixtures/`.

The recorder **reuses `alphavar.exchange`** (DeribitExchange/MoexExchange already
implement the requests) — it never re-implements HTTP calls; per-exchange modules only
declare *which* calls to capture.

## 1. Record (needs network, run rarely)

`agents/tools/exchange_fixtures/` — run when an endpoint's shape changes. Saves each raw
JSON body keyed by request path (+sorted query) under
`tests/unit/exchange/fixtures/<exchange>/` (`index.json` maps path→file). Best-effort: a
venue rejecting a call is logged and skipped.

```bash
uv run python -m agents.tools.exchange_fixtures            # both exchanges
uv run python -m agents.tools.exchange_fixtures --only moex
```

Params match the test fixtures: Deribit `BTC`, MOEX `SI` (conftest `moex_asset_code`).
Captured bodies are full (thousands of rows) — always trim next.

## 2. Trim (offline, idempotent)

`tests/utils/exchange_fixtures/trim.py` — keeps a few diverse rows per file (force-keeps
test assets SI/AFLT/SBER; otherwise ≤2 per group by kind + call/put), drops the rest.
Handles Deribit `{"result":[…]}`, MOEX bare lists, and MOEX optionboard
`{"call":[…],"put":[…]}`. Multi-MB → ~40–50 kB per exchange.

```bash
uv run python -m tests.utils.exchange_fixtures.trim --check   # report sizes, write nothing
uv run python -m tests.utils.exchange_fixtures.trim           # trim in place
```

## 3. Replay (automatic, at test time)

`tests/utils/exchange_fixtures/mock.py` builds an `httpx.MockTransport` from `index.json`;
the exchange-test `conftest.py` wires it into the Deribit/MOEX clients. No network.

## Workflow

1. `python -m agents.tools.exchange_fixtures` (network) → full fixtures.
2. `python -m tests.utils.exchange_fixtures.trim` → compact, commit-safe fixtures.
3. Tests run against the mock transport — hermetic.

Note: Deribit `kind=options` returns an API error (the venue wants singular `option`);
recording skips it. See the backlog item on splitting project enums from API-parameter
enums (the `options`/`option` bug).
