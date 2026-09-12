# Evolutionary Harness

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
