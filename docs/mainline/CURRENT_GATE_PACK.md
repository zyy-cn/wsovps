# Current Gate Pack (Derived View)

**Derived view / anti-drift notice:** canonical docs and executable truth outrank this pack.

- generated_at: `2026-03-30T22:58:57`
- registry_version: `wsovps-new-mainline-v1-private`
- active_gate_id: `S2`
- active_gate_version: `wsovps-s2-v1`
- active_gate_file: `docs/mainline/gates/scientific/S2_PP116_ORACLEOBJ_RESIDUAL_ONLY_FEASIBILITY.md`
- pack_quality: `full`

## 1. Purpose

Under the current PP116 Oracle-Obj protocol, determine whether the residual-only route is scientifically feasible and comparatively useful for object-conditioned part parsing.

## 2. Claim / Control Goal

Establish a bounded scientific claim for Stage-2 using the required B0/B1/B2 comparison chain:
- B0: direct retrieval inside object-conditioned support
- B1: object-conditioned part text without residual orthogonalization
- B2: residual-only mainline

## 4. Smoke Standard

Smoke checks may be used only to verify structural callability and protocol wiring. Smoke evidence cannot independently close S2.

## 5. Formal Standard

S2 closes only on clean official PP116 Oracle-Obj benchmark-loop evidence with valid Seen/Unseen/Harmonic reporting and B0/B1/B2 comparability.

## 6. Required Metrics

- Seen mIoU
- Unseen mIoU
- Harmonic mIoU

## 7. Judgment Rule

S2 passes only when both hold:
- Structural conditions: no trivial-collapse behavior, acceptable containment, controlled sibling overlap, non-pathological active-part behavior.
- Comparative conditions: B2 shows meaningful improvement versus B0 and B1 on official PP116 Oracle-Obj metrics.

## 8. Evidence Requirements

- formal benchmark report
- B0/B1/B2 ablation report
- qualitative packet
- diagnostic summary

## 9. Out of Scope

- Pred-Obj support sourcing
- bridge `Ψ`
- adaptive alpha
- null/none-of-listed channel
- TV loss or auxiliary enhancement branches

## 10. Fallback / Next Step Rule

If formal evidence remains partial, retain S2 as INCONCLUSIVE, preserve all run artifacts, and execute only the smallest bounded repair/rerun step needed to restore clean official benchmark-loop evidence.

## 11. Re-entry Condition

Re-enter S2 judgment only after canonical surfaces and takeover are coherent and the latest rerun provides official Seen/Unseen/Harmonic metrics through the clean formal path.

## Failure meaning
Failure means the current minimal scientific claim is not yet established. Downstream expansion must not proceed as if the mainline were already validated.

## Unlocks
Passing S2 unlocks:
- E5
- later expansion gates

## Canonical pointers
- gate doc: `docs/mainline/gates/scientific/S2_PP116_ORACLEOBJ_RESIDUAL_ONLY_FEASIBILITY.md`
- registry: `docs/mainline/gates/REGISTRY.json`
- status: `docs/mainline/STATUS.md`

