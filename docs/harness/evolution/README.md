# Harness Evolution

Local loop: `Execution → Failure/Friction → Classification → HARNESS-REQ → Candidate Change → Sandbox Eval → Promote/Reject`.

Every change declares scope: `execution-local`, `project`, `domain`, `core`.

Upward generalization: Project Lesson → cross-project evidence → Domain Candidate → domain eval; Domain Lesson → cross-domain evidence → Core Candidate → core eval.

Downward rollout: Core/Domain Release → compatibility eval → migration decision → automatic/canary/manual/pinned/blocked → rollback verification.
