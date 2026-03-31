#!/usr/bin/env bash
set -euo pipefail
python tools/render_state_views.py
python tools/render_gate_pack.py
python tools/render_takeover.py
python tools/validate_gate_registry.py
python tools/validate_experiment_registry.py
python tools/validate_control_plane_coherence.py
python tools/validate_state_views.py
