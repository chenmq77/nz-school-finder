# Requirement Challenge — Round 1 of 2

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-23 11:21:17

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 5

### COMPLETENESS
- Crawl flow coverage: PARTIAL — The proposal covers fetch, clean, extract, and validate, but does not define how relevant pages and PDFs are discovered before extraction.
- Human-in-the-loop process: GAP — The requirement says some subject classification needs manual judgment, but no review or escalation workflow is defined.
- Refresh/update strategy: GAP — Scheduled updates are raised as a core question but never resolved into a concrete policy.
- Operational model: PARTIAL — robots.txt compliance and 2-second rate limiting are stated, but concurrency, retries, crawl budget, and runtime at 2577-school scale are unspecified.
- Data quality and auditability: PARTIAL — Validation is mentioned, but provenance, source snapshots, conflict handling, and partial-data rules are missing.

### ISSUES
1. [critical] Crawl scope and source discovery — The design assumes a general crawler plus a school URL list is enough, but the required data is typically spread across multiple subpages, PDFs, and sometimes external domains — define page discovery, crawl depth, document selection, and per-field source tracing.
2. [major] Human review and uncertainty handling — The requirement explicitly allows cases where AI cannot safely decide, but the architecture has no confidence thresholds, review queue, or partial approval flow — add manual verification steps for ambiguous mappings and low-confidence extractions.
3. [major] Scale and failure behavior — Batch crawling with dynamic rendering and LLM extraction across 2577 schools may be slow, costly, and fragile under rate limits — specify retries, backoff, stop/resume behavior, render budget, token budget, and what happens on blocked pages, broken links, missing robots rules, or timeouts.
4. [minor] Persistence strategy — Rejecting per-school scripts is reasonable, but the proposal does not define what still must be persisted for reproducibility — persist extraction schema versions, prompts, crawl logs, discovered page maps, and field-level provenance even if the crawler code stays generic.
5. [question] For user — What should v1 optimize for first: maximum school coverage, highest data accuracy, lowest maintenance effort, or lowest API/runtime cost?

### SCENARIOS_ASSESSMENT
- Single-school crawl across homepage, subpages, and PDFs: NEEDS_WORK — The target outcome is clear, but navigation and source selection rules are not defined.
- Batch expansion from 5 schools to 2577 schools: NEEDS_WORK — Batch mode is named, but prioritization, throughput expectations, and recovery behavior are missing.
- Dynamic sites such as Wix or JS-heavy pages: NEEDS_WORK — A dynamic fetcher is mentioned, but fallback behavior and cost controls are undefined.
- Ambiguous subject/category mapping requiring human judgment: MISSING — No manual review scenario is described.
- Periodic re-crawl of already processed schools: MISSING — No update cadence or change-detection rules are provided.
- Partial extraction or conflicting sources: MISSING — There is no defined behavior for incomplete records or disagreements between pages/documents.

### ARCHITECTURE_ASSESSMENT
- Fitness: 5/10
- Risks: [multi-page discovery is underspecified, LLM extraction may be inconsistent or hallucinatory, no formal human-review loop exists, reproducibility/debugging will be weak without persisted artifacts, full-scale runtime and token cost may grow beyond the intended learning-project scope]
- Suggestions: [use a staged pipeline of discovery -> retrieval -> extraction -> validation -> review, classify sites by common patterns before falling back to LLM-heavy extraction, persist provenance and run artifacts for every extracted field, define measurable acceptance criteria and confidence thresholds, add crawl-budget and failure-recovery controls before attempting large-scale batch runs]

### SUMMARY
The proposal is directionally promising because it correctly rejects fully custom per-school scripts as the long-term default and recognizes that heterogeneous sites require more than selector-based scraping. However, it is not implementation-ready yet: the biggest gaps are page discovery, human review for ambiguous data, operational behavior at scale, and reproducibility of crawl results. Without those pieces, the architecture does not yet fully support the stated goal of moving from 5 manually processed schools to reliable coverage of 2577 schools.
