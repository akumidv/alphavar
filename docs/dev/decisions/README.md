# Decision records (ADR)

Short, dated records of **accepted architectural decisions** and the reasoning behind
them. They complement the requirement docs (`../ARCHITECTURE_REQUIREMENTS.md` R#,
`../DEVELOPMENT_REQUIREMENTS.md` D#): the R#/D# rules say *what the invariant is*; an ADR
records *a decision to act* (a migration, a retirement, a phased rollout) and why, so the
choice isn't re-litigated later.

Convention:
- One file per decision: `NNNN-kebab-title.md` (zero-padded, monotonic).
- Header: `Status` (Proposed / Accepted / Superseded by NNNN), `Date` (absolute),
  `Owner`.
- Body: Context → Decision → Consequences (incl. data/migration impact) → Rollout →
  References (R#/D#, backlog ids).
- Keep it short; link to R# rules instead of repeating them.

## Index
- [0001 — InstrumentKind/ContractKind as the canonical instrument kind everywhere](0001-instrument-kind-canon.md)
