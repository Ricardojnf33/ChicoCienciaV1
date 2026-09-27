"""Validate E00 planning artifacts without importing the application or calling APIs."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import sys

REQUIRED = [
    'docs/mestrado/roadmap.html',
    'docs/mestrado/roadmap.json',
    'docs/mestrado/EXECUCAO_ROADMAP.md',
    'docs/mestrado/PENDENCIAS_USUARIO.md',
    'docs/mestrado/RELATORIO_FINAL.md',
    'docs/mestrado/README.md',
    'docs/mestrado/REGISTRO_PROCESSO.md',
    'docs/mestrado/evidencias/e00-20260927/baseline.json',
    'docs/mestrado/evidencias/e00-20260927/index.md',
    'scripts/validate_roadmap.py',
    '.github/workflows/roadmap-e00.yml',
]


class RoadmapParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.anchors = []
        self.tasks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if attrs.get('href', '').startswith('#'):
            self.anchors.append(attrs['href'][1:])
        if 'data-task' in attrs:
            self.tasks.append(attrs['data-task'])


def validate(root):
    checks = []

    def check(name, condition, detail):
        checks.append({'name': name, 'passed': bool(condition), 'detail': detail})

    missing = [p for p in REQUIRED if not (root / p).is_file()]
    check('required_files', not missing, {'missing': missing})
    if missing:
        return checks, {}, {}
    hashes = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in REQUIRED}
    try:
        epics = json.loads((root / REQUIRED[1]).read_text(encoding='utf-8'))
        baseline = json.loads((root / REQUIRED[7]).read_text(encoding='utf-8'))
        parser = RoadmapParser()
        parser.feed((root / REQUIRED[0]).read_text(encoding='utf-8'))
        stories = [s for e in epics for s in e['stories']]
        tasks = [t for s in stories for t in s['tasks']]
        known = {e['id'] for e in epics} | {s['id'] for s in stories}
        all_ids = [e['id'] for e in epics] + [s['id'] for s in stories] + [t['id'] for t in tasks]
        check('unique_backlog_ids', len(all_ids) == len(set(all_ids)), len(all_ids))
        check('unique_html_ids', len(parser.ids) == len(set(parser.ids)), len(parser.ids))
        check('html_anchors_resolve', all(a in parser.ids for a in parser.anchors), parser.anchors)
        check('task_parity', sorted(parser.tasks) == sorted(t['id'] for t in tasks), len(tasks))
        dangling = [(x['id'], d) for x in epics + stories for d in x['deps'] if d not in known]
        check('dependencies_resolve', not dangling, dangling)
        # An epic reference expands to its stories; do not infer that every story
        # waits for the whole parent epic (some epics span the entire project).
        by_epic = {e['id']: [s['id'] for s in e['stories']] for e in epics}
        graph = {s['id']: [v for d in s['deps'] for v in by_epic.get(d, [d])] for s in stories}
        visiting, done = set(), set()

        def visit(node):
            if node in visiting:
                raise ValueError('cyclic story dependency: ' + node)
            if node in done:
                return
            visiting.add(node)
            for child in graph.get(node, []):
                visit(child)
            visiting.remove(node)
            done.add(node)

        try:
            for node in graph:
                visit(node)
            check('story_dependency_graph_acyclic', True, len(graph))
        except ValueError as exc:
            check('story_dependency_graph_acyclic', False, str(exc))
        check('acceptance_criteria_present', all(s['accept'].strip() for s in stories), len(stories))
        check('monitoring_required', 'E12' in by_epic and 'monitoramento' in parser.ids,
              'E12 and dedicated monitoring section')
        check('phase5_not_claimed_valid', baseline['findings']['phase5_e2e_validated'] is False,
              baseline['findings']['status'])
        check('snapshot_shas', all(len(baseline[k]) == 40 for k in ['main_sha', 'phase5_sha']),
              {'main': baseline['main_sha'], 'phase5': baseline['phase5_sha']})
        counts = {'epics': len(epics), 'stories': len(stories), 'tasks': len(tasks),
                  'subtasks': sum(len(t['subtasks']) for t in tasks)}
    except (KeyError, TypeError, ValueError) as exc:
        check('parse_and_schema', False, str(exc))
        counts = {}
    return checks, hashes, counts


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args.add_argument('--output', type=Path, required=True)
    opts = args.parse_args()
    checks, hashes, counts = validate(opts.root)
    passed = bool(checks) and all(c['passed'] for c in checks)
    report = {
        'schema_version': '1.0', 'increment': 'E00',
        'scope': 'Document integrity only; not application tests, live E2E or scientific validation.',
        'passed': passed, 'checks': checks, 'counts': counts,
        'source_commit': os.environ.get('GITHUB_SHA', 'LOCAL_WORKING_TREE'),
        'run_id': os.environ.get('GITHUB_RUN_ID'),
        'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
        'actor': os.environ.get('GITHUB_ACTOR'),
        'llm_api_calls_performed_by_this_validator': 0,
        'gate_g0_academic_approval': 'PENDING_USER_INPUT',
        'gate_g2_e2e': 'NOT_VALIDATED',
        'next_step': 'WAIT_FOR_MANUAL_ACTIONS_AND_REVIEW',
    }
    opts.output.mkdir(parents=True, exist_ok=True)
    (opts.output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    (opts.output / 'checksums.json').write_text(json.dumps(hashes, indent=2) + '\n')
    summary = ('# E00 validation\n\n' + ('PASS' if passed else 'FAIL') +
               '\n\nDocument integrity only. No live experiment was executed.\n\n' +
               '\n'.join(f"- {'PASS' if c['passed'] else 'FAIL'}: {c['name']}" for c in checks) + '\n')
    (opts.output / 'summary.md').write_text(summary)
    print(summary)
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
