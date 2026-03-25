# Current Gate Pack (Derived View)

**Derived view / anti-drift notice:** canonical docs outrank this pack.

- generated_at: `2026-03-25T09:09:39`
- source_digest: `f823dfe04d52a34440fbca032ae9780f2cf80ce7a565df67a115b7615faef90e`
- active_gate_id: `S1`
- active_gate_label: `S1 — Talk2DINO faithful reproduction`
- active_gate_file: `docs/mainline/gates/scientific/S1.md`
- active_gate_version: `v1`
- pack_quality: `full`

## 1. Purpose

Establish a faithful, reviewable Stage-1 Talk2DINO reproduction path that yields a reusable object projector Φ_o and a trusted benchmark/evaluation route for later WSOVPS stages.

## 2. Claim / Control Goal

### Scientific claim
A Talk2DINO-faithful text-to-DINO object grounding path can be reproduced in this repository closely enough to serve as the Stage-1 semantic object grounding module for WSOVPS.

### Engineering support goal
S1 depends on E0 and E1 to guarantee that environment, paths, weights, and feature artifacts are valid before scientific judgment.

## 4. Smoke Standard

A smoke result may count only as smoke when all of the following hold:
- the faithful Stage-1 entrypoints are bound and documented;
- the declared datasets / weights / feature sources can be opened or their exact absence is diagnosed;
- one bounded train/eval wiring check runs far enough to prove the path is real;
- the evaluator can emit at least one protocol-matched metric artifact or a precise blocker report;
- any checkpoint-loading pathology (for example, gross missing-key behavior) is explicitly explained.

Smoke evidence may support repairs and wait-state setup, but it does not count as formal PASS.

## 5. Formal Standard

Formal S1 acceptance requires all of the following:
- the faithful Stage-1 protocol is documented and bound to concrete entrypoints, configs, and paths;
- benchmark evaluation is executed on the declared object-level OVS validation set, centered on Pascal VOC 20, Pascal Context 59, and COCO Object;
- no critical integrity bug remains in dataset selection, metric aggregation, checkpoint loading, evaluator invocation, or config binding;
- the resulting projector Φ_o is judged reusable for Stage 2;
- the full evidence pack is present and reviewable.

Until a later hot update tightens numeric thresholds, the default formal interpretation is: protocol-complete benchmark evidence plus explicit judgment on reuse, not a smoke-only floor.

## 6. Required Metrics

### Benchmark metrics
- Pascal VOC 20 object-level OVS metric(s)
- Pascal Context 59 object-level OVS metric(s)
- COCO Object metric(s)
- any additional protocol-matched Talk2DINO evaluation metrics that the faithful path actually uses

### Diagnostic metrics
- checkpoint load integrity
- dataset / feature coverage
- config parity notes
- loss curves or train/eval progress indicators when training is involved
- qualitative object-grounding sanity on at least one worked example

## 7. Judgment Rule

### PASS
Return PASS only when the formal standard is fully met and E0/E1 are also passed.

### FAIL
Return FAIL when evidence shows the faithful reproduction claim is contradicted, or when the active path is proven to be non-faithful in a way that invalidates Stage 1.

### INCONCLUSIVE
Return INCONCLUSIVE when smoke results exist but the formal evidence pack is incomplete, or when protocol integrity remains unresolved.

### Trade-off rule
If one benchmark improves but another protocol-critical diagnostic or integrity check worsens materially, default to INCONCLUSIVE.

## 8. Evidence Requirements

- `phase_gate_latest`, `acceptance_latest`, and `evidence_latest`
- one worked example (md + json)
- exact command lines, config ids, and path bindings
- benchmark output table on the declared OVS validation set
- checkpoint/load-integrity notes
- explicit conclusion on whether Φ_o is reusable for Stage 2

## 9. Out of Scope

- Oracle-Obj residual-part training/evaluation
- Pred-Obj / instance-source exploration
- arbitrary backbone substitutions or non-faithful redesigns
- claiming full end-to-end WSOVPS part parsing success

## 10. Fallback / Next Step Rule

### If PASS
Freeze the accepted Stage-1 interface, archive the S1 evidence pack, and only then consider activating S2.

### If FAIL
Diagnose the smallest protocol-breaking issue and repair only that issue before rerunning.

### If INCONCLUSIVE
Close the smallest missing evidence or protocol-integrity gap first; do not broaden scope.

## 11. Re-entry Condition

Re-enter S1 after E0/E1 evidence changes, after a new smoke or formal benchmark result is produced, or after a long-running train/eval job completes and latest docs are synchronized.
