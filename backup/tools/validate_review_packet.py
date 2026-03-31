#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

FORBIDDEN = ['supports_gate', 'blocks_gate', 'inconclusive', 'recommended_next_actions', '"should"', '"ought"', '"recommend"']


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--review-packet-json', required=True)
    args = ap.parse_args()
    path = Path(args.review_packet_json).resolve()
    errs: list[str] = []
    payload = {}
    if not path.exists():
        errs.append('missing review packet json')
    else:
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception as e:
            errs.append(f'invalid json: {e}')
        for key in ['gate_id', 'experiment_id', 'run_id', 'job_id', 'final_state', 'metrics', 'comparison_facts', 'diagnostics', 'artifact_paths', 'provenance']:
            if key not in payload:
                errs.append(f'missing {key}')
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        for token in FORBIDDEN:
            if token in serialized:
                errs.append(f'forbidden decision-like token present: {token}')
    if errs:
        print('CONFLICTED: review packet invalid')
        for e in errs:
            print('-', e)
        return 1
    print('OK: review packet is valid and non-decision')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
