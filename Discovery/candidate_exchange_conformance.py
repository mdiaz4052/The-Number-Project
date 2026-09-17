"""One bounded conformance disposition and read-only committed-evidence guard.

Commands: pin-source, emit, check. emit refuses to replace published evidence.
No historical campaign, fitting, oracle or heldout replay is invoked.
"""
from __future__ import annotations
import argparse
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import unittest

from Discovery import candidate_exchange as cx
from Discovery import candidate_exchange_adapters as adapters
from Discovery import candidate_exchange_fixtures as fixtures
from Discovery import candidate_exchange_history as history
from Discovery import candidate_exchange_mutations as mutations

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / 'Experiments/SymbolicDiscovery/CandidateExchange1'
REL = str(PKG.relative_to(ROOT))
SOURCE_PATHS = ['Discovery/candidate_exchange.py', 'Discovery/candidate_exchange_adapters.py',
    'Discovery/candidate_exchange_history.py', 'Discovery/candidate_exchange_fixtures.py',
    'Discovery/candidate_exchange_mutations.py', 'Discovery/candidate_exchange_conformance.py',
    'tests/test_candidate_exchange.py', 'Discovery/dimensions.py', 'Discovery/symbolic_benchmark_engine.py',
    'Discovery/dependency_definitions.py', 'Discovery/planck_identities.py', 'Discovery/constants.py',
    'Discovery/dimensional_search.py', 'Discovery/monomial_constraints.py'] + [REL + '/' + x for x in
    ('mock_pairs.json', 'historical_metadata.json', 'contract.v1.md', 'work_order.r1.md', 'work_order_receipt.json', 'anchor.json', 'interface.md')]
NUMERIC_POLICY = {'historical_relative_tolerance': 2e-12, 'historical_absolute_tolerance': 1e-14,
                  'paired_absolute_tolerance': 1e-13, 'comparison': 'original_log_route_vs_expression_route'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def read(name): return json.loads((PKG / name).read_text())


def write_new(name, value):
    with (PKG / name).open('xb') as stream: stream.write(cx.encoded(value))


def environment():
    cx.require(sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 12), 'ENVIRONMENT', 'CPython 3.12 required for this evidence epoch.')
    return {'implementation': sys.implementation.name, 'version': platform.python_version(),
            'cache_tag': sys.implementation.cache_tag, 'platform': sys.platform}


def pin_source():
    env = environment(); head = git('rev-parse', 'HEAD')
    bindings = {}
    for path in SOURCE_PATHS:
        raw = (ROOT / path).read_bytes()
        committed = subprocess.check_output(['git', 'show', head + ':' + path], cwd=ROOT)
        cx.require(raw == committed, 'SOURCE_PIN', 'Pin only committed source bytes.')
        bindings[path] = cx.sha(raw)
    write_new('source_snapshot.json', {'schema': cx.NS + '/source-snapshot', 'source_sha': head,
        'files': bindings, 'numeric_policy': NUMERIC_POLICY, 'environment': env,
        'historical_head': history.PIN, 'historical_blobs': history.BLOBS})


def test_evidence():
    from tests.test_candidate_exchange import ExchangeTests
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ExchangeTests)
    names = [t.id() for t in suite]
    stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    return {'methods': names, 'tests_run': result.testsRun, 'success': result.wasSuccessful(),
            'failures': len(result.failures), 'errors': len(result.errors), 'output': stream.getvalue().replace(str(ROOT), '<repo>')}


def demonstration():
    records = []
    m = fixtures.manifest()
    pairs = fixtures.paired()
    for fmt, key in [('mock-tree/1', 'tree'), ('mock-postfix/1', 'postfix')]:
        raw = fixtures.raw([p[key] for p in pairs], m, fmt)
        source = 'visible_fixture:' + fmt
        bundle = adapters.ingest(m, raw, fmt, source)
        points = fixtures.fixed_points()
        result = adapters.evaluate_records(m, raw, fmt, bundle, points, source)
        records.append({'name': fmt, 'manifest': m, 'raw_utf8': raw.decode(), 'format': fmt,
                        'source': source, 'records': bundle, 'points': points, 'evaluation': result})
    for name in history.BLOBS:
        m, raw, bundle = history.imported(name)
        source = history.PIN + ':' + history.MARGIN + '/selection/' + name + '.json'
        points = fixtures.fixed_points()
        result = adapters.evaluate_records(m, raw, 'internal-margin1/1', bundle, points, source)
        records.append({'name': name, 'manifest': m, 'raw_source': source, 'format': 'internal-margin1/1',
                        'source': source, 'records': bundle, 'points': points, 'evaluation': result})
    return records


def verify_demo(records):
    cx.require(type(records) is list and [r['name'] for r in records] == ['mock-tree/1', 'mock-postfix/1', *history.BLOBS], 'DEMO', 'Exact demonstration inventory required.')
    for record in records:
        hist = record['name'] in history.BLOBS
        cx.fields(record, {'name', 'manifest', 'raw_source' if hist else 'raw_utf8', 'format', 'source', 'records', 'points', 'evaluation'})
        if hist:
            manifest, raw, original = history.imported(record['name'])
            cx.require(record['raw_source'] == record['source'] == original['receipt']['source']['location'], 'RAW_BINDING', 'Wrong pinned historical source.')
            cx.require(record['manifest'] == manifest and record['records'] == original, 'RAW_BINDING', 'Historical record differs from pinned full ranking.')
            count = 5
        else:
            manifest = fixtures.manifest(); fmt = record['name']
            key = 'tree' if fmt == 'mock-tree/1' else 'postfix'
            raw = fixtures.raw([p[key] for p in fixtures.paired()], manifest, fmt)
            cx.require(record['manifest'] == manifest and record['raw_utf8'].encode() == raw and record['format'] == fmt, 'RAW_BINDING', 'Mock bytes differ from independent fixture.')
            count = 3
        cx.require(record['points'] == fixtures.fixed_points(), 'FIXTURE', 'Named fixture points changed.')
        adapters.verify_records(manifest, raw, record['format'], record['records'], record['source'])
        adapters.verify_cards(manifest, raw, record['format'], record['records'], record['points'], record['evaluation'], record['source'])
        cards = record['evaluation']['cards']
        cx.require(len(cards) == count and all(c['outcome'] == 'PASS' for c in cards), 'DEMO', 'Missing or unsuccessful demonstration candidate.')
        for i, card in enumerate(cards):
            cx.require(card['scientific_evidence'] == cx.PROMOTION and card['candidate_status'] == cx.CANDIDATE_STATUS, 'EVIDENCE', 'Scientific promotion forbidden.')
            if not hist:
                expected = fixtures.paired()[i]['expected']
            else:
                old = record['records']['candidates'][i]['source_item']
                from fractions import Fraction
                expected = [math.exp(old['log_coefficient'] + math.fsum(float(Fraction(p)) * math.log(point['values'][k])
                    for k, p in old['representative'].items())) for point in record['points']]
            for row, value in zip(card['numerical_checks'], expected):
                cx.require(math.isclose(row['value'], value, rel_tol=2e-12 if hist else 0., abs_tol=1e-14 if hist else 1e-13), 'NUMERICS', 'Independent fixture expectation disagrees.')
    for left, right in zip(records[0]['evaluation']['cards'], records[1]['evaluation']['cards']):
        cx.require(cx.equivalence(left['representation'], right['representation']) == 'ESTABLISHED_SUPPORTED_RULES', 'EQUIVALENCE', 'Lawful mock pair normalization disagrees.')


def source_check():
    environment()
    snapshot = read('source_snapshot.json')
    cx.schema(snapshot, 'source-snapshot', {'source_sha', 'files', 'numeric_policy', 'environment', 'historical_head', 'historical_blobs'})
    cx.require(set(snapshot['files']) == set(SOURCE_PATHS), 'SOURCE_PIN', 'Incomplete source inventory.')
    cx.require(snapshot['numeric_policy'] == NUMERIC_POLICY and snapshot['historical_head'] == history.PIN and snapshot['historical_blobs'] == history.BLOBS, 'SOURCE_PIN', 'Source policy mismatch.')
    for path, expected in snapshot['files'].items():
        raw = (ROOT / path).read_bytes()
        cx.require(cx.sha(raw) == expected, 'SOURCE_PIN', 'Changed source/evidence binding: ' + path)
        pinned = subprocess.check_output(['git', 'show', snapshot['source_sha'] + ':' + path], cwd=ROOT)
        cx.require(raw == pinned, 'SOURCE_PIN', 'Working bytes differ from immutable source epoch.')
    anchor = read('anchor.json')
    cx.schema(anchor, 'anchor', {'pr', 'created_at', 'snapshot_sha', 'freeze_sha', 'base_sha'})
    cx.require(git('show', '--pretty=', '--name-only', anchor['freeze_sha']) == REL + '/contract.v1.md', 'CHRONOLOGY', 'Contract freeze must be sole-file commit.')
    for before, after in [(anchor['base_sha'], anchor['snapshot_sha']), (anchor['snapshot_sha'], anchor['freeze_sha']), (anchor['freeze_sha'], snapshot['source_sha']), (snapshot['source_sha'], git('rev-parse', 'HEAD'))]:
        cx.require(subprocess.run(['git','merge-base','--is-ancestor',before,after],cwd=ROOT).returncode == 0, 'CHRONOLOGY', 'Accepted ancestry/freeze chain lost.')
    from datetime import datetime
    freeze_time = datetime.fromisoformat(git('show','-s','--format=%cI',anchor['freeze_sha']))
    source_time = datetime.fromisoformat(git('show','-s','--format=%cI',snapshot['source_sha']))
    draft_time = datetime.fromisoformat(anchor['created_at'].replace('Z','+00:00'))
    cx.require(freeze_time <= draft_time < source_time, 'CHRONOLOGY', 'Draft server anchor must precede implementation source.')
    receipt=read('work_order_receipt.json')
    cx.require(receipt['sha256'] == cx.sha((PKG/'work_order.r1.md').read_bytes()),'SOURCE_PIN','Consumed work order mismatch.')
    # Only directly implicated preserved subtrees; no unrelated historical recomputation.
    for path in ('Experiments/SymbolicDiscovery/Benchmark0','Experiments/SymbolicDiscovery/BenchmarkSuite1',history.MARGIN,'.github/workflows/verify.yml'):
        cx.require(not git('diff',anchor['base_sha'],'--',path), 'IMMUTABILITY', 'Historical or CI surface changed: '+path)
    return snapshot


def emit():
    snapshot = source_check()
    cx.require(not (PKG / 'conformance.json').exists(), 'EVIDENCE_EXISTS', 'Never overwrite an evidence epoch.')
    tests = test_evidence(); mutation_result = mutations.run(); records = demonstration()
    demo_error = None
    try: verify_demo(records)
    except cx.ContractError as e: demo_error = {'code':e.code,'message':e.message}
    passed = tests['success'] and mutation_result['calibrated'] and demo_error is None
    report = {'schema': cx.NS + '/conformance', 'task': 'NP-CANDIDATE-EXCHANGE-01',
        'disposition': 'CANDIDATE_EXCHANGE_1_PASS' if passed else 'CANDIDATE_EXCHANGE_1_FAIL',
        'review_status': 'PROVISIONAL — INDEPENDENT AUDIT PENDING', 'outcome_blind': False,
        'evidence_mode': 'deterministic_contract_conformance', 'source_snapshot_digest': cx.digest(snapshot),
        'tests': tests, 'mutations': mutation_result, 'demonstrations': records, 'demonstration_error': demo_error,
        'claim': 'bounded internal contract integrity; no new scientific promotion or real-engine compatibility'}
    write_new('conformance.json', report)
    return report['disposition']


def check():
    snapshot = source_check(); report = read('conformance.json')
    cx.schema(report, 'conformance', {'task','disposition','review_status','outcome_blind','evidence_mode',
        'source_snapshot_digest','tests','mutations','demonstrations','demonstration_error','claim'})
    cx.require(report['source_snapshot_digest'] == cx.digest(snapshot), 'SOURCE_PIN', 'Report/source snapshot binding mismatch.')
    cx.require(report['task'] == 'NP-CANDIDATE-EXCHANGE-01' and report['disposition'] == 'CANDIDATE_EXCHANGE_1_PASS', 'DISPOSITION', 'Wrong authoritative disposition route.')
    cx.require(report['outcome_blind'] is False and report['evidence_mode'] == 'deterministic_contract_conformance' and report['review_status'] == 'PROVISIONAL — INDEPENDENT AUDIT PENDING', 'EVIDENCE', 'Evidence classification changed.')
    test = report['tests']
    from tests.test_candidate_exchange import ExchangeTests
    expected = [t.id() for t in unittest.defaultTestLoader.loadTestsFromTestCase(ExchangeTests)]
    cx.require(test['methods'] == expected and test['tests_run'] == len(expected) and test['success'] is True and test['errors'] == test['failures'] == 0, 'TEST_EVIDENCE', 'Conformance test inventory or outcome mismatch.')
    mutation = report['mutations']
    cx.require(mutation['calibrated'] is True and len(mutation['controls']) == 2 and len(mutation['mutants']) == 6, 'MUTATIONS', 'Mutation evidence incomplete.')
    for row, expected_name in zip(mutation['controls'], ('baseline','equivalent_control')):
        cx.require(row['name'] == expected_name and row['survived'] is True and row['returncode'] == 0 and 'OK' in row['output'], 'MUTATIONS', 'Control did not survive.')
    for row, case in zip(mutation['mutants'], mutations.CASES):
        name,path,old,new,test_name = case
        cx.require((row['name'],row['production_path'],row['mutation_before'],row['mutation_after'],row['test_methods']) == (name,path,old,new,[test_name]), 'MUTATIONS', 'Mutation identity mismatch.')
        cx.require(row['semantic_assertion_kill'] is True and row['returncode'] == 1 and 'AssertionError' in row['output'] and 'ERROR:' not in row['output'], 'MUTATIONS', 'Expected semantic assertion did not kill mutation.')
    cx.require(report['demonstration_error'] is None, 'DEMO', 'Demonstration failed.')
    verify_demo(report['demonstrations'])
    # This small seal is mandatory; deleting it is not a way to skip the guard.
    seal = read('evidence_binding.json')
    cx.schema(seal,'evidence-binding',{'conformance_sha256','source_snapshot_sha256','evidence_sha'})
    for name,key in [('conformance.json','conformance_sha256'),('source_snapshot.json','source_snapshot_sha256')]:
        raw=(PKG/name).read_bytes()
        cx.require(cx.sha(raw)==seal[key],'EVIDENCE_BINDING','Committed evidence bytes changed.')
        pinned=subprocess.check_output(['git','show',seal['evidence_sha']+':'+REL+'/'+name],cwd=ROOT)
        cx.require(pinned==raw,'EVIDENCE_BINDING','Evidence introduction differs from sealed bytes.')
        introduced=git('log','--diff-filter=A','--format=%H','--',REL+'/'+name).splitlines()
        cx.require(introduced == [seal['evidence_sha']],'EVIDENCE_BINDING','Evidence must bind its actual unique introduction.')
    cx.require(subprocess.run(['git','merge-base','--is-ancestor',snapshot['source_sha'],seal['evidence_sha']],cwd=ROOT).returncode == 0,
               'CHRONOLOGY','Evidence must descend from pinned source.')
    return report['disposition']


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['pin-source','emit','check'])
    command=parser.parse_args().command
    if command=='pin-source':pin_source()
    else:print(emit() if command=='emit' else check())
