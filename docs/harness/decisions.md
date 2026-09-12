# Decisions

Record durable decisions, not transient chat.

Each decision should include: Decision ID, Status, Context, Decision, Alternatives, Authority, Evidence, Supersedes, Effective version.


## DEC-20260913-CLI-001 — Proposed CLI product boundary

- Status: proposed; no human acceptance recorded.
- Context: RFC-0001 reciprocal audit of Evolutionary Harness and Newgame.
- Proposed decision: local single-writer transactional ledger, evidence-derived independent state axes, opt-in project adapters.
- Alternatives: authoritative JSON/JSONL files; remote service ledger; reuse Newgame as-is.
- Authority: project owner; pending review. The author recommendation is not approval.
- Evidence: EVD-20260913-CLI-BASELINE-001, EVD-20260913-CLI-CHECKS-001, EVD-20260913-CLI-ENV-CHECK-001, EVD-20260913-CLI-PROBES-001, EVD-20260913-CLI-REVIEW-001.
- Supersedes: none.
- Effective version: none; proposed in RFC-0001 only.


## DEC-20260913-SEED-001 — Minimal private distribution

- Status: user-authorized scope; specific implementation choices are seed baseline decisions, not acceptance of full runtime design.
- Authority/source: user request to record goals, organize upper architecture and distribute a reusable private GitHub seed.
- Decision: keep the hierarchy as the product architecture; ship a separate clean seed payload and small offline copy/check/pack utility in aedws/codex_evolutionary_harness, private, v0.1.0.
- Alternatives: full CLI runtime now; whole-repository template copy; public package. These exceed scope or carry project history into new projects.
- Evidence: EVD-20260913-SEED-BASELINE, EVD-20260913-SEED-VALIDATION.
- Supersedes: no historical evidence. RFC-0001 remains a subordinate proposal; DEC-20260913-CLI-001 is not adopted as a required DB implementation.
- Effective version: seed contract version 1 / distribution 0.1.0.
