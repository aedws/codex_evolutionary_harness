# Overlay composition, evaluation and propagation — contract 5

## E01 — Composition and compatibility

Pin Core, optional Domain and Project identities/versions/digests. An overlay declares scope, base contract range, additions, restrictions, source/decision refs, dependencies, eval and compatibility refs. Allowed additions are namespaced source bindings, acceptance/test contracts, tools/skills and domain/project rules. An unknown required extension or conflicting meaning blocks dependent actions; do not use last-write-wins.

Compute and retain an effective composition manifest. Top-level protected authority, evidence/provenance semantics, human acceptance, retention, eval integrity and rollback invariants are not freely overrideable. A local need for a common change becomes F04 feedback, not an undocumented Core fork. Project-specific source values stay in project records; the common seed contains empty bindings.

Version axes are distribution, contract/record schema, derivation rules, command protocol, adapter/skill and execution environment. Unknown required semantics fail closed; optional namespaced metadata is retained without granting meaning. Readers do not auto-migrate during queries. Compatibility records name from/to digests, test fixtures, preserved/lost fields, data transformations, limits and rollback proof. Contract 2 adds required review/feedback/operational clauses; contract 1 adopters need reviewed migration, not blind overwrite.

The composition manifest records exact package and content identities for Core, every selected Domain and Project, dependency DAG, explicit domain order, extension schemas, per-key ownership/merge operator, source provenance and resulting digest. Resolve version ranges to immutable pins before evaluation; never use floating latest/branch as a reproducible input. Missing pins, dependency cycles, incompatible required schemas and unequal duplicate namespace definitions block composition.

Extension points declare namespaced ID, owner, allowed scope, input/output version and validation/compatibility cases. Rules/tools/skills/evals are keyed by identity, not concatenated positionally. Identical entries may deduplicate while preserving both sources; unequal entries with the same ID conflict. Effective grants intersect applicable limits, denials accumulate, required safety checks accumulate, and scalar/domain-semantic values require an explicitly declared compatible operator; there is no implicit last-wins merge. Absence of a grant cannot be interpreted as permission. A conflict receipt includes key, competing sources/values, blocked actions and resolution authority. A new reviewed version/resolution must pass the relevant fixtures; a local patch cannot silently alter the pinned core.

## E02 — Reproducible and independent Eval

Freeze baseline/candidate source, input/fixture/acceptance/grader/rule/environment digests and metrics before evaluation. Cover original failure, unaffected regression, negative/counterexample, stale/conflict, duplicate request and relevant interruption/restore cases. Record run identity, raw results and all failed/deferred runs; don't select only successes.

Use deterministic/environment outcomes before subjective graders. The proposer must not change the grader, expected answer or acceptance after seeing results to make a pass; a necessary grader change is a separately reviewed candidate and invalidates the old comparison. Hold-out or cross-project evidence must not merely duplicate the proposal's own examples. Independent means independently reproducible evidence/evaluation authority, not two messages from the same agent. Record proposer, evaluator, decision-maker, overlap and limitations explicitly.

Trust gates (false_verified, duplicate effects, unapproved mutation, history loss, human-boundary violation) cannot regress. Compare manual intervention, retry/context volume, workflow/contract size, maintenance cost and latency on the same workload. State metric units, sample/population, noise/uncertainty and preset thresholds. Fewer rules or smaller context qualify as improvement only when trust remains within the gate; no benchmark means no optimization superiority claim.

An optimization comparison pre-registers workload IDs and difficulty/risk strata, baseline/candidate pins, execution order or matched replay, repetitions/sample rule, estimator/uncertainty method, per-metric non-inferiority margins, missing-data rule and decision authority. Use the same acceptance and trust tests. The denominator is all attempted cases including failed, deferred and excluded cases with reasons; an exclusion cannot disappear after results are seen. Report per-project/stratum as well as pooled results so a weak cohort is not hidden by an average.

Hard trust violations require zero observed false_verified, duplicate effects, unapproved mutation, history loss and human-boundary violations in the evaluated workload. Baseline defects do not authorize retaining these violations. Zero observations alone do not prove safety or statistical equivalence. Other reliability metrics must meet predeclared non-inferiority criteria with adequate samples; absent metrics or an underpowered/unstable comparison means inconclusive.

Measure rule count together with total normative text/complexity (splitting or hiding rules is not reduction), cumulative model context across attempts/subagents (input/output/tool results; bytes labeled separately if tokens unavailable), and human intervention count plus minutes/rework. Include eval/review, migration, maintenance and failure recovery costs over a declared horizon; moving effort outside the recorded task is not savings. Record actual values/units and uncertainty. Claim optimized only if trust gates pass, at least one preset cost objective improves by its minimum meaningful amount, and remaining costs stay within preset budgets or an explicitly accepted tradeoff. Otherwise report non_regressed, tradeoff_pending, regressed or inconclusive with metric-specific reasons. Do not compress them into a single unqualified score.

## E03 — Promotion decision and maintenance

| Scope transition | Required gate |
|---|---|
| Execution-local → Project | Version-bound local eval, applicable authority, regression and recovery path |
| Project → Domain | Same causal pattern in at least two independent same-domain projects, removed project assumptions, domain eval, complexity and compatibility |
| Domain → Core | Multiple domains, removed domain-specific semantics, core regression/compatibility/rollback and acceptable complexity |

Record candidate origin, independent contexts, assumptions/counterexamples, decision actor/authority, accepted scope, exact diff digest, eval refs and reasons. Rejection, deferral, withdrawal and supersession are preserved. A local pass can justify upstream submission before generalization is proven, but not universal adoption.

Keep seed-maintenance decisions separate from empirical promotion. A user-authorized correction/completion of this initial contract baseline may be released with explicit local/design evidence and unverified generality; it must not be labeled cross-domain-proven or used to bypass protected changes. Scope labels do not grant write/merge/release rights. High-risk decisions are never self-approved; authorized low-risk automation requires preset gates and revocable scoped authority.

Generalization is an explicit transformation: observed local failure → causal invariant → project assumptions removed/parameterized → domain applicability predicate → candidate scope → independently evaluated contexts. Record eligibility conditions, prerequisites, excluded environments, counterexamples, adverse cases and what evidence would falsify the claim. Distinguish the change's applicability predicate from a claim of universal correctness. A project outside the predicate stays pinned/not_applicable; do not silently broaden the predicate after seeing a pass.

The evaluation matrix identifies project/domain IDs (authorized pseudonyms allowed), ancestry/shared fixtures, relevant stack/risk/environment, baseline/candidate input digests, proposer/evaluator, applicable and non-applicable cases, raw results and uncertainty. At least two independent same-domain projects support Domain; Core needs at least two distinct domains with evidence supporting the claimed scope. Repeated runs, renamed forks or copied fixtures do not create independent projects/domains. A separate holdout fixture/context is fixed before evaluation; contamination or shared evaluator authority is disclosed, not counted as independence automatically. Restricted/unavailable evidence remains needs_evidence. A failing eligible cohort blocks promotion until the candidate is revised or its scope is narrowed by a new decision and reevaluation. Keep failed candidates, exclusions and dissent in lineage.

## E04 — Release, canary and stop conditions

A release links accepted candidates/decisions to immutable source, package and overlay digests, verified capability evidence, supported versions, migration/rollback plans and limits. Preserve old tags/assets and event history. Changing the seed's distribution number never automatically raises V2/V3/V4 capability status.

Before rollout declare baseline/target, selected and excluded cohorts with rationale, evaluation window/work-count, metrics and thresholds, observation completeness, decision authority, write scope, abort and rollback target. Canary runs need compatibility pass plus recoverability, actual target observations and explicit enrollment authority. Projects may choose pinned/manual/blocked without being marked failed.

Rollout states derive from records: proposed → compatibility_checked → canary → expanded → adopted, with pinned/blocked/aborted/rollback_pending/rolled_back/unknown. No controller is implied by these names. Missing telemetry or insufficient samples cannot authorize expansion. Stop on any trust-gate violation, unexpected scope/effect, incompatible record or unavailable rollback; isolate affected scope, preserve observations and do not roll out farther.

Canary success requires preset conditions across the declared window, not one successful run. Expansion is a separate authorized decision tied to the evaluated digest; source/policy/base drift invalidates it. Rollback verification checks both identity and required behavior. A rollback failure blocks dependent activation until actual state is known.

Select cohorts from a declared eligible population by a recorded method covering relevant domain/stack/risk strata, with matched baseline/control where feasible, exclusions and enrollment authority. Bound the initial blast radius and concurrent changes; selecting only the easiest successful projects is not representative. Unsafe/irreversible operations without a validated recovery or bounded compensation path are ineligible for autonomous canary. Record observation start, minimum elapsed duration AND minimum completed work/sample count, maximum deadline/budget, telemetry completeness/freshness and expected delayed effects. Values must be supplied before enrollment; null is unknown, never zero or unlimited. Low traffic after the time window is inconclusive; do not expand solely because time passed.

| Observation | Decision and required receipt |
|---|---|
| Compatibility/recovery/enrollment unresolved | pinned/blocked; no activation |
| Hard trust breach, scope escape or incompatible data | stop expansion immediately; isolate scope and authorized rollback/compensation |
| Telemetry gap, uncertain effect or insufficient samples | pause/unknown; preserve evidence, inspect; deadline exhaustion cannot pass |
| Both minimum duration and work met, telemetry complete, all preset gates pass | eligible for a separately authorized expansion; exact cohort/digest/decision receipt |
| Reproducible release-wide regression | mark release withdrawn for new adoption, notify only through authorized routes, inventory affected/pinned projects |
| Rollback succeeded/failed | verified restored identity+behavior / rollback_pending with escalation and no further activation |

Withdrawal prevents new adoption; it does not delete an immutable release/tag or assert every project was rolled back. Record per-project applied/unchanged/unreachable/compensation-pending states and later observations. A corrected release gets a new identity. Emergency decision authority, stop/rollback latency targets and fallback contact/path are configured in advance; a missing actor prevents autonomous enrollment.

## E05 — Adoption, migration and return observation

Upgrade by a separate pinned checkout: inspect contract/schema/effective-overlay diff → inventory actual project changes → snapshot records/user files → compatibility/rollback plan → explicit application → verification. Preserve project data, events, human decisions, locally owned skills and overlays. No automatic reinstallation over active records; base mismatch or manual drift is conflict.

Migration identifies expected input revision, per-file ownership, before/after digests, schema transformations, record/reference counts, preservation invariants, rollback limitations and validation. New required fields start unknown unless independently sourced; do not copy sample answers as truth. Resume only after checking partial effects. If later events make reverse migration unsafe, retain them and choose forward repair.

Adoption records installed seed/overlay digests, local eval/acceptance, canary decision where applicable and restoration proof. Follow up on the originating failure and cost metrics. Send/pull an authorized outcome back to its candidate lineage through F07, including recurrence or regression. Project feedback and upstream releases form a closed loop only when these return observations exist.

## E06 — Capability and completeness reporting

For every claimed capability, separate documented contract, implemented mechanism, local test, runtime observation and human acceptance. The coverage map proves navigation and declared obligations only, not semantic correctness or operating automation. V2 needs actual evidence/state/policy/recovery mechanisms; V3 needs observed local improvement; V4 needs cross-context promotion and safe downward propagation.

Expose missing evaluators, sources, actors and telemetry as unknown/deferred with next actions. Human/mixed acceptance remains with the authorized human. No audit report, skill, matrix or passing packaging test can certify the complete long-term harness by itself.
