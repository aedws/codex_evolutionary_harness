# Mandatory bootstrap profile — contract 6

Bootstrap always reads V01/V03 and this profile before selecting the first product task. Inspect/reuse an existing wiki; otherwise create a Markdown or HTML navigation surface first. A wiki server is optional. Preserve existing source authority and manual content.

Required categories: onboarding, product, design_data, architecture_modules, tools_workflows, verification_troubleshooting, decisions, release_history, role_workspaces. Required object types: requirement, task, decision, module, test, release. Unimplemented modules/releases have explicit unknown/unverified explanations rather than fabricated passes.

First interview the project owner: who needs access, which documents/actions each role may access, authentication method and exposure. Never install default owner/planner/developer/reviewer accounts or infer grants from role labels. Until confirmed, record interview_pending and block bootstrap completion. A single owner-only role is valid when explicitly selected; other roles require another interview.

Bind an existing project's views to the exact schema implemented by `bootstrap.py`: schema_version=1, profile=bootstrap-wiki-2, entrypoint, documents, categories, object_views, relations, journeys, input_sha256, validation_task, wiki_contract. Every source/view path is project-relative and content-hashed. Each confirmed project role needs a journey traversing at least three linked documents. This binding is derived and is not a second authoritative state store.

wiki_contract points to a project-owned JSON validated by wiki_core.py: schema_version=1, profile=wiki-tree-access-1, interview {status, decision_ref, policy_digest}, roles {project_role: label}, access {root_read, overrides}, nodes [{id,title,parent,page,grants:{read,edit,approve,execute}}], root, adapter {kind,source_paths,test_paths,required_tests}. Implemented adapter kinds are authenticated_read_only and explicitly owner-selected loopback_read_only; edit/approve/execute grants must remain empty. Owner interview establishes roles and inheritance policy; new children inherit it. Role/override changes and cross-boundary moves need renewed owner review, not a silently recomputed approval digest.

Use one tree for large document → topic → detail, breadcrumbs, child lists and role-filtered indexes. Canonical document filenames match tree pages. Role artifacts live at docs/wiki/roles/<role>/<page>. Every role artifact is hash-bound and contains wiki_core.navigation output. Route all HTTP access through the selected access adapter and the same policy; never expose raw role directories or legacy static output mounts. Include direct URLs, forbidden role/unknown paths and metadata/search/sitemap in negative tests. The seed ships reusable tree and local account/session components; the project supplies and tests its HTTP adapter. Account possession is not independent human identity or approval evidence.

Commands from project root:

```powershell
python bootstrap.py --binding .local/bootstrap-binding.json --artifacts-only
python bootstrap.py --binding .local/bootstrap-binding.json
```

No binding is bootstrap_partial. Missing categories/views, orphan/broken navigation, stale bytes, unresolved sources, invalid types or a validation task without a current observed pass return exit 6. No custom list can remove the built-in mandatory categories/types. Artifacts-only can produce wiki_ready, never bootstrap_ready. Final check also queries the actual pinned local ledger task and preserves human_pending. Generic harness.py run passed means only the selected checks passed; it cannot substitute for this gate. Installation receipt means installed, not bootstrap_ready. Product readiness remains separate.

The gate proves structural completeness, integrity and local test applicability. Access adapter sources, owner decision, tree and negative tests must also match the current Run, including its required test IDs. A structural pass is not production security certification, human approval, writing quality or OS isolation. Subjective wiki usability remains mixed/human-verifiable. Existing renderers can adapt to this contract.

Include the artifact-only check in the project's mandatory check command. Generate view/binding snapshots outside the test run and exclude self-referential generated state from that run's target list. After the run and event/projection updates, regenerate the wiki/binding and perform the final bootstrap check. A failed final check blocks the bootstrap completion report and dependent product kickoff. Preserve partial state with reasons; do not call it complete merely because API tests passed.

Migration from v0.4.0: the ledger engine harness.py is byte-identical and retains component version 0.4.0. Add bootstrap.py and reviewed project binding/check integration without repinning engine or rewriting the existing ledger. Preserve the old install receipt and append an adoption receipt naming added files/version/hash and compatibility evidence. Existing projects keep their manuals, wiki, authorization and historical runs. Roll back the added integration using the recorded pre-change snapshot; preserve all new evidence and never overwrite later project work.

For an offline single-workspace project the owner may explicitly choose loopback_read_only, with no login/account dependency. Exactly one local read scope is allowed; it is not authenticated identity separation. Test literal loopback/Host enforcement, write denial, direct-file protection and no credential reads. Online/shared access requires a new owner decision and appropriate authentication; offline must not silently become public.
