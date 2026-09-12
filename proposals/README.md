# Upstream feedback intake

This directory is for reviewed candidate packets/abstracted reproductions from seed consumers. It is not part of seed/ and must never be added to the reusable payload allowlist. No candidate has been submitted merely because this intake contract exists.

Before a submission, follow seed/docs/harness/contracts/feedback.md F04–F06: exact destination and export authorization, unique candidate/packet revision, sanitized allowlist, source/base digests and reproducible evidence. Use a candidate-specific branch and a proposal PR, with a stable marker such as `harness-candidate:<id>:<packet-revision>` in the description. Read back remote identity/digest and preserve a local receipt. Do not make duplicate PRs after a timeout.

Maintainer review distinguishes accepting a packet for investigation from changing shipped common contracts. Check generalization scope, decision authority, baseline/candidate eval, counterexamples, privacy, compatibility and rollback. A candidate collected here may remain needs_evidence/rejected/deferred. Accepted seed changes require separate code/contract diff, appropriate scope gates, tests and a new version. Do not mutate released tags or import project state into seed/.

Document release/decision IDs in the proposal lineage so the origin can pull its outcome without sending unapproved messages. This repository supplies no automatic network submitter or merge bot.
