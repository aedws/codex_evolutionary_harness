# End-to-end decision system

This contract connects the obligations in V01–V05, X01–X05, F01–F07 and E01–E06. Its presence alone does not provide an engine. It does not replace source authority or grant capabilities.

## D01 — Typed inputs and trust resolution

A decision request pins profile/schema/rule versions, operation kind, subject, source/acceptance/test/relationship/effective-overlay digests, event watermark and explicit evaluation time. The profile defines required records/gates and permitted extensions. The caller cannot make a missing gate optional by deleting it from the request.

Validate exact scalar/container types; booleans are not integers, non-finite numbers are invalid, digests have a declared algorithm/encoding, timestamps carry timezone, and durations/counts have units and bounds. Duplicate IDs/JSON keys, unknown required semantics, unresolved references and unsupported versions are rejected before effects. Empty known populations and unknown populations are different. An empty required-test/eval/cohort set cannot pass by vacuous truth.

Every supporting record carries producer/source, subject, applicable target and observation limits. Resolve raw content integrity separately from source authenticity and authorization. A user-entered `passed`, `approved`, `human`, `runtime_observed` or `independent` field is an assertion until an applicable trusted source supports it. A local file owner can alter files; checksums are not a credential or tamper-proof history. Record the actual threat and enforcement boundary.

## D02 — Eligibility, axes and precedence

Keep verification, acceptance, readiness, delivery and recovery axes separate. Return the complete deterministic reason set, missing/rejected evidence, profile/input digests and next allowed action. A useful primary status may summarize the reasons but must not erase failed, stale or unknown axes.

For a governed action, invalid/unsupported input prevents evaluation; an integrity or same-authority contradiction produces conflict; explicit policy denial prevents dispatch; known failed required gates prevent eligibility; missing required observations produce unknown/inconclusive; obsolete-only evidence produces stale. Eligibility requires every mandatory gate satisfied for the exact inputs and authority. Preserve all applicable reasons even when one dominates the action decision. Unknown optional metadata grants no capability.

`eligible` is permission to attempt the specified next transition within its scope, not proof of execution, acceptance, release or adoption. Only a subsequent observation supports those facts. The same immutable inputs/time/profile produce the same canonical decision. Late evidence or changed evaluation time is a new input, not retroactive rewriting.

## D03 — Temporal and reference semantics

Test/implementation/acceptance/authority evidence must match the exact governed subject, relevant target, requirement/test definition, selection contract and attempt lineage. A result for another task or an older data/acceptance version cannot satisfy the current gate. Evidence that postdates the decision's watermark/evaluation time is inapplicable to that historical decision.

Resolve revocation, invalidation and supersession from applicable source records. Preserve rejected/invalidated records in history with reasons. Supersession cannot erase a failing observation or change its identity; the new assertion's authority and applicability are checked independently. The latest selected attempt's start prevents reuse of an earlier pass until its own result is known. Conflicting terminal results for one attempt require reconciliation, not last-write-wins.

## D04 — Authority inheritance and action boundary

Authority grants come from the authoritative actor/capability store or an explicit scoped human decision, not from overlay definitions. An omitted restriction means inherit the already-established grant; an explicit deny_all narrows it to none; an unconfigured required authority binding is unknown and blocks dependent effects. Lower layers never create a grant. Restrictions intersect applicable granted scope, denies accumulate, and higher stability anchors remain intact.

An eligible decision binds actor, action, exact target/payload/base revision, expiry and logical operation key. The executor rechecks them immediately before dispatch. A read-only evaluator cannot claim that other tools honor its decision. Only an executor/credential boundary demonstrated to mediate an effect may claim that scoped enforcement. Authentication adapters and human decision capture must expose their limitations; naming a principal is not authenticating it.

## D05 — Lifecycle gates and completion scope

Use an explicit dependency graph from seed integrity → project bindings → scoped task readiness → version-bound execution/verification → applicable human acceptance. Feedback extends it through observation/classification → candidate → frozen evaluation → scoped promotion decision → immutable release → compatibility/recovery → canary/adoption → origin follow-up. Failures, deferrals, conflicts, withdrawal and rollback retain their own records and next actions.

Each gate identifies owner, required inputs, evaluator/profile, outputs, denial/unknown handling and downstream consumers. Dependencies may be satisfied by authorized manual observations when the profile allows them; label this mode. A gate demanding runtime enforcement cannot accept a documentation review in its place. A stage's result does not bypass another stage's separate grant or evidence requirement.

The final goal requires demonstrated V2 mechanisms, V3 within-project improvement and V4 independent cross-project/domain promotion and safe return propagation. Do not use a percentage of populated fields/objects or one aggregate pass as completion. Source adapters, applicable evaluations, authorized actors and recovery must all exist for the claimed scope. A system may support future reachability while its actual goal outcome remains unverified.

## D06 — Adapter conformance and black-box limits

Declare adapters by purpose: authoritative source observation, command/test execution, human decision/identity, external effect/readback, and projection rendering. Each pins its version, input/output contract, target scope, permitted capabilities, timeout/retry, raw evidence and uncertainty behavior. Bind through project/domain configuration; never assume a particular game engine, repository host, planner or cloud service.

Adapters must distinguish not_found from denied/unavailable, observation from source modification time, known failure from tool/environment failure, and confirmed effect from effect_unknown. Require invalid-input, stale revision, permission denial, interruption and recovery cases for the claimed boundary. Networkless synthetic fixtures demonstrate protocol behavior only; they are not operating provider or domain evidence.

## D07 — Evaluation integrity and contract evolution

Freeze evaluator, expected outcomes, trust gates, cost objectives and required populations before collecting results. Preserve all attempts and uncertainty. Changes to acceptance, schema semantics or mandatory gates require a new compatible profile/contract version and reevaluation; do not edit the baseline comparison into success.

Keep record schema, storage, command protocol, derivation rule, contract and distribution versions separate. Queries do not migrate. An old reader encountering required new events must fail closed rather than skip them. Migration records inventory ownership/references/counts, preserved assertions, unconvertible fields and rollback/readback proof. Adopt a new runtime only after compatibility and recovery evidence; an install receipt cannot substitute for this.

## D08 — Bounded operation and feedback liveness

Fix time/work/context/effect budgets and retry classes before autonomous activity. Missing budget is unconfigured, never unlimited. On exhaustion retain observations, report deferred/unknown and stop dependent effects. Keep unrelated authorized work possible when a local gate is blocked.

Feedback about the feedback process is collected once per execution boundary and linked to an existing candidate when applicable. Do not recursively create reviews/evals forever to certify a review. A finite plan may defer broader proof to later executions; deferral cannot be relabeled success. Human decisions and unavailable external evidence remain legitimate boundaries, not reasons to weaken gates.
