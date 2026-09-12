# Derived State Rules

Do not directly write a state that can be computed from evidence.

Task states may include: `planned`, `implemented_unverified`, `verification_failed`, `verified`, `released`, `blocked`, `stale`.

A task is `verified` only if implementation evidence exists, required tests are known, latest required runs target current code/data version, all required runs pass, and no blocking evidence is stale.

Same evidence + same rule version should produce the same derived state.
