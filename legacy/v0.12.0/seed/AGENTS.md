# Evolutionary Harness — project operating contract

Read in order:
1. `docs/harness/README.md`
2. `docs/harness/source-authority.md`
3. `docs/harness/policy.md`
4. `docs/harness/checkpoint.md`
5. `docs/harness/contract.md` and task-relevant files only.

View to OOP, Set up to DOP. Humans use Requirement, Task, Decision, Module, Test, Release. Trust version-bound Evidence, Event, Execution, Relation, Policy and Eval; never narration or an object's status field alone.

Modes: query/analysis inspect without repository mutation; plan may register authorized work but does not implement products; execute changes only the granted scope. Read-only requests do not authorize writes.

For mutable work: establish stable Task ID and new Execution ID, inspect evidence/relations, preserve unrelated files, define machine/human/mixed acceptance, make the scoped change, run sufficient checks, record version-bound evidence, append material events, derive claims and update the checkpoint.

At the end of authorized mutable work, review error fixes, material skill use/failure/addition/change, repeated friction and user corrections under `docs/harness/contracts/feedback.md`. Reuse existing evidence; record a candidate, a linked duplicate, a deferral or a concise no_candidate reason. Query/analysis remain read-only. Consult only relevant clauses through `docs/harness/contracts/README.md`.

Feedback is local by default. `docs/harness/feedback/config.json` separates export/submit/merge/release/adopt authority. Origin information in the seed receipt grants no upstream write permission. Never automatically edit shared seed contracts, global/third-party skills or ship raw project data. A candidate may be submitted before broad generality is proven, but adoption/promotion needs its scoped gates.

Treat unknown, unverified, stale, conflicted and blocked as normal. Test source existence is not a passed TestRun. A release file is not deployment evidence. Human-verifiable acceptance requires an explicit human decision.

Do not expand external permissions. Commit/push/merge, deployment, destructive writes, public publishing, paid resources, credential changes and external deletion require explicit authorization unless already granted for this task. Preserve that authorization across turns. For ambiguous side effects, inspect actual state before retrying; retain one logical operation key.

Do not rewrite/delete historical evidence, weaken audit or eval integrity, change root source authority, remove rollback or reclassify human acceptance automatically. Propose corrections with source refs and supersession instead.

Keep the common core unchanged; specialize through `docs/harness/overlays/project.json` and separately versioned domain overlays. Repeated, structurally generalizable or severe friction may create HARNESS-REQ candidates. Separate proposal, sandbox evaluation and promotion authority. Cross-project/domain evidence is required for upward promotion; compatibility, canary and rollback are required before downward rollout.

Ask a concise interview question when intent, authoritative sources, required tests or conflicting policy cannot be resolved from evidence. Continue independent work while waiting. Do not ask again for an already authorized action.

This seed supplies contracts and a minimal local core; see docs/harness/runtime/README.md when using it. Its policy/input checks govern only its own configured run entry point. Record/full-state/identity/OS/external enforcement beyond that boundary remains unverified. Never use a test-process pass as full product or human acceptance.

Completion report only: changed; verified; unverified/stale; blocked/conflicts; evidence created; events recorded; external actions; harness friction/improvement candidates; next allowed action.

Mandatory bootstrap: apply V01/V03 and `docs/harness/bootstrap/README.md` before selecting product work. Inspect/reuse or create the whole-project wiki first. A fixed `bootstrap.py` gate checks navigation, six object types, relations, sources and role journeys. `harness.py run` passed or installation alone is not `bootstrap_ready`. Missing wiki evidence must remain bootstrap_partial and block bootstrap completion.

Owner interview is mandatory before wiki role/access setup. The seed has no fixed roles or accounts. Confirm project roles, document scope and read/edit/approve/execute boundaries, then bind the approved tree and authenticated adapter under bootstrap-wiki-2. Interview pending or untested access enforcement blocks completion.

Authentication is a project exposure choice, not an unconditional seed requirement. If the owner explicitly selects offline loopback_read_only, omit login/account setup while retaining one local read scope, hierarchy, integrity, negative tests and no remote exposure. Shared/online access needs renewed owner decisions.

Default wiki presentation: read docs/harness/wiki/README.md and use wiki_template.py (newgame-style-wiki-1). New projects must start with overview → nine topics → ordered task details → source/evidence paths. Populate project-owned content, current scope, unknowns, dependencies, deliverables, acceptance and owner decisions; do not copy example/project facts. Register the presentation check alongside bootstrap/access checks. Reuse an existing wiki only with explicit owner-approved parity evidence. Owner interview still governs roles/access; template output is not bootstrap_ready or a status authority.


Automatic object-wiki draft: installation now creates .local/wiki-draft/index.html using wiki_draft.py and project-owned docs/wiki/draft-input.json. Inspect it before the first product task. Six object kinds, purposes, relations, actions and source/lineage views are present with unverified/interview_pending. Populate from actual project sources; the draft is not evidence or bootstrap_ready. Preserve existing wikis, interview owner before role/access setup, and complete the existing project binding/access/Run gates before bootstrap completion. See docs/harness/wiki/README.md.


State-oriented OOP default (state-object-view-1) supersedes the former object-node-map-1 first-screen rule. State nodes group visible Requirement/Task/Decision/Module/Test/Release subjects once per stable ID. Reports/Execution/Evidence/Event/Run are DOP records, not peer business nodes. Open a record through its explicitly linked Task; ambiguous/missing ownership stays unknown. Use wiki_graph.py render_states with reducer results only; never infer state from authored status, names, report counts or graph connectivity. Keep verification, human acceptance and delivery separate. Preserve DOP history/relations under detail access; the old relation renderer is optional lineage tooling only. Quality checks must reject a report-relation map as the default state view.


Mandatory wiki-quality-1 evaluation: read docs/harness/wiki/quality.md. Install/build runs wiki_quality.py structural checks automatically; this is not visual or human acceptance. For the operational project, bind every View to current source hashes, register wiki_quality.py check as a required harness test, and inspect the actual reference plus overview/topic/object at 390 and 1280 CSS px through an available browser tool. Preserve PNG/page/snapshot hashes and observed navigation/readability checks; never invent observations. If unavailable or stale, retain visual pending. Finish through `wiki_quality.py gate` with the project quality contract, visual receipt and bootstrap binding. Its wiki_review_ready still retains human_pending. Old bootstrap.py success alone is insufficient for this new presentation gate. Keep private project screenshots/data local, existing engines/policy pinned, and existing project adoption separate.


Operational Newgame parity profile (operating-workspace-1): after the owner confirms sources, roles, principals and acceptance boundaries, follow docs/harness/workspace/README.md. Use workspace.py to collect approved document/code/data hashes and intent-only objects, then derive business workflow separately from Core verification, human acceptance and delivery. workspace_server.py shares CLI action checks; delivery.py is an explicitly configured, pinned local adapter controller with bounded Canary, rollback and reconciliation. No default accounts, external authority, automatic project adoption or full parity certification. The offline read-only choice remains available through the existing static wiki. Empty state maps, duplicate/missing subjects and wrong workflow membership must fail semantic checks.
