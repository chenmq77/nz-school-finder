# Requirement Challenge — Round 2 of 8

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-26 22:19:52

---

我已经拿到任务文档，正在按其中的评审维度逐项挑战提案，重点核对场景覆盖、边界条件、架构支撑和只能由用户拍板的决策点。### VERDICT: CHANGES_REQUESTED

### SCORE: 6

### COMPLETENESS
- [school-level extraction scope]: PARTIAL — The proposal covers summary-table extraction and subject Top 10 ingestion, but key field semantics and units are still not fully locked down.
- [end-user flows]: PARTIAL — List-page UE and detail-page NCEA views are defined, but the detail UI depends on unresolved assumptions about what the level metrics actually mean.
- [failure and boundary handling]: PARTIAL — Unmatched names and transaction rollback are covered, but true orphan schools, Top 10 tie cases, and non-interactive import behavior are not specified.
- [dependency and parser resilience]: PARTIAL — The design clearly depends on PyMuPDF and a stable PDF text layout, but there is no fallback or resilience strategy if extraction output is inconsistent.
- [acceptance criteria]: GAP — A 10-school sample check is not enough to prove correctness for 80+ schools plus 11 subject ranking tables.
- [scope control]: COVERED — Regional summaries, historical trends, and comparison views are explicitly deferred, so Release 1 scope is mostly controlled.

### ISSUES
1. [critical] Data semantics — The proposal assumes the Below L1 / L1 / L2 / L3 values can be shown as a "leaver distribution" and also stores `outstanding_merit` / `distinction` as percentages, but the source labels do not yet prove those are mutually exclusive buckets or percentage-based fields — this risks storing and presenting incorrect data.
2. [critical] Matching strategy — Scenario 1 says matching is exact -> normalized -> fuzzy, while the architecture section says exact -> normalized -> manual mapping only — the core join strategy is contradictory, and false-positive school matches are not safeguarded.
3. [major] Testability — "10 schools sampled" is too weak for a parser/import pipeline of this size — the plan is missing deterministic reconciliation checks such as expected row counts, percentage range assertions, duplicate detection, and per-page import totals.
4. [major] Schema consistency — The tables include a `source` column and the import deletes by `source`, but the primary key is only `(school_number, data_year)` — the model cannot actually support multiple sources for the same school/year even though the design suggests it can.
5. [minor] Dependency/operations — The extraction plan is tightly coupled to fixed PDF pages and text parsing behavior, and "script pauses" is not defined for automated or repeatable runs — this makes the workflow brittle operationally.
6. [question] For user — If a Metro school still cannot be matched to any existing `schools` row after manual review, should Release 1 add that school to master data, exclude it entirely, or allow an unlinked NCEA record?

### SCENARIOS_ASSESSMENT
- [scenario 1: data extraction and import]: NEEDS_WORK — The overall flow is sensible, but the unresolved metric semantics, contradictory matching policy, and weak validation make the import path unsafe.
- [scenario 2: list page UE column]: WELL_DEFINED — Display, null fallback, and sorting expectations are concrete and testable.
- [scenario 3: detail page NCEA overview]: NEEDS_WORK — The UI shape is clear, but the meaning of the level metrics and the unit of merit/distinction must be confirmed before the display can be trusted.

### ARCHITECTURE_ASSESSMENT
- Fitness: 6
- Risks: [misinterpreted PDF metrics, false school-name joins, parser fragility from PDF text/layout variance, schema inconsistency around `source`, insufficient validation allowing silent bad imports]
- Suggestions: [confirm the exact semantics and units of every numeric field from the PDF before freezing schema/UI, choose one matching workflow with explicit human-review rules and an audit trail, add reconciliation and assertion-based import validation, align the schema with either a single-source or multi-source strategy, define the product rule for unmatched schools after manual review]

### SUMMARY
The proposal is close to a workable Release 1 and has good scope discipline, but it is not yet safe to approve because the biggest risks are still at the data-definition and school-matching layers. Until the team confirms the exact meaning of the imported metrics, resolves the matching-strategy contradiction, and upgrades validation from sample-based checking to full import reconciliation, the architecture could successfully run while still importing or displaying incorrect school performance data.
