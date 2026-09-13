# Mandatory bootstrap profile — contract 5

Bootstrap always reads V01/V03 and this profile before selecting the first product task. Inspect/reuse an existing wiki; otherwise create a Markdown or HTML navigation surface first. A wiki server is optional. Preserve existing source authority and manual content.

Required categories: onboarding, product, design_data, architecture_modules, tools_workflows, verification_troubleshooting, decisions, release_history, role_workspaces. Required object types: requirement, task, decision, module, test, release. Unimplemented modules/releases have explicit unknown/unverified explanations rather than fabricated passes.

Bind an existing project's views to the exact schema implemented by `bootstrap.py`: schema_version=1, profile=bootstrap-wiki-1, entrypoint, documents, categories, object_views, relations, journeys, input_sha256, validation_task. Every source/view path is project-relative and content-hashed. Views expose ID, purpose, source_refs, next_action, rule, acceptance_class and unknowns. Relations resolve endpoints/provenance. Owner/developer/reviewer journeys each traverse at least three linked documents. This binding is a derived index of existing sources, not a second authoritative status store.

Commands from project root:

```powershell
python bootstrap.py --binding .local/bootstrap-binding.json --artifacts-only
python bootstrap.py --binding .local/bootstrap-binding.json
```

No binding is bootstrap_partial. Missing categories/views, orphan/broken navigation, stale bytes, unresolved sources, invalid types or a validation task without a current observed pass return exit 6. No custom list can remove the built-in mandatory categories/types. Artifacts-only can produce wiki_ready, never bootstrap_ready. Final check also queries the actual pinned local ledger task and preserves human_pending. Generic harness.py run passed means only the selected checks passed; it cannot substitute for this gate. Installation receipt means installed, not bootstrap_ready. Product readiness remains separate.

The gate proves structural completeness, integrity and local test applicability. It does not authenticate humans, evaluate writing quality, protect arbitrary OS tools or prove all project requirements. Subjective wiki usability is mixed/human-verifiable. Markdown and an existing renderer are equally allowed.

Include the artifact-only check in the project's mandatory check command. Generate view/binding snapshots outside the test run and exclude self-referential generated state from that run's target list. After the run and event/projection updates, regenerate the wiki/binding and perform the final bootstrap check. A failed final check blocks the bootstrap completion report and dependent product kickoff. Preserve partial state with reasons; do not call it complete merely because API tests passed.

Migration from v0.4.0: the ledger engine harness.py is byte-identical and retains component version 0.4.0. Add bootstrap.py and reviewed project binding/check integration without repinning engine or rewriting the existing ledger. Preserve the old install receipt and append an adoption receipt naming added files/version/hash and compatibility evidence. Existing projects keep their manuals, wiki, authorization and historical runs. Roll back the added integration using the recorded pre-change snapshot; preserve all new evidence and never overwrite later project work.
