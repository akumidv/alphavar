# Pipeline: options-analyst

Ordered playbook. Read-only (**G5**); halt on any data problem (**G2**); source every
number (**G1**).

## Steps

1. **Snapshot** — load the current options/futures snapshot for the underlying through
   `alphavar` (the provider interface), not raw venue calls. Record the data timestamp.
2. **Enrich** — compute intrinsic/time value, moneyness (ATM/ITM/OTM), Greeks and IV via
   `alphavar` enrichment. Use the canonical columns (R#); do not hand-derive.
3. **Build the surface** — assemble the chain and the IV surface across strikes and
   expiries.
4. **Scan** — flag candidates (e.g. IV outliers vs the surface, rich/cheap time value).
   Knowledge: [`../../skills/`](../../skills/) (USAGE — domain concept→function map).
5. **Report** — output a shortlist; **every figure cites its source** (quote timestamp +
   computation) per G1. If a step hit stale/missing data, halt and say so (G2) — do not
   paper over it.
6. **Record** — append anything missing/wrong/insightful to `memory/findings.md` for the
   learn loop (the build agent turns it into a skill/tool/fix).

## Verify

- [ ] No order placed, no write to any venue (read-only, G5).
- [ ] Every reported number is sourced (G1); no silent fill-ins (G2).
- [ ] Columns/semantics are the canonical ones (R#), not raw venue fields.
- [ ] Findings (gaps/insights) captured in `memory/findings.md`.
