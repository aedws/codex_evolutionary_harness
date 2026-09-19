# Contract routing — version 6

Read only the clauses needed for the task; [coverage.json](coverage.json) maps all 17 goal IDs to these contracts and planned acceptance scenarios.

| Task | Contract |
|---|---|
| Every project bootstrap (mandatory, not relevance-selected) | [V01/V03 views](views-state.md) and [fixed bootstrap gate](../bootstrap/README.md) |
| Error improvement, skill use/change, feedback candidate or upstream submission | [F01–F07 feedback](feedback.md) |
| Object/wiki view, state explanation, graph/test selection, context/resumption | [V01–V05 views and state](views-state.md) |
| Mutation, policy, external effects, evidence integrity or recovery | [X01–X05 execution](execution.md) |
| Overlay changes, eval, promotion, new release, canary or adoption | [E01–E06 evolution](evolution.md) |
| Cross-contract decision semantics and lifecycle dependencies | [D01–D08 decision system](decision-system.md) and [gate graph](lifecycle.json) |
| Runtime setup, commands, storage and enforcement limits | [Local core guide](../runtime/README.md) |
| Architecture assurance review of these seven areas | [Review protocol and planned decision scenarios](review-protocol.md) |

The minimum contract and source-authority/policy anchors still apply. These detailed clauses expand their operational obligations; they do not silently override root authority. The seed includes a minimal local record/test/state core. It does not install a feedback agent/skill, scheduler, network submitter, complete model validator or rollout controller. Perform the procedures within granted scope and explicitly record manual execution until automatic mechanisms have their own evidence.
