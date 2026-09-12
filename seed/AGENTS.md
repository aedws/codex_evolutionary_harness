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

Treat unknown, unverified, stale, conflicted and blocked as normal. Test source existence is not a passed TestRun. A release file is not deployment evidence. Human-verifiable acceptance requires an explicit human decision.

Do not expand external permissions. Commit/push/merge, deployment, destructive writes, public publishing, paid resources, credential changes and external deletion require explicit authorization unless already granted for this task. Preserve that authorization across turns. For ambiguous side effects, inspect actual state before retrying; retain one logical operation key.

Do not rewrite/delete historical evidence, weaken audit or eval integrity, change root source authority, remove rollback or reclassify human acceptance automatically. Propose corrections with source refs and supersession instead.

Keep the common core unchanged; specialize through `docs/harness/overlays/project.json` and separately versioned domain overlays. Repeated, structurally generalizable or severe friction may create HARNESS-REQ candidates. Separate proposal, sandbox evaluation and promotion authority. Cross-project/domain evidence is required for upward promotion; compatibility, canary and rollback are required before downward rollout.

Ask a concise interview question when intent, authoritative sources, required tests or conflicting policy cannot be resolved from evidence. Continue independent work while waiting. Do not ask again for an already authorized action.

This seed supplies contracts, not an automatic policy or state engine. Report enforcement as unverified until actual execution-layer controls are tested.

Completion report only: changed; verified; unverified/stale; blocked/conflicts; evidence created; events recorded; external actions; harness friction/improvement candidates; next allowed action.
