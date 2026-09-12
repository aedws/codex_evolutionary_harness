# AGENTS.md — Evolutionary Harness Operating Contract

This repository uses an evidence-driven, evolution-capable development harness.

## Mission
Do not treat your own narration as project truth.

```text
Reality → Evidence / Event → Derived State → Human-readable Projection → Interpretation / Action
```

Evolution flow:

```text
Failure / Friction → HARNESS-REQ → Candidate Harness Change → Sandbox Eval → Promotion Gate → Harness Release
```

## First Read Order
1. `docs/harness/README.md`
2. `docs/harness/source-authority.md`
3. `docs/harness/policy.md`
4. `docs/harness/checkpoint.md`
5. task-relevant files only

Do not load every harness document unless needed.

## Work Modes
- `query`: inspect/explain only
- `analysis`: inspect and propose; no mutation
- `plan`: register work/decision state; no implementation unless explicitly requested
- `execute`: implement within granted scope

Read-only requests do not authorize repository mutation.

## Required Execution Discipline
For any mutable task:
1. create/reuse stable Task ID;
2. create Execution ID;
3. inspect current evidence and relevant relations;
4. preserve unrelated state;
5. implement only authorized scope;
6. verify with smallest sufficient test set;
7. create evidence tied to tested code/data version;
8. append material events;
9. derive status from evidence;
10. update checkpoint/projections.

Never claim `implemented`, `verified`, `released`, `deployed`, `accepted`, or `current` without evidence.

## Side Effects
Explicit authorization is required unless already granted for this task: commit/push/merge, production deploy, destructive data changes, public publishing, paid resources, credential changes, external deletion.

Use idempotency protection for side-effecting operations.

## Relation Provenance
Use one of:
`confirmed_by_code`, `confirmed_by_test`, `confirmed_by_runtime`, `confirmed_by_user`, `inferred_by_static_analysis`, `inferred_by_llm`, `unknown`.

Never promote `inferred_by_llm` to confirmed without independent evidence.

## Human Judgment Boundary
Classify acceptance as `machine_verifiable`, `human_verifiable`, or `mixed`.
Do not convert subjective product quality into machine truth.

## Harness Evolution
Detect repeated failure, stale-evidence use, relation misses, missed tests, false policy blocks, manual workarounds, repeated human corrections, unnecessary retries, and redundant context loading.

Do not immediately rewrite the harness. When evidence is sufficient, create a `HARNESS-REQ` candidate.

All harness changes declare scope: `execution-local`, `project`, `domain`, or `core`.
Higher-scope promotion requires broader evidence.

## Stability Anchors
Do not automatically rewrite/delete historical evidence, disable event/audit history, change root source authority, expand destructive capabilities or credential scope, remove rollback, weaken eval integrity, or redefine human-verifiable acceptance as machine-verifiable.

## Completion Report
Report only: changed; verified; unverified/stale; blocked/conflicts; evidence created; events recorded; external actions; harness friction/improvement candidates; next allowed action.
