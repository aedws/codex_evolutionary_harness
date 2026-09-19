# Seven-area contract review

Use this protocol when reviewing a harness/view/overlay/policy/promotion/rollout change, not on every product task. Load only relevant clauses and review areas. The [blank review packet](../templates/assurance-review.example.json) is a recording shape, not an approval or executable policy. [review-cases.json](review-cases.json) supplies acceptance, rejection and inconclusive scenarios for each area. They are planned scenarios, not observed test results.

1. Freeze review ID, change/input digest, reviewer/principal and relevant areas. Give excluded areas a scoped reason; never silently omit one in a whole-architecture audit.
2. Fill fields with version-bound sources and actual observations. Null means unknown; lists require an explicit population/completeness statement where relevant. `not_applicable` requires a reason and authority, not an empty array.
3. Inspect the allow/reject/inconclusive scenarios against the changed mechanism. Record missing evidence, contrary evidence, findings, next allowed action and actual gate decision for each area.
4. Separate contract_review, implementation_test, runtime_observation and human_acceptance. A documentation review can pass while runtime evidence is missing; it cannot grant promotion, enforcement or rollout capability.
5. Resolve findings in a new version and verify the exact corrected inputs. Retain review attempts and prior rejections. A reviewer must not mark planned fixture descriptions as executed runs.

The seed checker verifies the seven-area packet layout, scenario coverage, clause references and empty/no-authority distribution boundary only. It cannot establish that source facts are true, roles are authenticated, statistical power is adequate or a real runtime gate works. Those require the referenced evaluations and scoped decisions under V03/X02/E02–E04. No background automation is supplied.
