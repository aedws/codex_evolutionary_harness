# Current: fixed V2 → frozen project V3

2026-09-16 rewrite: [RFC-0016](../rfcs/RFC-0016-fixed-v2-specialized-v3.md), [usage](../../README.md), [goal coverage](../requirements/FIXED-V2-GOALS.md). New seed is the default. The following text is historical through v0.12; its seed references resolve under `legacy/v0.12.0/seed/`, and its capability labels do not certify the new runtime.

---

# Evolutionary Harness

Latest implementation comparison: [seed v0.12 local parity results](../requirements/PARITY-RESULTS-20260915.md). Selected result fields pass; whole Newgame parity remains unverified.

Current goal reflection audit: [2026-09-15 initial goals versus local implementation](../requirements/GOAL-REFLECTION-20260915.md). Contract coverage, partial local mechanisms and whole-goal acceptance are counted separately; none is a product completion percentage.

Repository documentation map: [user goals](../requirements/HARNESS-GOALS.md) → [architecture RFC-0002](../rfcs/RFC-0002-hierarchical-evolutionary-architecture.md) → [reusable seed contract](../../seed/docs/harness/contract.md). The current deliverable is a versioned contract seed; V2/V3/V4 below are capability targets, not verified implementation claims.

Contract 2 adds [self-feedback RFC-0003](../rfcs/RFC-0003-feedback-common-contract.md) and [goal-to-clause coverage](../../seed/docs/harness/contracts/coverage.json). Route to relevant clauses only; original schema examples here remain development references, not executable contract-2 validators.

## Purpose
Start every project from the same evidence-driven core, then specialize through actual operational experience. Promote reusable lessons upward only after broader evaluation.

```text
Universal Core
   ↓ specialization
Domain Overlay
   ↓ specialization
Project Overlay
   ↓
Project Execution
   ↑ lessons
Domain Candidate
   ↑ generalization
Core Candidate
```

## Human-facing vs Internal Model
Humans work with familiar objects: Requirement, Decision, Task, Module, Test, Release.

The harness trusts records: Event, Evidence, Execution, Relation, Policy, Eval Result, Compatibility Result.

```text
Object Interface
↑
Derived Projection
↑
Data-Oriented Processing
↑
Evidence / Events / Runs / Relations
```

## Capability Levels
### V2 — Evidence-driven
Evidence-first, events, derived state, source authority, execution identity, relation provenance, policy boundary, eval readiness, harness lifecycle.

### V3 — Project self-improvement
Failure/friction aggregation, HARNESS-REQ proposals, candidate harness changes, historical replay, sandbox comparison, low-risk local promotion.

### V4 — Hierarchical evolution
Core/domain/project hierarchy, upward generalization, downward compatibility evaluation, cross-project/cross-domain evals, canary rollout, rollback lineage.

Version labels describe verified capabilities, not documentation claims.

## Core Rule
When uncertain, use `unknown`, `unverified`, `stale`, `blocked`, or `conflicted`. Do not invent certainty.

Current contract 3 adds [seven-area audit RFC-0004](../rfcs/RFC-0004-seven-area-assurance-audit.md) and a blank review protocol. Earlier contract-2 design evidence is retained, not promoted into runtime assurance.

Current v0.4.0 / contract 4 includes a minimal local core and [end-to-end decision RFC-0005](../rfcs/RFC-0005-end-to-end-decision-system.md). Its record/test/state/restore checks are scoped local mechanisms; full V2/V3/V4 and external/identity enforcement remain unverified.

Current v0.5.0 / contract 5 adds the mandatory bootstrap wiki gate: [RFC-0006](../rfcs/RFC-0006-bootstrap-completion-gate.md). The v0.4.0 engine remains unchanged; bootstrap readiness is separate from product readiness and human acceptance.
