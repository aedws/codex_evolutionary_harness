# Codex Bootstrap Prompt

Read `AGENTS.md` and `docs/harness/README.md` first.

Initialize this project under the Evolutionary Harness **contract seed**. V2/V3/V4 are capability targets, not claims of working automation. Read docs/requirements/HARNESS-GOALS.md and docs/rfcs/RFC-0002-hierarchical-evolutionary-architecture.md for the target architecture. To seed another project, use seed/BOOTSTRAP_PROMPT.md and docs/REUSE.md.

Do not implement product features yet.

Your first task is to:
1. inspect the repository, Git state, tests, docs, data sources, and automation;
2. identify authoritative sources for intent, implementation, runtime data, verification, build, deployment, and human acceptance;
3. reuse existing sources of truth instead of duplicating them;
4. create/update harness records only where necessary;
5. identify the initial project domain and create a project overlay only if Core cannot express a required rule;
6. register unknowns, conflicts, and stale evidence;
7. create the minimum Requirement / Decision / Task / Module / Test / Execution relations needed for the first real task;
8. define the minimum verification contract for that task;
9. update `docs/harness/checkpoint.md`;
10. report the first implementation-ready task.

Constraints:
- no feature implementation in this bootstrap pass;
- no commit/push/merge/deploy unless explicitly authorized;
- do not invent project state;
- do not mark anything verified without version-bound evidence;
- keep project-specific rules at project scope;
- do not promote any rule to Domain/Core without cross-project evidence.

Final report only:
- environment discovered
- authoritative sources
- reusable assets
- harness records created/updated
- conflicts/unknowns
- first implementation-ready task
- required verification
- next allowed action
