# Minimum contract — version 5

Detailed operational obligations are routed through [contracts/README.md](contracts/README.md): feedback/skills, OOP views/state, execution/policy and overlays/evolution. [coverage.json](contracts/coverage.json) maps G01–G17 to clauses and planned acceptance scenarios. The detailed contracts are mandatory within the authorized task scope; their presence is not a claim that automation is implemented.

## 1. Scope and authority

This is a reusable data and operating contract with a minimal local core in harness.py. The core supplies scoped record validation, a transactional event ledger, configured local test execution and version-bound task-state derivation. Full identity/policy isolation, external effect controllers, promotion and canary are not supplied. Manual workflows remain available with their enforcement limits explicit.

Common core: source authority, identity, evidence/provenance, derivation boundary, policy, eval, promotion and rollback. Domain/project specialization adds rules, tools and evals through overlays without silently editing the common core.

## 2. Human object interface

Requirement, Task, Decision, Module, Test and Release are purpose-oriented views, including a project's whole wiki and its navigation/relationships/workflows. A view exposes purpose, source, responsibility, acceptance, status basis, uncertainty, relations and next allowed action. Explanatory prose and human decisions remain source inputs; state labels come from evidence.

Each state claim identifies subject, target snapshot, evidence refs, rule version, evaluation time and reasons. Checkpoint is the minimal human-readable projection. A copied completion label is not verification.

## 3. Storage and ownership at seed level

| File/record | Role | Writer |
|---|---|---|
| objects.json | Index of intent/object identities and source refs; not trusted status authority | Authorized project execution |
| relations.json | Provenanced relationship assertions | Authorized project execution |
| events.jsonl | Append-only material observations/decisions/action events | Authorized project execution |
| evidence/<execution-id>/ | Version-bound manifests, TestRuns, raw result refs | Test/inspection producer |
| checkpoint.md | Derived current-work summary | Projection author; must cite evidence |
| overlays/project.json | Local sources/rules/tools/evals and restrictions | Project owner/authorized agent |
| releases/current-harness.json | Distribution identity and explicit capability limits | Seed release process |

The manual JSON/JSONL workflow supplies no multi-file atomicity or concurrent writer safety. Use one authorized writer at a time. If interrupted, compare records and source snapshots, retain original bytes, mark partial/unknown and repair with a new execution. Do not silently skip corrupted events or overwrite unrelated changes.

Correction is a new record/event with supersedes or invalidates refs. Raw evidence remains immutable. A broken or stale historical projection stays explainable against its original inputs; it does not need to be rewritten into today's truth.

## 4. IDs, versions and provenance

Use stable unique IDs prefixed by type, e.g. TASK-, EXE-, EVD-, EVT-, REL-, HARNESS-REQ-. New retry attempts have new attempt/execution identity while the same logical side effect retains its operation key. Never reuse a historical ID for another meaning.

Record UTC observation time separately from source modified time. Target identity includes Git commit/tree if present plus relevant dirty/untracked files, data, test definition and environment hashes. A non-Git project uses a path+content manifest. Git SHA alone does not identify dirty inputs.

Relation basis enum: confirmed_by_code, confirmed_by_test, confirmed_by_runtime, confirmed_by_user, inferred_by_static_analysis, inferred_by_llm, unknown. LLM inference cannot become confirmed without independent evidence. Store conflicting assertions and their sources.

## 5. Minimum fields (contract, not executable JSON Schema)

All records declare their format version and IDs. Source/evidence refs must resolve to an actual source or a recorded unavailable/unknown boundary. Meaningful records must not use sample placeholder IDs as real evidence.

| Type | Required information |
|---|---|
| Object | id, type, name, schema_version, source_refs, relation_refs, unknowns; acceptance_class for governed work |
| Execution | execution_id, task_id, mode, actor, input snapshot, start/end, attempted scope, outcome, evidence refs; parent/attempt links when resuming |
| Evidence/TestRun | evidence_id, type, subject, execution_id, target snapshot, created_at, producer, observed result, artifact refs+sha256, limitations; test definition and acceptance contract versions for test runs |
| Event | event_id, event_type, subject, execution_id, target version, timestamp, actor, evidence_refs, metadata; operation key for side effects |
| Relation | relation_id, from, to, type, basis, source_refs, observed_at, applicable snapshot; supersedes/invalidates when necessary |
| Policy | id/version, authority source, actor/capability/target scope, allowed/denied conditions, approval refs, enforcement mechanism, eval refs |
| Eval | id/version, candidate/baseline digests, fixtures/inputs, grader and environment, result/limitations, trust and complexity metrics, raw evidence refs |
| HarnessReq/Change | id, scope, origin, problem/evidence refs, causal hypothesis, assumptions, candidate diff, expected improvement, eval/compatibility/rollback refs, proposal/decision lineage |
| HarnessRelease | immutable version/digest, base/overlay compatibility, declared and verified capabilities, capability evidence, migration/rollback refs |
| Rollout | release/baseline, target cohorts, compatibility refs, canary plan/thresholds, observed metrics, decision authority, adopt/pin/block/rollback evidence |

An Eval should be reproducible independently of the proposing agent's explanation. A passing local eval does not imply domain/core generality.

## 6. Derivation and acceptance

Separate intent/progress/verification/delivery/acceptance/blockers. Treat unknown, unverified, stale, conflicted and blocked as normal. `ready` requires known prerequisites; `verified` requires current implementation evidence, known required tests, matching target versions, passing required runs and no relevant stale/blocking evidence. No known test list is not an empty passing suite.

Same inputs+event watermark+rule version+evaluation time must yield the same state. For manual records, record the derivation rule and evidence explicitly. Runtime-managed tasks use the tested local-verification rule with its narrower declared-input/process scope; this does not validate every future rule. Latest failed/current attempts must not be hidden by older successful runs.

Human-verifiable and mixed acceptance require explicit authorized human judgment for subjective dimensions. Tests cannot certify fun, taste or value by changing the acceptance classification. Artifact production and deployment are distinct; remote deployment needs observed target identity.

## 7. Verifiable black boxes

For a module, tool, agent or provider, record input and preconditions, output and postconditions, state/effect boundaries, timeout/failure classes, observability limits and version-bound tests. You need not understand every internal detail. You must not make stronger claims than the observed contract permits.

## 8. Overlays and evolution

Compose Core → optional Domain → Project by declared compatible versions. Add rules/tools/evals and narrow permissions; conflicting meaning is a conflict, not a last-write-wins override. The core's stability anchors remain intact.

Failure/friction → classified HARNESS-REQ → scoped candidate → sandbox vs baseline → Eval+compatibility+rollback → authorized decision → release. Reduce repeated manual work, false policy blocks, missed tests, stale evidence and redundant context. Simpler rules and smaller context with the same trust count as improvements.

Project→Domain needs evidence from at least two same-domain projects and removal of project-only assumptions. Domain→Core needs multiple domains, removal of domain-specific semantics, core regression, compatibility, rollback and acceptable complexity. Scope labels alone do not grant promotion authority.

Downward release adoption needs pinned versions, compatibility checks and a canary plan with cohort, baseline, period/work count, preset metrics and stop thresholds, responsible authority and rollback target. Insufficient evidence means pinned/blocked, not automatic expansion.

Candidate generation and sandbox evaluation may be delegated to AI within granted scope. High-risk promotion cannot be self-approved. Root authority, destructive/credential scope, evidence/audit/eval weakening, human boundary and rollback removal require explicit human review.

## 9. Side effects, failure and rollback

Record intent before an external effect, stable operation key, normalized request/input digest, target/authority, observed outcome and receipt. Same key+different request is a conflict. Same key+confirmed completed outcome reuses the result. Ambiguous remote success requires state inspection; do not promise exactly-once without supporting mechanism/evidence.

Distinguish bad input, policy block, stale source, integrity failure, unsupported version, environment failure, timeout/effect_unknown, partial commit and rollback failure. Preserve logs and original evidence, choose a bounded retry class and report next allowed action.

Rollback is not deletion of later history. Distinguish projection rebuild, harness version rollback, storage migration recovery and external compensation. Preserve original/new evidence, confirm previous readers are compatible, and verify the restored behavior. If new records cannot be retained by a rollback, block it and plan forward repair.

## 10. Bootstrapping and capability claims

Register the first task only when asked to work on this project. Inspect authority sources and ask concise interviews for missing goals/tests/domain or genuine conflicts. Do not copy the seed author's tasks or authorization.

Distribution 0.4.0 / contract 4 supplies these contracts, a minimal local core, blank configuration examples and empty project records. It does not certify the complete V2 capability level. V2 trust infrastructure, V3 local self-improvement and V4 hierarchical evolution must each earn verified capabilities through recorded eval/runtime evidence. Contract 1 adopters must review the new feedback/skill and operational obligations while preserving their project records and scoped permissions.

Contract 3 strengthens the existing V01/V03/E01/E02/E03/E04/X02 obligations with field-level lineage, whole-wiki journeys, explicit composition operators, independent-context applicability, canary decision rules, principal/gate boundaries and comparable cost accounting. Contract 2 adopters also need reviewed migration. Seven-area review packets and planned cases support that review without pretending an automated engine or successful runtime eval exists.

Contract 4 adds [D01–D08 decision composition](contracts/decision-system.md), the explicit [lifecycle graph](contracts/lifecycle.json), and [local runtime use/limits](runtime/README.md). Runtime-owned task/run observations live in .harness/ledger.sqlite3; legacy/manual records remain separate sources and may link to that evidence without duplicating its state authority. Engine/policy pins and storage versions require reviewed migration; no automatic import of historical approvals or passes.

Contract 5 closes the bootstrap omission path: existing/new wiki inventory and V01/V03 are mandatory before product kickoff. `bootstrap.py` separates installed, bootstrap_partial, wiki_ready and bootstrap_ready. Generic process pass is narrower. See [bootstrap profile](bootstrap/README.md); execution ledger component bytes/version remain 0.4.0.
