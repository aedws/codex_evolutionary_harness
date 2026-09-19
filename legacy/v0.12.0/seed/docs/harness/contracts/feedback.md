# Feedback and skill lifecycle — contract 6

## F01 — Trigger and bounded review

On authorized mutable tasks, inspect improvement opportunities after a verified error fix, repeated retry/manual workaround, user correction, skill selection failure, skill addition/update/removal, and before task completion. Successful skill use is an observation, not automatically a candidate. Query/analysis remain read-only: report an opportunity without creating records.

Review once at the task boundary unless a severe integrity/permission failure requires immediate attention. Reuse the evidence already collected; do not reload every skill/document or run the whole eval suite for every call. Record `no_candidate` with a reason in the execution summary when nothing generalizes. Do not create a redundant requirement per ordinary successful use. Review budgets and deferrals belong to the project overlay; an exhausted budget cannot certify success.

## F02 — Observe and classify

Record the project/execution, installed seed contract and manifest digest, input/code/data/tool versions, observed failure or friction, raw evidence refs, fix and verification result, causal hypothesis, assumptions and unresolved uncertainty.

Classify as product_bug, project_overlay, skill_specific, domain_contract, core_contract, environment_failure or unknown. A product bug stays in the product unless it exposes a reproducible shared-contract defect. Removing project-specific names is not enough to demonstrate generality. Candidate creation requires recurrence, structural generalizability or high severity with evidence; otherwise retain an observation/deferred assessment.

## F03 — Skill provenance, ownership and effects

Track relevant used/added/updated/removed skills with `skill_id, source_kind, source_ref, owner, version_or_content_digest, invocation_reason, execution_id, observed_result, evidence_refs, limitations`. Distinguish available, selected, instructions_read, execution_observed and result_verified. A skill listed in context was not necessarily used; reading SKILL.md alone does not prove its workflow ran. Missing telemetry is unknown, never invented execution.

Hash SKILL.md and any actually used scripts/references/assets as a bundle manifest. Local path alone is not identity. Preserve before/after digests for changes. Adding a skill requires matching-scope and nonmatching-scope trigger cases, representative outcome checks, dependency/permission review and conflicts with existing instructions. Removing a skill requires dependent workflow checks and a rollback reference. Provider/model/environment changes are recorded when relevant to reproducibility.

Project-owned skills may be edited within granted scope. User-global, system and third-party/plugin-managed skills are separate owners: prefer a project adapter/overlay or upstream proposal; never silently rewrite caches or global instructions. Do not automatically bundle external skill text, credentials or tool accounts into the seed. A skill cannot grant itself permissions, alter acceptance authority or override explicit user instructions. If existing authorization covers a needed action, reuse it; interview only missing/conflicting authority.

The duty to review belongs in AGENTS and execution completion, with an optional skill supplying the method. Skill invocation alone is not a guaranteed hook. This seed adds no skill-run telemetry collector or global skill installation.

## F04 — Candidate packet and deduplication

Use `templates/feedback-candidate.example.json` as a draft shape, not evidence. Required packet information is candidate/schema ID, origin project/executions, seed base digest/version, classification and proposed scope, observation/evidence/skill refs, hypothesis and counterexamples, project assumptions to remove, normalized change summary/digest, baseline/candidate evals, complexity budget, compatibility and rollback plans, sharing manifest and submission receipts.

Assign a stable candidate ID. Compute a fingerprint from normalized contract clause IDs, causal failure class, trigger shape and target scope; store normalization version and canonical input digest. The fingerprint groups related reports, while each observation keeps its project/base-version identity. New evidence extends a candidate by append/supersession; it is not silently overwritten. Same fingerprint with conflicting root causes is linked for review rather than merged blindly. Same submission operation key plus different packet bytes is a conflict.

Candidate phase is derived from supporting records: observed → classified → candidate → locally_evaluated → submission_ready → submitted → under_review → accepted_for_scope/rejected/deferred → released. `duplicate`, `needs_evidence`, `conflicted`, `withdrawn`, `submission_unknown` can interrupt the flow. Only a scoped authorized decision supports accepted_for_scope; only release evidence supports released. Submission and discussion do not imply acceptance.

## F05 — Local evaluation and sharing boundary

Compare the frozen baseline and candidate on the same declared task/eval inputs. Include the original failure, a unaffected regression case, a counterexample/non-trigger case, stale/conflicting evidence and applicable failure/rollback cases. A local pass permits a local proposal; it does not prove domain/core generality. Follow E02 for independent evaluation and non-regression.

Build a minimum export bundle containing an abstracted problem, sanitized reproducible fixtures, specific proposed contract diff, evidence digests/results and explicit limitations. Keep raw source, private requirements, user decisions, credential values and unrelated project data local unless separately authorized. A private upstream repository is not automatic authorization to transfer another project's information. Export approval is bound to the exact file allowlist/digest, destination and authority ref. Hashes establish byte identity, not confidentiality or truth. Sensitive hashes/paths may also need abstraction.

If evidence cannot be shared, publish only an authorized abstraction and mark reproduction restricted/needs_evidence. Never fabricate a public fixture or independent confirmation. Stop when authorization or source rights conflict; retain local work and ask only about that boundary.

## F06 — Upstream transport and authorization

`feedback/config.json` defaults to local-only with no external authorization. Obtain source repository/version from `.harness-seed.json` as provenance; it does not grant upstream write access. Set an exact authorized repository, submission base, allowed paths, export scope and authority refs before sending a packet. Permission to submit, merge, release and adopt are distinct. Do not copy this seed author's account credentials or standing permissions into downstream projects.

Submission procedure: verify remote identity/visibility and authorized base → freeze packet/export digest → record pending operation → search existing candidate marker/receipt → create or reuse one candidate PR/record → read back its ID, URL, base and packet digest → append submission receipt. External creation needs existing authorization. No automatic issue/comment/PR messages are sent by these documents.

On timeout, check the remote marker and content before retrying. If it exists with the same digest, reuse it; if different, conflict; if unobservable, retain submission_unknown and do not duplicate. Deduplication key is `(destination, candidate_id, packet_revision)` with payload digest. Remote base drift requires rebase and rerun of affected evals; an old pass is not carried forward silently. Deleted/closed submissions remain in lineage.

## F07 — Reflect into the seed and close the loop

Upstream candidates can be collected before cross-project proof exists. Collection under proposals/ is distinct from changing shipped seed/ contracts. A maintainer reviews generality, tests, ownership, privacy, stability anchors and scope under E03. Accepted feedback updates only the appropriate project/domain/core contract or optional skill reference. It must not ship origin-project records with the reusable payload.

Version the contract change and seed manifest, run distribution/contract checks and compatibility fixtures, publish a new immutable tag/assets, then append a release receipt linking candidate→decision→eval→release digest. Return the outcome to the origin by authorized transport or a pull-only status check. Rejection/defer/withdrawal reasons and supersession remain visible.

Origins stay pinned until E04–E05 adoption. The originating project verifies whether the adopted change actually reduced the observed failure/cost; failed follow-up creates linked evidence and can trigger rollback or a new candidate. Closing a PR is not proof that the problem was fixed. This completes Project → upstream evaluation → release → Project observation without requiring automatic promotion.
