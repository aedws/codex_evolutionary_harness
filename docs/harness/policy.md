# Policy

Default allowed: read repo/records and inspect code/config/tests/docs. Within an authorized mutable task, run applicable local/static tests, create local evidence/projections and propose decisions/harness improvements. Query/analysis remain read-only.

Explicit authorization required unless already granted: commit/push/merge, production deploy, destructive external writes, public publishing, paid resources, credential changes, external deletion.

Important policy should move downward when possible:
`Prompt → Tool Capability → Policy Check → Credential Scope → Sandbox/Egress`.

Retry classes: `safe_retry`, `state_check_before_retry`, `human_approval_before_retry`, `not_retryable`.
