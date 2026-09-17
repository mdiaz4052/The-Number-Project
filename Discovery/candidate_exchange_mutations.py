"""Six production mutations with semantic assertion kills, plus two controls."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

from Discovery import candidate_exchange as cx

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('domain_erasure', 'Discovery/candidate_exchange.py',
     "values = [go(a) for a in n['args']]",
     "values = [0.0] if op == 'multiply' and any(a == {'op': 'literal', 'number': {'kind': 'exact', 'numerator': 0, 'denominator': 1}} for a in n['args']) else [go(a) for a in n['args']]",
     'test_domain_erasure'),
    ('leakage_bypass', 'Discovery/candidate_exchange.py',
     "leaking = sorted(k for k in refs if target_path(k))",
     "leaking = []",
     'test_target_leakage'),
    ('dimension_bypass', 'Discovery/candidate_exchange.py',
     "require(dimension == dimensions[m['target']], 'DIMENSION', 'Expression and target dimensions differ.')",
     "require(True, 'DIMENSION', 'Expression and target dimensions differ.')",
     'test_dimension_bypass'),
    ('evidence_promotion', 'Discovery/candidate_exchange.py',
     "'scientific_evidence': dict(PROMOTION), 'candidate_status': CANDIDATE_STATUS,",
     "'scientific_evidence': {**PROMOTION, **candidate['claims']}, 'candidate_status': CANDIDATE_STATUS,",
     'test_evidence_promotion'),
    ('raw_binding_bypass', 'Discovery/candidate_exchange_adapters.py',
     "cx.require(bundle == expected, 'RAW_BINDING', 'Receipt, inventory or normalized records disagree with exact raw source.')",
     "cx.require(True, 'RAW_BINDING', 'Receipt, inventory or normalized records disagree with exact raw source.')",
     'test_raw_binding_tampering'),
    ('candidate_loss', 'Discovery/candidate_exchange_adapters.py',
     "for index, item in enumerate(items):",
     "for index, item in enumerate(items[:1]):",
     'test_candidate_inventory'),
]


def run_case(name, path=None, old=None, new=None, test=None):
    with tempfile.TemporaryDirectory(prefix='tnp-exchange-mutation-') as temp:
        stage = Path(temp)
        shutil.copytree(ROOT / 'Discovery', stage / 'Discovery', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy(ROOT / 'tests/test_candidate_exchange.py', stage / 'exchange_tests.py')
        if path:
            target = stage / path; text = target.read_text()
            if old is None: text += new
            else:
                cx.require(text.count(old) == 1, 'MUTATION_SETUP', 'Mutation site must be unique.')
                text = text.replace(old, new)
            target.write_text(text)
        names = [test] if test else [case[-1] for case in CASES]
        command = [sys.executable, '-B', '-m', 'unittest', *['exchange_tests.ExchangeTests.' + n for n in names], '-v']
        proc = subprocess.run(command, cwd=stage, capture_output=True, text=True, timeout=30)
        output = (proc.stdout + proc.stderr).replace(str(stage), '<stage>')
        # No syntax/import/runtime failure or binding guard failure may earn a kill.
        semantic = (proc.returncode == 1 and 'FAIL: ' in output and 'AssertionError' in output
                    and 'ERROR:' not in output and 'Traceback' in output
                    and all(word not in output for word in ('SyntaxError', 'ImportError', 'ModuleNotFoundError')))
        return {'name': name, 'test_methods': names, 'production_path': path,
                'mutation_before': old, 'mutation_after': new, 'returncode': proc.returncode,
                'semantic_assertion_kill': semantic, 'survived': proc.returncode == 0,
                'output': output, 'stage_source_digest': cx.sha((stage / path).read_bytes()) if path else None}


def run():
    rows = [run_case('baseline'), run_case('equivalent_control', 'Discovery/candidate_exchange.py', None,
                                         '\n# Semantically equivalent control: comment only.\n')]
    rows += [run_case(*case) for case in CASES]
    return {'schema': cx.NS + '/mutations', 'controls': rows[:2], 'mutants': rows[2:],
            'calibrated': all(r['survived'] for r in rows[:2]) and all(r['semantic_assertion_kill'] for r in rows[2:])}


if __name__ == '__main__':
    print(json.dumps(run(), sort_keys=True, indent=2))
