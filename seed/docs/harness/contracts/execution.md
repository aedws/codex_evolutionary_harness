# Execution, policy, evidence and recovery — contract 4

## X01 — Evidence lifecycle and storage ownership

Use globally unambiguous IDs and record schema versions. Bind evidence to code/tree and relevant dirty/untracked/data/config/test/toolchain/skill inputs, not commit alone. Content digests require canonical path/byte manifests; source refs identify who is authoritative and what was observed. Include exit/outcome, start/end, producer, artifacts+hash/size and limits. Corrupted/missing bytes are integrity failures, never skipped to derive a pass.

The manual JSON/JSONL records have no multi-file transaction engine; the optional local core commits its own ledger events transactionally without automatically importing those manual files. A single authorized writer owns a mutation scope; preflight revisions/hashes, write uniquely named evidence first, append material events, then update indexes/projections. An index/projection mismatch is partial/unknown until reconstructed. Do not write computed status into the object index as independent truth. Evidence referenced by events is retained; corrections use supersession/invalidation. Garbage collection and retention weakening are not automatic seed operations.

Filesystem writes require canonical target boundaries and preservation of unrelated/manual content. Symlinks/junctions, case collisions and path escapes are conflicts. Check the current input and ownership immediately before writing. An absent lock/transaction implementation remains an explicit limitation; a Markdown policy cannot provide crash durability.

## X02 — Authority and autonomy

For each action, derive effective permission from actor, authority source, exact capability/target/data scope, payload/base version, active restrictions and expiry/revocation. A skill, overlay or agent statement cannot create authority. Lower scopes may narrow permissions; conflicts do not silently widen them.

| Action | Default seed behavior |
|---|---|
| Query/analysis | Read only; no hidden records, installs, network writes or repair |
| Authorized local task | Scoped edits/tests/evidence and feedback review |
| Local candidate preparation/eval | Within task scope and sandbox limits; no automatic upstream transfer |
| Upstream submission | Separate submit+export authority for exact destination and packet |
| Merge/release/deploy/adopt | Separately applicable authority; submission permission alone is insufficient |
| Root authority, destructive/credential scope, audit/eval weakening, human boundary, rollback removal | Explicit human decision; no self-approval |

Represent permission request, approval, expiration/revocation and enforcement observations separately. Existing authorization is reused within scope; unknown scope triggers a targeted interview. Report the exact conflicting instruction/source rather than inventing policy barriers. No credentials are stored in packets or copied from upstream. No background scheduler or unpaid/paid runner is assumed; budgets and execution host are explicit before autonomous jobs.

Important controls should move to tool capability checks, policy gates, scoped credentials and sandbox/egress boundaries. For each claimed control, record whether it is documented_only, configured, tested or runtime_observed. The local core enforces pinned command/policy/input checks within its own run command. OS sandboxing, principal separation, protected autonomous promotion and external-effect enforcement remain documented_only.

Bind proposer, evaluator, approver and effect executor to authenticated principal IDs and explicit capability grants, not role names alone. The proposer writes candidate code and proposed eval inputs; the evaluator reads a frozen candidate and writes evidence without changing candidate/grader/acceptance; the approver issues a decision for the exact diff/eval/target; the executor performs only that decision's scoped action. Record principal overlap and conflicts of interest. Renaming the same agent/session is not independence. High-risk self-approval is forbidden; human approval must come from an authorized human. Low-risk combined roles require an existing explicit policy and disclose the lack of independent evaluation.

For each protected operation retain an enforcement map: principal/capability/target, policy and approval digests, actual gate/adapter location, credential boundary (identifier only), pre-dispatch check, denial and revocation evidence, and bypass-test refs. Recheck exact payload/base, expiry/revocation and target revision at dispatch. Test direct API/CLI/tool invocation, replayed/stale approval, changed payload, wrong role/target, missing policy service and disallowed egress; UI refusal alone is insufficient. The proposer must not alter these gates, protected evals or audit storage as part of its candidate.

Without observed enforcement, protected autonomous execution is blocked and marked documented_only. An already-authorized human-supervised manual path may proceed within its scope, with that limitation recorded; it must not be labeled runtime-enforced. Do not ask again merely because an existing applicable authorization is recorded outside a particular template. Unknown or conflicting authority requires a targeted interview, not invented grants or silent escalation.

## X03 — Verifiable module/tool/skill black boxes

Declare versioned input/output schemas, preconditions/postconditions, state transitions, effect targets, dependency/capability requirements, time/resource budget, failure modes, idempotency/recovery method and observable evidence. Include negative/invalid-input and dependency-unavailable cases. Interior implementation details are optional; observed boundaries and limitations are mandatory.

Replacing a tool/skill/provider must recheck these contracts against its new digest/environment. A narration of successful tool use is not a result. Sandbox runs must not gain production credentials or use uncontrolled external mutation just because the candidate proposes it.

## X04 — Operation identity and failure outcomes

Task ID is stable work; Execution and attempt IDs represent actual runs; operation ID/key represents one logical side effect. Store normalized request digest, normalization version, authority, destination, input/expected target revision, phase and receipt. Same key+same completed request replays the observed result; same key+different bytes conflicts. Local and upstream retries retain the logical key.

Before dispatch, persist intent. After dispatch, persist observations and readback. A timeout/cancellation after remote success is effect_unknown until target inspection confirms outcome. Provider idempotency/CAS and readback must be proven before claiming duplicate-effect protection. If no reliable observation exists, block retry and preserve the unknown instead of promising exactly-once.

| Failure | Preserve / next allowed step |
|---|---|
| Invalid schema/input/unsafe path | Reject before effect; corrected request |
| Stale version/revision or owner conflict | Preserve current files; new plan after comparison |
| Missing test/tool/environment | environment_failure; explicit setup or defer, not assertion failure |
| Evidence corruption/unknown required event | integrity/conflict; preserve original bytes and block dependent claims |
| Lock contention/partial local write | Inspect owner/receipt; no lock stealing by age or blind replay |
| Timeout/429/5xx/disconnected auth | Distinguish not_found from unobservable; bounded state-check-before-retry |
| Effect confirmed, projection failed | Record effect and projection_pending; rebuild view without repeating effect |
| Rollback failure | rollback_pending/unknown; stop dependent activation and inspect actual state |

Retry classes are safe_retry, state_check_before_retry, human_approval_before_retry and not_retryable. Fix attempts/deadline/backoff bounds in the action contract. Budget exhaustion is deferred/blocked, not success. Return performed/unperformed scopes, evidence refs, error class and next action without leaking secrets.

## X05 — Recovery and auditability

Distinguish projection rebuild, incomplete execution recovery, harness/code rollback, storage migration and external compensation. Plan from/to identities, expected revision, snapshot manifest, subsequent records to preserve, authority, checks and a failure path. Test restore in isolation before claiming recoverability. A retained backup name is not a restore test.

An older runtime must read current schemas/events before code rollback. After new events exist, old-snapshot overwrite is forbidden unless a tested transformation preserves those events and refs. Otherwise pin/block and plan forward repair. No raw Git reset, mass deletion, event truncation or credential rollback is automatically authorized.

Append attempted, observed, verified/failed recovery events with new execution identity. Verify restored artifact/data/runtime identity and required behavior; keep original failure and compensation evidence. Human decisions and source authorities remain separately traceable through rollback.
