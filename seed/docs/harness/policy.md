# Policy boundary

Default: read local sources, inspect records, run authorized local/static checks, create local records for authorized mutable work, propose improvements. Query/analysis requests remain read-only.

Explicit authorization unless already granted: commit/push/merge, production deploy, destructive writes, public publishing, paid resources, credential changes and external deletion. A seed install or bootstrap is not blanket authorization for these actions.

Prefer tested Tool Capability → Policy Check → Credential Scope → Sandbox/Egress enforcement. This document does not itself provide that enforcement.

Retries: safe_retry; state_check_before_retry; human_approval_before_retry; not_retryable. Timeouts do not prove that a remote operation had no effect. Preserve the same operation key and inspect the target before retrying ambiguous effects.

Never automatically change root source authority, expand destructive/credential scope, weaken audit/evidence/eval retention, remove rollback or convert human-verifiable acceptance to machine truth.
