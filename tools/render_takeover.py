#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().isoformat(timespec='seconds')


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def compact(text: str, limit: int = 800) -> str:
    text = re.sub(r'\s+', ' ', text.strip())
    return text[:limit] if text else 'not-yet-declared'


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def extract_section(md: str, heading: str) -> str:
    m = re.search(rf'^##\s+{re.escape(heading)}\s*$', md, flags=re.M)
    if not m:
        return ''
    start = m.end()
    m2 = re.search(r'^##\s+', md[start:], flags=re.M)
    end = start + m2.start() if m2 else len(md)
    return md[start:end].strip()


def digest(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(str(p).encode())
        if p.exists():
            h.update(p.read_bytes())
        else:
            h.update(b'MISSING')
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    mainline = repo / 'docs/mainline'
    takeover_dir = mainline / 'takeover'
    takeover_dir.mkdir(parents=True, exist_ok=True)
    reports = mainline / 'reports'
    state_dir = mainline / 'state'
    experiments_dir = mainline / 'experiments'
    postrun_latest = mainline / 'postrun/latest'

    status = read_text(mainline / 'STATUS.md')
    ticket_md = read_text(mainline / 'CURRENT_EXECUTION_TICKET.md')
    ticket = load_json(state_dir / 'CURRENT_EXECUTION_TICKET.json', {})
    phase = read_text(reports / 'phase_gate_latest.txt')
    acceptance = read_text(reports / 'acceptance_latest.txt')
    evidence = read_text(reports / 'evidence_latest.txt')
    remote_summary_md = read_text(reports / 'remote_job_summary_latest.md')
    control_state = load_json(state_dir / 'CONTROL_PLANE_STATE.json', {})
    loop_state = load_json(mainline / 'loop_state_latest.json', {})
    active_jobs = load_json(state_dir / 'ACTIVE_JOBS.json', {'jobs': []})
    listeners = load_json(state_dir / 'LISTENER_REGISTRY.json', {'listeners': []})
    snapshot = load_json(state_dir / 'SNAPSHOT_STATE.json', {})
    gate_reg = load_json(mainline / 'gates/REGISTRY.json', {})
    exp_reg = load_json(experiments_dir / 'REGISTRY.json', {'experiments': []})
    postrun_ptr = load_json(postrun_latest / 'latest_packet_manifest.json', {})
    latest_postrun_md = read_text(postrun_latest / 'latest_postrun_evidence_packet.md')
    latest_review_ptr = load_json(postrun_latest / 'latest_review_packet.json', {})
    latest_review_md = read_text(postrun_latest / 'latest_review_packet.md')
    latest_prov = load_json(reports / 'code_provenance_report_latest.json', {})

    srcs = [
        mainline / 'STATUS.md',
        mainline / 'CURRENT_EXECUTION_TICKET.md',
        state_dir / 'CURRENT_EXECUTION_TICKET.json',
        reports / 'phase_gate_latest.txt',
        reports / 'acceptance_latest.txt',
        reports / 'evidence_latest.txt',
        reports / 'remote_job_summary_latest.md',
        reports / 'code_provenance_report_latest.json',
        state_dir / 'CONTROL_PLANE_STATE.json',
        state_dir / 'ACTIVE_JOBS.json',
        state_dir / 'LISTENER_REGISTRY.json',
        state_dir / 'SNAPSHOT_STATE.json',
        mainline / 'gates/REGISTRY.json',
        experiments_dir / 'REGISTRY.json',
        experiments_dir / 'ACTIVE_EXPERIMENTS.md',
        postrun_latest / 'latest_packet_manifest.json',
        postrun_latest / 'latest_postrun_evidence_packet.md',
        postrun_latest / 'latest_review_packet.json',
        postrun_latest / 'latest_review_packet.md',
    ]
    src_digest = digest(srcs)
    state_version = control_state.get('state_version', loop_state.get('state_version', 'not-yet-declared'))
    active_gate = control_state.get('active_gate', loop_state.get('active_gate', 'not-yet-declared'))
    active_sci = control_state.get('active_scientific_gate', loop_state.get('active_scientific_gate', 'not-yet-declared'))
    engs = gate_reg.get('active_engineering_gates', []) if isinstance(gate_reg, dict) else []
    all_exps = exp_reg.get('experiments', []) if isinstance(exp_reg, dict) else []
    active_statuses = {'approved', 'prepared', 'running', 'summarized', 'reviewed', 'interrupted', 'failed'}
    active_exps = [e for e in all_exps if e.get('status') in active_statuses and not bool(e.get('placeholder', False))]
    placeholder_exps = [e for e in all_exps if e.get('status') == 'prepared' and bool(e.get('placeholder', False))]
    recent_exps = [e for e in all_exps if e.get('status') in {'summarized', 'reviewed', 'accepted', 'rejected', 'inconclusive'}]

    ticket_meta = {
        'objective': ticket.get('objective', compact(extract_section(ticket_md, 'Objective'), 400)),
        'formal_pass': ticket.get('formal_pass', compact(extract_section(ticket_md, 'Formal PASS requires'), 500)),
        'allowed_scope': ticket.get('allowed_scope', compact(extract_section(ticket_md, 'Allowed execution scope'), 500)),
        'resume_note': ticket.get('resume_note', compact(extract_section(ticket_md, 'Resume / re-entry note'), 300)),
        'governance_ingestion_note': ticket.get('governance_ingestion_note', 'not-yet-declared'),
        'archive_sync_note': ticket.get('archive_sync_note', 'not-yet-declared'),
        'long_running': bool(ticket.get('long_running', False)),
        'watcher_required': bool(ticket.get('watcher_required', False)),
        'listener_required': bool(ticket.get('listener_required', False)),
        'git_boundary': bool(ticket.get('git_boundary', False)),
        'experiment_id': ticket.get('experiment_id', 'not-yet-declared'),
        'run_id': ticket.get('run_id', 'not-yet-declared'),
        'question_type': ticket.get('question_type', 'not-yet-declared'),
        'level': ticket.get('level', 'not-yet-declared'),
        'expected_next_status': ticket.get('expected_next_status', 'not-yet-declared'),
        'allowed_tools': ticket.get('allowed_tools', []),
        'delivery_mode': ticket.get('delivery_mode', 'prompt'),
        'design_pack_id': ticket.get('design_pack_id', 'not-yet-declared'),
        'design_pack_status': ticket.get('design_pack_status', 'not-yet-declared'),
        'milestone_id': ticket.get('milestone_id', 'not-yet-declared'),
        'commit_sha': ticket.get('commit_sha', snapshot.get('commit_sha', 'not-yet-declared')),
        'tree_sha': ticket.get('tree_sha', snapshot.get('tree_sha', 'not-yet-declared')),
        'working_tree_clean': ticket.get('working_tree_clean', snapshot.get('working_tree_clean', 'not-yet-declared')),
        'config_snapshot_path': ticket.get('config_snapshot_path', 'not-yet-declared'),
    }
    code_summary = {
        'execution_model': 'local-first',
        'current_sync_mode': snapshot.get('sync_mode', 'not-yet-declared'),
        'local_snapshot_id': snapshot.get('local_snapshot_id', 'not-yet-declared'),
        'remote_snapshot_id': snapshot.get('remote_snapshot_id', 'not-yet-declared'),
        'bound_job_id': snapshot.get('bound_job_id', 'not-yet-declared'),
        'commit_sha': snapshot.get('commit_sha', 'not-yet-declared'),
        'tree_sha': snapshot.get('tree_sha', 'not-yet-declared'),
        'working_tree_clean': snapshot.get('working_tree_clean', 'not-yet-declared'),
    }
    runtime_state = {
        'active_jobs': active_jobs.get('jobs', []) if isinstance(active_jobs, dict) else [],
        'listeners': listeners.get('listeners', []) if isinstance(listeners, dict) else [],
        'latest_remote_summary': compact(remote_summary_md, 800),
    }
    experiment_ledger = {
        'active_count': len(active_exps),
        'active': [
            {
                'experiment_id': e.get('experiment_id', 'not-yet-declared'),
                'gate_id': e.get('gate_id', 'not-yet-declared'),
                'level': e.get('level', 'not-yet-declared'),
                'status': e.get('status', 'not-yet-declared'),
                'active_run_id': e.get('active_run_id', 'not-yet-declared'),
                'eligible_for_gate_judgment': bool(e.get('eligible_for_gate_judgment', False)),
            }
            for e in active_exps[:12]
        ],
        'prepared_placeholders': [
            {
                'experiment_id': e.get('experiment_id', 'not-yet-declared'),
                'gate_id': e.get('gate_id', 'not-yet-declared'),
                'level': e.get('level', 'not-yet-declared'),
                'status': e.get('status', 'not-yet-declared'),
                'active_run_id': e.get('active_run_id', 'not-yet-declared'),
                'eligible_for_gate_judgment': bool(e.get('eligible_for_gate_judgment', False)),
            }
            for e in placeholder_exps[:12]
        ],
        'recent': [
            {
                'experiment_id': e.get('experiment_id', 'not-yet-declared'),
                'status': e.get('status', 'not-yet-declared'),
                'level': e.get('level', 'not-yet-declared'),
            }
            for e in recent_exps[:12]
        ],
        'current_ticket_experiment': ticket_meta['experiment_id'],
    }
    acceptance_state = {
        'phase_gate': compact(phase, 500),
        'acceptance': compact(acceptance, 500),
        'evidence': compact(evidence, 500),
        'scientific_status': control_state.get('scientific_status', 'not-yet-declared'),
        'engineering_status': control_state.get('engineering_status', 'not-yet-declared'),
        'overall_status': control_state.get('overall_status', 'not-yet-declared'),
    }
    blockers = [compact(extract_section(status, 'Current blockers'), 1200), compact(extract_section(status, 'Current experiment blockers'), 600)]
    latest_postrun = {'pointer': postrun_ptr, 'summary': compact(latest_postrun_md, 1200)}
    latest_review = {'pointer': latest_review_ptr, 'summary': compact(latest_review_md, 1200)}
    artifacts = [
        'docs/mainline/STATUS.md',
        'docs/mainline/CURRENT_EXECUTION_TICKET.md',
        'docs/mainline/state/CURRENT_EXECUTION_TICKET.json',
        'docs/mainline/reports/phase_gate_latest.txt',
        'docs/mainline/reports/acceptance_latest.txt',
        'docs/mainline/reports/evidence_latest.txt',
        'docs/mainline/reports/remote_job_summary_latest.md',
        'docs/mainline/reports/code_provenance_report_latest.md',
        'docs/mainline/experiments/REGISTRY.json',
        'docs/mainline/experiments/ACTIVE_EXPERIMENTS.md',
        'docs/mainline/postrun/latest/latest_packet_manifest.json',
        'docs/mainline/postrun/latest/latest_postrun_evidence_packet.md',
        'docs/mainline/postrun/latest/latest_review_packet.json',
        'docs/mainline/postrun/latest/latest_review_packet.md',
        'docs/mainline/takeover/TAKEOVER_LATEST.md',
    ]
    next_candidates = [
        'repair ticket, git preconditions, or registry state if any required fields are missing',
        'execute only the smallest step that serves the active gate, delivery mode, and bound experiment/design pack',
        'refresh takeover after summary, acceptance, experiment-state, post-run packet, or review packet changes',
    ]

    md = f"""# Takeover Latest

This is the primary handoff artifact for web-side GPT review.

- generated_at: `{now()}`
- source_digest: `{src_digest}`
- state_version: `{state_version}`

## Current control-plane truth
- active_gate: `{active_gate}`
- active_scientific_gate: `{active_sci}`
- supporting_engineering_gates: `{engs}`
- scientific_status: `{acceptance_state['scientific_status']}`
- engineering_status: `{acceptance_state['engineering_status']}`
- overall_status: `{acceptance_state['overall_status']}`

## Current execution ticket
- objective: {ticket_meta['objective']}
- delivery_mode: `{ticket_meta['delivery_mode']}`
- design_pack_id: `{ticket_meta['design_pack_id']}`
- design_pack_status: `{ticket_meta['design_pack_status']}`
- milestone_id: `{ticket_meta['milestone_id']}`
- experiment_id: `{ticket_meta['experiment_id']}`
- run_id: `{ticket_meta['run_id']}`
- question_type: `{ticket_meta['question_type']}`
- level: `{ticket_meta['level']}`
- expected_next_status: `{ticket_meta['expected_next_status']}`
- long_running: `{ticket_meta['long_running']}`
- watcher_required: `{ticket_meta['watcher_required']}`
- listener_required: `{ticket_meta['listener_required']}`
- git_boundary: `{ticket_meta['git_boundary']}`
- commit_sha: `{ticket_meta['commit_sha']}`
- tree_sha: `{ticket_meta['tree_sha']}`
- working_tree_clean: `{ticket_meta['working_tree_clean']}`
- config_snapshot_path: `{ticket_meta['config_snapshot_path']}`
- governance_ingestion_note: `{ticket_meta['governance_ingestion_note']}`
- archive_sync_note: `{ticket_meta['archive_sync_note']}`
- allowed_tools: `{ticket_meta['allowed_tools']}`
- formal_pass: {ticket_meta['formal_pass']}
- allowed_scope: {ticket_meta['allowed_scope']}

## Experiment Ledger
- active_count: `{experiment_ledger['active_count']}`
- current_ticket_experiment: `{experiment_ledger['current_ticket_experiment']}`
- active_experiments:
{json.dumps(experiment_ledger['active'], ensure_ascii=False, indent=2)}
- recent_experiments:
{json.dumps(experiment_ledger['recent'], ensure_ascii=False, indent=2)}

## Code and sync summary
- execution_model: `{code_summary['execution_model']}`
- current_sync_mode: `{code_summary['current_sync_mode']}`
- local_snapshot_id: `{code_summary['local_snapshot_id']}`
- remote_snapshot_id: `{code_summary['remote_snapshot_id']}`
- bound_job_id: `{code_summary['bound_job_id']}`
- commit_sha: `{code_summary['commit_sha']}`
- tree_sha: `{code_summary['tree_sha']}`
- working_tree_clean: `{code_summary['working_tree_clean']}`

## Latest runtime / remote summary
- active_jobs: `{len(runtime_state['active_jobs'])}`
- listeners: `{len(runtime_state['listeners'])}`
- latest_remote_summary: {runtime_state['latest_remote_summary']}

## Latest Post-run Evidence
- latest_packet_pointer: `{latest_postrun['pointer'].get('path', 'not-yet-declared')}`
- latest_packet_status: `{latest_postrun['pointer'].get('status', 'not-yet-declared')}`
- latest_packet_experiment: `{latest_postrun['pointer'].get('experiment_id', 'not-yet-declared')}`
- latest_packet_run: `{latest_postrun['pointer'].get('run_id', 'not-yet-declared')}`
- latest_packet_summary: {latest_postrun['summary']}

## Latest Review Packet
- latest_review_pointer: `{latest_review['pointer'].get('path', 'not-yet-declared')}`
- latest_review_md_path: `{latest_review['pointer'].get('md_path', 'not-yet-declared')}`
- latest_review_experiment: `{latest_review['pointer'].get('experiment_id', 'not-yet-declared')}`
- latest_review_run: `{latest_review['pointer'].get('run_id', 'not-yet-declared')}`
- latest_review_final_state: `{latest_review['pointer'].get('final_state', 'not-yet-declared')}`
- latest_review_summary: {latest_review['summary']}

## Latest Code Provenance
- commit_sha: `{latest_prov.get('commit_sha', 'not-yet-declared')}`
- tree_sha: `{latest_prov.get('tree_sha', 'not-yet-declared')}`
- working_tree_clean: `{latest_prov.get('working_tree_clean', 'not-yet-declared')}`
- runtime_override_present: `{latest_prov.get('runtime_override_present', 'not-yet-declared')}`
- config_snapshot_hash: `{latest_prov.get('config_snapshot_hash', 'not-yet-declared')}`
- remote_tree_verified: `{latest_prov.get('remote_tree_verified', 'not-yet-declared')}`

## Current evidence / acceptance summary
- phase_gate: {acceptance_state['phase_gate']}
- acceptance: {acceptance_state['acceptance']}
- evidence: {acceptance_state['evidence']}

## Blockers and risks
- blockers: {blockers}

## Next candidate actions
- {next_candidates[0]}
- {next_candidates[1]}
- {next_candidates[2]}

## Artifact pointers
- {artifacts}
"""
    (takeover_dir / 'TAKEOVER_LATEST.md').write_text(md, encoding='utf-8')
    payload = {
        'generated_at': now(),
        'source_digest': src_digest,
        'state_version': state_version,
        'active_gate': active_gate,
        'active_scientific_gate': active_sci,
        'supporting_engineering_gates': engs,
        'ticket': ticket_meta,
        'code_summary': code_summary,
        'runtime_state': runtime_state,
        'latest_postrun': latest_postrun['pointer'],
        'latest_review': latest_review['pointer'],
        'latest_provenance': latest_prov,
        'acceptance_state': acceptance_state,
        'experiment_ledger': experiment_ledger,
        'blockers': blockers,
        'artifacts': artifacts,
        'next_candidates': next_candidates,
    }
    (takeover_dir / 'TAKEOVER_LATEST.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    print(str(takeover_dir / 'TAKEOVER_LATEST.md'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
