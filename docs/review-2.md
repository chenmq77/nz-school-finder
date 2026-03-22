# Requirement Challenge — Round 2 of 2

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-23 11:31:04

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 6

### COMPLETENESS
- Core decision questions: PARTIAL — the proposal answers per-site-type reuse directionally, but it does not explicitly resolve scheduled updates or define when Scrapling is no longer sufficient.
- Accuracy-first workflow: PARTIAL — mandatory human review is defined, but approval states, partial acceptance, rejection handling, and conflicting-source resolution are not.
- Site variability coverage: COVERED — the classifier plus template strategy addresses major school site families and common external providers at a useful high level.
- Failure and edge handling: GAP — no behavior is defined for missing sites, robots denial, login-gated content, scanned PDFs, anti-bot blocks, or schools with mixed platforms.
- Operational scalability for 50-100 schools: PARTIAL — the pipeline is plausible for a pilot, but retry/resume rules, crawl status tracking, and per-school terminal states are missing.
- Testability and acceptance criteria: GAP — confidence scoring exists, but no benchmark set, measurable quality bar, or reviewer checklist makes success verifiable.
- Scope control: PARTIAL — the scope is correctly narrowed to Auckland secondary schools, but investing in 5-8 templates before coverage is proven may still be premature.

### ISSUES
1. [critical] Requirement coverage — Two original questions remain effectively unresolved: update cadence and tool-boundary choice. The proposal hints at annual reruns and keeps Scrapling by default, but it does not state a decision, non-goals, or triggers for moving to heavier browser automation.
2. [critical] Workflow/state model — There is no explicit per-school outcome model such as `COMPLETE`, `PARTIAL`, `BLOCKED`, `UNSUPPORTED`, or `REJECTED_BY_REVIEW`. Without terminal states, the pipeline cannot reliably support retries, reporting, or manual triage.
3. [major] Reuse strategy — "Template per site type" is directionally correct, but it is underspecified. You need a defined override/versioning model for schools that are mostly WordPress/Wix but have school-specific navigation, external portals, or custom PDFs.
4. [major] Discovery boundaries — The fixed depth limit of 2 and homepage-first assumption are brittle. Course handbooks, fee schedules, and sports pages may live deeper, on separate subdomains, or only in linked documents.
5. [major] Dependency risk — LLM extraction, JS rendering, PDF parsing, and third-party providers such as SchoolBridge/Sporty are all external dependencies, yet no degraded mode or fallback path is defined when any of them fail.
6. [major] Testability — The `confidence < 0.7` rule is arbitrary without calibration. The proposal needs measurable acceptance criteria such as required fields, reviewer checklist, benchmark schools, and minimum extraction precision/recall on a sample set.
7. [minor] Scope discipline — Site-type distribution analysis is sensible, but committing upfront to 5-8 reusable templates is speculative before validating how many Auckland schools actually fit stable patterns.
8. [question] For user — When a school has only partially reliable data, do you want to store an explicitly partial record after review, or reject the school entirely until all key sections are verified?
9. [question] For user — What refresh effort is actually worth your time for a learning project: no scheduled updates, annual reruns, or only manual recrawls when you notice changes?

### SCENARIOS_ASSESSMENT
- Save crawler logic for reuse: NEEDS_WORK — the proposal reasonably prefers site-type templates plus logs, but it does not define how school-specific overrides, failures, or template drift are managed.
- Classify sites by framework/provider: NEEDS_WORK — the category set is useful, but unknown, mixed, or misclassified sites have no explicit handling path.
- Scale from 5 schools to a 50-100 school pilot: NEEDS_WORK — the architecture supports a pilot in principle, but operational controls for resume/retry/status tracking are missing.
- Extract high-accuracy data with manual review before insert: NEEDS_WORK — the review gate exists, but the approval criteria and conflict-resolution rules are not concrete enough.
- Handle WordPress/Wix/HTML/SchoolBridge/PDF-heavy variants: NEEDS_WORK — major patterns are recognized, but scanned PDFs, login walls, deep navigation, and multi-domain schools are not specified.
- Decide whether Scrapling is enough: MISSING — there is no explicit evaluation framework or escalation threshold for introducing a heavier tool.
- Decide whether scheduled updates are needed: MISSING — refresh policy is still implicit rather than defined.

### ARCHITECTURE_ASSESSMENT
- Fitness: 6
- Risks: site misclassification leading to wrong extraction strategy; brittle discovery due to fixed depth; heavy dependence on LLM/PDF/rendering quality; undefined partial/blocked outcomes; manual review load becoming inconsistent without a checklist
- Suggestions: define a per-school state machine and artifact schema; use site-type templates plus lightweight per-school overrides instead of full per-school code; define explicit criteria for when Scrapling is enough and when browser automation is required; make refresh policy explicit even if the decision is "out of scope for v1"; validate the template hypothesis on a benchmark set before expanding

### SUMMARY
The proposal is materially better than round 1 and is directionally sound for an accuracy-first learning project: narrowing scope, using site-type templates, and requiring human review are all sensible. However, it is still not a complete execution spec because key decisions about refresh policy, tooling boundaries, failure states, and measurable acceptance criteria remain undefined; those gaps will create rework and inconsistent outcomes even within a 50-100 school pilot.
