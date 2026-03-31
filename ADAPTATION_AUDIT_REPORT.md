# WSOVPS Private-Layer Adaptation Audit

## Conclusion
The first generated overlay was **not clean enough**. It retained structural dependencies on the old in-project kit/control-plane and therefore could not be guaranteed as a pure v5p4-lite private layer.

## Concrete contamination / incompleteness found
1. `AGENTS.md`, `INDEX.md`, `IMPLEMENT.md`, and Prompt 2 referenced canonical files that the overlay did not provide.
2. The overlay omitted `docs/mainline/gates/*` entirely while still referencing gate registry files and active gate docs.
3. The overlay retained old authority lines pointing at `docs/mainline/reports/takeover_latest.md` / `TAKEOVER_SCHEMA.md`, which conflicts with takeover-first v5p4-lite handoff.
4. Prompt 2 required `python tools/validate_gate_registry.py --repo-root .`, but the overlay did not provide that tool.

## Repair strategy used in this clean build
- re-based the private layer on the new v5p4-lite kit assets,
- restored the full canonical `docs/mainline/*` surface expected by the kit,
- restored the gate registry and gate docs,
- removed old takeover authority from the new private layer,
- preserved only project facts and archived progress truth from the original WSOVPS package.

## Preserved project facts
- project: `WSOVPS`
- active scientific gate: `S1`
- supporting engineering gates: `E0`, `E1`
- archived state: `S1 PASS frozen and archived`
- archived commit truth: `{commit}`
- archived trained benchmark pack: `{metrics_trained}`
- archived official comparison pack: `{metrics_official}`
