# Policy

Default allowed: read repo/records, inspect code/config/tests/docs, run local/static tests, create local evidence/projections, propose decisions and harness improvements.

Explicit authorization required unless already granted: commit/push/merge, production deploy, destructive external writes, public publishing, paid resources, credential changes, external deletion.

Important policy should move downward when possible:
`Prompt → Tool Capability → Policy Check → Credential Scope → Sandbox/Egress`.

Retry classes: `safe_retry`, `state_check_before_retry`, `human_approval_before_retry`, `not_retryable`.
