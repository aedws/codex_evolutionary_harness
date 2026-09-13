# RFC-0007 — Owner-interviewed document hierarchy and access

Task TASK-20260913-WIKI6-SEED. Scope: project seed maintenance, not automatic universal promotion.

The contract-5 gate checked categories, links and selected tests but did not require a document hierarchy or authenticated access. Newgame's nested navigation and separate authorization worker are the reference. A list of object cards and role reading instructions did not meet that requirement.

## Contract

Contract 6 / bootstrap-wiki-2 adds a project-owned tree and an owner interview. The seed ships **no fixed roles, accounts or grants**. Before activation, interview the owner about roles, read/edit/approve/execute boundaries, authentication and exposure. Keep access pending and block bootstrap completion until an explicit decision is bound to the project policy. This project's owner selected owner-only access, login required; other roles need a later interview.

One tree owns every canonical page: stable ID, title, single parent, page and separate action grants. Reject cycles, missing parents, a flat index, duplicate routes and child permissions broader than the parent. Generate breadcrumbs and direct children from this tree. Render each authorized role's navigation/index using the same policy; omit forbidden titles, paths and relations. New child documents inherit the approved parent policy. Role changes, permission overrides and moves across access boundaries need a new reviewed owner decision.

`wiki_core.py` validates and derives navigation; `wiki_access.py` stores salted password hashes and opaque expiring sessions. A project HTTP adapter checks authentication/role and output integrity for every wiki route, including direct files, search/index/sitemap and unknown paths. Private outputs must never be mounted as unguarded static files. The implemented adapter is read-only: edit/approve/execute grants remain empty and HTTP writes are rejected. A wiki session never authorizes product tools or satisfies human acceptance in the event ledger.

## Completion and failure

bootstrap-wiki-2 requires the tree, owner decision, role outputs, adapter code and negative tests to be content-bound. A current ledger Run must contain the configured access tests and exact policy/adapter/test inputs. A legacy profile cannot claim this readiness. Missing interview, hierarchy or role output yields partial. Unknown role/path and stale policy/session/output fail closed. No password, token or raw credential DB enters the seed, wiki, tests' logs or upstream feedback.

Tests cover parent/child derivation, cycles, unauthorized inheritance, interview drift, forbidden links, unauthenticated direct/index requests, role spoofing, cross-origin writes, session expiry/logout/policy change, login throttling, output drift and preservation. Human readability remains mixed and unaccepted until the owner judges it.

## Ownership, compatibility and recovery

Ship v0.6.0 as a private prerelease. Keep the v0.4.0 event engine and existing install receipt unchanged; use a separate additive adoption receipt, preserving previous bootstrap components and project files before edits. Regenerate role artifacts from the reviewed tree. A partial build does not become current until manifest/integrity checks pass. Account provisioning uses exclusive creation; retries do not replace credentials. Unsupported storage versions are preserved and rejected.

Recover into a separate directory or restore reviewed code/config while preserving newer events and credential state. **Do not restore the old unauthenticated static mount** as a rollback shortcut: stop wiki serving instead. New approvals cannot be inferred from file presence, AI narration or successful login. Local file owners can bypass this application, and authenticated account possession is not proof of a natural person's identity. Remote hosting, HTTPS/SSO/IAM and independent cross-domain evaluation remain separate work.

## Tradeoff

A shared tree/permission contract avoids copying Newgame's product-specific roles and hosting choices. It adds a local authentication adapter and tests, but makes hierarchy and access omissions observable. Compared with contract 5, it meets the owner's requested operating structure more closely; overall context, rule count and intervention savings are not yet measured. No financial analytics work is mixed into this wiki acceptance change.
