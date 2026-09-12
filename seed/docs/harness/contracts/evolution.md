# Overlay composition, evaluation and propagation — contract 2

## E01 — Composition and compatibility

Pin Core, optional Domain and Project identities/versions/digests. An overlay declares scope, base contract range, additions, restrictions, source/decision refs, dependencies, eval and compatibility refs. Allowed additions are namespaced source bindings, acceptance/test contracts, tools/skills and domain/project rules. An unknown required extension or conflicting meaning blocks dependent actions; do not use last-write-wins.

Compute and retain an effective composition manifest. Top-level protected authority, evidence/provenance semantics, human acceptance, retention, eval integrity and rollback invariants are not freely overrideable. A local need for a common change becomes F04 feedback, not an undocumented Core fork. Project-specific source values stay in project records; the common seed contains empty bindings.

Version axes are distribution, contract/record schema, derivation rules, command protocol, adapter/skill and execution environment. Unknown required semantics fail closed; optional namespaced metadata is retained without granting meaning. Readers do not auto-migrate during queries. Compatibility records name from/to digests, test fixtures, preserved/lost fields, data transformations, limits and rollback proof. Contract 2 adds required review/feedback/operational clauses; contract 1 adopters need reviewed migration, not blind overwrite.

## E02 — Reproducible and independent Eval

Freeze baseline/candidate source, input/fixture/acceptance/grader/rule/environment digests and metrics before evaluation. Cover original failure, unaffected regression, negative/counterexample, stale/conflict, duplicate request and relevant interruption/restore cases. Record run identity, raw results and all failed/deferred runs; don't select only successes.

Use deterministic/environment outcomes before subjective graders. The proposer must not change the grader, expected answer or acceptance after seeing results to make a pass; a necessary grader change is a separately reviewed candidate and invalidates the old comparison. Hold-out or cross-project evidence must not merely duplicate the proposal's own examples. Independent means independently reproducible evidence/evaluation authority, not two messages from the same agent. Record proposer, evaluator, decision-maker, overlap and limitations explicitly.

Trust gates (false_verified, duplicate effects, unapproved mutation, history loss, human-boundary violation) cannot regress. Compare manual intervention, retry/context volume, workflow/contract size, maintenance cost and latency on the same workload. State metric units, sample/population, noise/uncertainty and preset thresholds. Fewer rules or smaller context qualify as improvement only when trust remains within the gate; no benchmark means no optimization superiority claim.

## E03 — Promotion decision and maintenance

| Scope transition | Required gate |
|---|---|
| Execution-local → Project | Version-bound local eval, applicable authority, regression and recovery path |
| Project → Domain | Same causal pattern in at least two independent same-domain projects, removed project assumptions, domain eval, complexity and compatibility |
| Domain → Core | Multiple domains, removed domain-specific semantics, core regression/compatibility/rollback and acceptable complexity |

Record candidate origin, independent contexts, assumptions/counterexamples, decision actor/authority, accepted scope, exact diff digest, eval refs and reasons. Rejection, deferral, withdrawal and supersession are preserved. A local pass can justify upstream submission before generalization is proven, but not universal adoption.

Keep seed-maintenance decisions separate from empirical promotion. A user-authorized correction/completion of this initial contract baseline may be released with explicit local/design evidence and unverified generality; it must not be labeled cross-domain-proven or used to bypass protected changes. Scope labels do not grant write/merge/release rights. High-risk decisions are never self-approved; authorized low-risk automation requires preset gates and revocable scoped authority.

## E04 — Release, canary and stop conditions

A release links accepted candidates/decisions to immutable source, package and overlay digests, verified capability evidence, supported versions, migration/rollback plans and limits. Preserve old tags/assets and event history. Changing the seed's distribution number never automatically raises V2/V3/V4 capability status.

Before rollout declare baseline/target, selected and excluded cohorts with rationale, evaluation window/work-count, metrics and thresholds, observation completeness, decision authority, write scope, abort and rollback target. Canary runs need compatibility pass plus recoverability, actual target observations and explicit enrollment authority. Projects may choose pinned/manual/blocked without being marked failed.

Rollout states derive from records: proposed → compatibility_checked → canary → expanded → adopted, with pinned/blocked/aborted/rollback_pending/rolled_back/unknown. No controller is implied by these names. Missing telemetry or insufficient samples cannot authorize expansion. Stop on any trust-gate violation, unexpected scope/effect, incompatible record or unavailable rollback; isolate affected scope, preserve observations and do not roll out farther.

Canary success requires preset conditions across the declared window, not one successful run. Expansion is a separate authorized decision tied to the evaluated digest; source/policy/base drift invalidates it. Rollback verification checks both identity and required behavior. A rollback failure blocks dependent activation until actual state is known.

## E05 — Adoption, migration and return observation

Upgrade by a separate pinned checkout: inspect contract/schema/effective-overlay diff → inventory actual project changes → snapshot records/user files → compatibility/rollback plan → explicit application → verification. Preserve project data, events, human decisions, locally owned skills and overlays. No automatic reinstallation over active records; base mismatch or manual drift is conflict.

Migration identifies expected input revision, per-file ownership, before/after digests, schema transformations, record/reference counts, preservation invariants, rollback limitations and validation. New required fields start unknown unless independently sourced; do not copy sample answers as truth. Resume only after checking partial effects. If later events make reverse migration unsafe, retain them and choose forward repair.

Adoption records installed seed/overlay digests, local eval/acceptance, canary decision where applicable and restoration proof. Follow up on the originating failure and cost metrics. Send/pull an authorized outcome back to its candidate lineage through F07, including recurrence or regression. Project feedback and upstream releases form a closed loop only when these return observations exist.

## E06 — Capability and completeness reporting

For every claimed capability, separate documented contract, implemented mechanism, local test, runtime observation and human acceptance. The coverage map proves navigation and declared obligations only, not semantic correctness or operating automation. V2 needs actual evidence/state/policy/recovery mechanisms; V3 needs observed local improvement; V4 needs cross-context promotion and safe downward propagation.

Expose missing evaluators, sources, actors and telemetry as unknown/deferred with next actions. Human/mixed acceptance remains with the authorized human. No audit report, skill, matrix or passing packaging test can certify the complete long-term harness by itself.
