# Object views, derivation and context — contract 2

## V01 — Whole-project OOP surface

Requirement, Task, Decision, Module, Test and Release views organize the whole project wiki: onboarding, feature explanations, architecture, data, quality, decisions, operations and release history. Navigation and role-specific entry points are projections of the same objects/relations, not competing status stores. Plain Markdown is an allowed first implementation; a class hierarchy or a specific UI stack is not required.

Every governed view exposes stable object ID/type, purpose, authority/source, responsible actor, acceptance class/criteria, derived state and reasons, target snapshot, rule version, observation watermark/as_of, unknowns/conflicts, related objects and next allowed action. Label unavailable information explicitly. Search and overview counts state their population and denominator; do not turn object counts into product completion percentages.

Separate author-owned explanation/intent/human judgment from generated state sections. Editing prose cannot mark a test passed. Generated-region markers and expected hashes protect manual content; drift creates a conflict/diff instead of overwriting. Each state label links to its evidence and exposes stale/missing evidence in accessible text, not color alone. Empty search or removed objects must not retain a prior selected object's status as if current.

## V02 — Object action interface

An action declares ID/version, subject type, intent input, actor/authority, preconditions, expected revision/snapshot, allowed target/write set, acceptance, side-effect/idempotency class, timeout/failure classes and evidence outputs. Views show why an action is allowed/blocked; submitting it creates an Execution request, never directly sets a derived state.

Command/CLI, wiki and agent callers use the same action contract. Unknown actor/target or stale preconditions block mutation. A human decision records actor, authority source, exact scope/criteria/version, rationale and supersedes refs. Prior approval remains valid within its scope; changed payload/authority/acceptance conditions require a new applicable decision.

## V03 — Deterministic claim derivation

The derivation input is `(source_snapshot, committed_event_watermark, test_selection_contract, acceptance_digest, relation_snapshot, rule_digest, evaluation_time)`. Persist those inputs and the resulting reason/evidence set. Same inputs must produce the same canonical state; manual derivation is explicitly labeled until a reducer is independently tested.

Keep intent, progress, verification, delivery, acceptance and blockers separate. Evidence does not become trustworthy merely by being stored: verify source authority, producer identity, applicability, content integrity and observation limits.

| Condition | Required result |
|---|---|
| Unknown requirement/prerequisite/required test list | unknown; not ready and not an empty passing suite |
| Known implementation but no required runs | unverified |
| Only incompatible/old target evidence | stale, with historical pass retained |
| Latest selected required attempt still active | running; older pass does not replace it |
| Current required attempt failed | failed, including failure evidence |
| Incompatible claims for the same attempt/authority | conflicted; no convenient winner |
| Current required runs all pass and relevant integrity/blocker checks clear | verified for that exact target and acceptance scope |
| Artifact bytes created without publication/target observation | artifact_prepared only; released needs a publication receipt, deployed needs a target observation |
| Machine pass with subjective acceptance outstanding | human/mixed acceptance remains pending |

Order attempts/events by declared monotonic sequence/attempt lineage, not wall-clock arrival. Where the seed has no sequencer, serialize writers and record explicit predecessor/attempt links; ambiguity becomes conflict. An accepted no-test exception requires its own authority and rationale. Corrections/invalidation append new evidence; no history rewriting.

## V04 — Relations and test selection

Relation assertions contain endpoints/type, provenance basis, source refs, observed_at, applicable snapshot, and supersedes/invalidates links. Validate endpoint identity/type and direction: verified_by a TestDefinition is a planned verification relation, while a TestRun can support an observed result. A generic source:e2e link is not a passing run.

Cycles in traceability are allowed where meaningful; prerequisite cycles block readiness. Missing relations, stale edges and dynamic black-box dependencies are uncertainty. ChangeSet + acceptance + applicable graph + risk policy select tests; unknown impact falls back to conservative mandatory checks. Record selected and omitted tests with reasons. Periodic full regression detects selection misses; a miss feeds F01 rather than silently patching the graph's history.

## V05 — Context, freshness and resumption

Load the first-read contract and task-relevant objects/relations/evidence only. Reference reusable source snapshots by digest. Summaries/checkpoints are disposable projections, not privileged memory; after resumption recheck input revision, active execution, pending effects and relevant stale sources before action.

Record observed_at separately from source_modified_at. Freshness rules state max age/invalidation conditions and explicit evaluation_time. Missing remote access yields unknown/stale with a reason, not a fresh claim. Conflicting source authorities block dependent claims while unrelated work continues.

Measure context bytes/tokens, files loaded, repeated reads, manual corrections and restore time when proposing optimization. A summary that hides uncertainty or provenance fails even if smaller. Batch repeated observations into the execution's review; retain unique failures and references rather than copying all raw material into every view.
