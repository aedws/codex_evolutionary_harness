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

## DEC-20260913-FEEDBACK-001 — Complete contracts before runtime automation

- Status: authorized seed maintenance; subjective design acceptance and empirical generality unverified.
- Context/authority: user requested completion of self-feedback common contracts and missing upper-design contracts; prior private distribution scope persists.
- Decision: release contract 2 / distribution 0.2.0 with bounded feedback review, skill provenance/ownership, local-only upstream defaults, operational state/policy/recovery/evolution clauses and 17-goal traceability. Keep controllers unimplemented and runtime capability lists empty.
- Alternatives: principles only; immediate automatic submission/promotion. RFC-0003 compares costs and goal fit; no benchmark superiority claimed.
- Evidence: EVD-20260913-FEEDBACK-BASELINE; local validation and remote publication evidence are recorded separately when observed.
- Scope: project seed-maintenance baseline; no cross-domain-proven promotion and no root authority/stability-anchor weakening.
- Supersedes: contract-1 distribution default for new users only. Old tags, evidence and installed projects remain intact.

## DEC-20260913-ASSURANCE-001 — Seven-area contract assurance

- Status: user-authorized seed maintenance; runtime and human design acceptance unverified.
- Authority: user's explicit seven-area audit and seed improvement request; prior private distribution authorization persists.
- Decision: strengthen V01/V03/E01/E02/E03/E04/X02 and ship contract 3 / v0.3.0 with blank review packet and planned cases. Existing contract 1/2 users review migration; no automatic adoption or permissions transfer.
- Evidence: EVD-20260913-ASSURANCE-NEWGAME; EVD-20260913-ASSURANCE-VALIDATION; RFC-0004.
- Alternatives: retain coarse goal-to-clause mapping; implement full runtime now. The former misses concrete decision rules, the latter exceeds current seed scope.
- Cost observation: clause IDs remain 23; shipped Markdown grows from 52,314 to 66,763 bytes. Relevant-area reading limits intended context load, but actual context/time savings are unmeasured. No optimization superiority or same-trust operating result claimed.
- Effective scope: seven-area contract documentation and structural distribution checks only. Existing evidence, tag identities and stability anchors are preserved.

## DEC-20260913-DECISION-001 — End-to-end contracts and minimum local core

- Authority: EVD-20260913-DECISION-AUTHORIZATION; explicit user implementation/validation reply; prior private distribution scope persists.
- Decision: ship v0.4.0 / contract 4 with strict local records, SQLite events, configured test dispatch, version-bound status/Task View, local candidates and isolated ledger restore. Add D01–D08 and 16 lifecycle gates.
- Evidence: EVD-20260913-DECISION-VALIDATION, 59 local unit/integration tests, including installed-seed CLI and real concurrent dispatch rejection.
- Scope: project seed-maintenance. This does not authenticate human roles, sandbox child processes, promote itself or establish full V2/V3/V4 outcomes. Human acceptance remains separate.
- Alternatives/tradeoffs: RFC-0005 section 6. Better fit for reproducible CLI decisions than document-only seed; increased code and operating setup. Net context/time/trust optimization remains unmeasured.
- Recovery: preserve older tags and manual history; new runtime has its own explicit initialization; policy/engine migration is not automatic; restore never overwrites later active events or transfers authority to a new workspace.

## Prevention gate decision

RFC-0006 and EVD-20260913-PREVENTION-VALIDATION support contract 5. Scope: project seed maintenance. Keep engine/policy pins unchanged and adopt the extra component through a separate receipt. A structural gate improves omission detection; semantic quality and net effort savings remain unmeasured. Preserve previous releases for recovery.
