"""Eight frozen semantic mutations, executed with the existing isolated runner."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from Discovery import nist_2026_paired_torque_feasibility as n

SELF = 'Discovery/' + n.STEM + '_mutations.py'
TEST = 'tests/test_' + n.STEM + '_mutations.py'
BEHAVIOR_TEST = 'tests/test_' + n.STEM + '.py'
PREFIX = 'tests.test_' + n.STEM + '_mutations.PairedMutationBehaviorTests.'
OUTPUT = n.DIRECTORY / (n.STEM + '_mutations_v1.json')
COPY_PATHS = (n.MODULE, SELF, TEST, BEHAVIOR_TEST, n.PREREGISTRATION_PATH.as_posix(),
              n.ATTESTATION.as_posix(), 'Discovery/__init__.py', *n.HELPERS, 'Discovery/mutation_test_runner.py')
SOURCE_PATHS = tuple(dict.fromkeys((*n.SOURCE_PATHS, *COPY_PATHS)))
IMPORTS = {'Discovery.' + n.STEM: n.MODULE, 'Discovery.' + n.STEM + '_mutations': SELF,
           'tests.test_' + n.STEM: BEHAVIOR_TEST, 'tests.test_' + n.STEM + '_mutations': TEST, 'Discovery.mutation_test_runner': 'Discovery/mutation_test_runner.py'}


class MutationEvidenceError(ValueError):
    pass


def case(ident, old, new, test, index=None, expected='KILLED'):
    return {'id': ident, 'category': 'production' if index is not None else 'calibration',
            'requirement_index': index, 'path': n.MODULE, 'old': old, 'new': new,
            'tests': [PREFIX + test], 'expected': expected}


def frozen_cases():
    p = n._json((n.ROOT/n.PREREGISTRATION_PATH).read_bytes())
    production = tuple(case(row['id'], row['old'], row['new'], row['test'].rsplit('.',1)[1], i)
                       for i,row in enumerate(p['mutation_requirements']))
    return (*production,
            case('faulty_scale_calibration', 'return tuple(tuple(v*rational(scale) for v in row) for row in matrix(M))',
                 'return tuple(tuple(-v*rational(scale) for v in row) for row in matrix(M))', 'test_faulty_calibration'),
            case('equivalent_projection_control', 'return mm(mm(P, V), transpose(P))',
                 'return tuple(mm(mm(P, V), transpose(P)))', 'test_equivalent_control', expected='SURVIVED'))


CASES = frozen_cases()


def definitions():
    baseline = {'id': 'unmutated_baseline', 'category': 'baseline', 'requirement_index': None,
                'path': n.MODULE, 'tests': sorted({t for c in CASES for t in c['tests']}), 'expected': 'SURVIVED'}
    return (baseline, *CASES)


def validate_definitions(source, protocol):
    production = [c for c in CASES if c['category'] == 'production']
    if len(production) != 8 or len(protocol['mutation_requirements']) != 8:
        raise MutationEvidenceError('exactly eight production mutations required')
    for i, (c, req) in enumerate(zip(production, protocol['mutation_requirements'])):
        if c['id'] != req['id'] or c['tests'] != [req['test']] or c['requirement_index'] != i or c['old'] != req['old'] or c['new'] != req['new']:
            raise MutationEvidenceError('frozen mutation mapping differs')
    for c in CASES:
        if source.count(c['old']) != 1 or c['old'] == c['new']:
            raise MutationEvidenceError('ambiguous or unchanged mutation patch: ' + c['id'])
    if len({n.digest(source.replace(c['old'],c['new']).encode()) for c in CASES}) != len(CASES):
        raise MutationEvidenceError('mutant byte images are not distinct')


def assess(e, tests):
    if (not isinstance(e, dict) or e.get('runner_status') != 'completed'
        or type(e.get('tests_run')) is not int or e['tests_run'] != len(tests)
        or e.get('error_tests') != [] or e.get('skipped_tests') != []
        or not isinstance(e.get('failing_tests'), list)
        or any(t not in tests for t in e['failing_tests'])
        or len(set(e['failing_tests'])) != len(e['failing_tests'])
        or e.get('successful') is not (not e['failing_tests'])):
        raise MutationEvidenceError('infrastructure, errors, skips, or undesignated failures earn no credit')
    for phase in ('validated_imports_before', 'validated_imports_after'):
        if not isinstance(e.get(phase),dict) or any(e[phase].get(k) != v for k,v in IMPORTS.items()):
            raise MutationEvidenceError('isolated import binding missing')
    return 'KILLED' if e['failing_tests'] else 'SURVIVED'


def execute(root, c):
    with TemporaryDirectory(prefix='nist-paired-mutant-') as temp:
        target = Path(temp)
        for path in COPY_PATHS:
            dest = target / path; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, dest)
        (target/'tests/__init__.py').write_text('')
        source = (target / n.MODULE).read_text()
        if c['category'] != 'baseline':
            if source.count(c['old']) != 1:
                raise MutationEvidenceError('patch not unique')
            source = source.replace(c['old'], c['new'])
            (target / n.MODULE).write_text(source)
        bootstrap = "import sys;sys.path.insert(0,sys.argv.pop(1));from Discovery import mutation_test_runner;mutation_test_runner.main()"
        cmd = [sys.executable, '-I', '-B', '-c', bootstrap, str(target), '--mutation-root', str(target)]
        for module in IMPORTS:
            cmd += ['--required-module', module]
        cmd += c['tests']
        process = subprocess.run(cmd, cwd=target, capture_output=True, text=True, timeout=45)
        if process.returncode:
            raise MutationEvidenceError('runner process failed')
        evidence = n._json(process.stdout)
        outcome = assess(evidence, c['tests'])
        stable = {k:v for k,v in evidence.items() if k != 'test_output'}
        return {**{k:c[k] for k in ('id','category','requirement_index','path','tests','expected')},
                'applied_source_sha256': n.digest(source.encode()), 'outcome': outcome, 'evidence': stable}


def validate_records(records, source):
    if not isinstance(records,list) or len(records) != len(definitions()):
        raise MutationEvidenceError('incomplete records')
    for c,r in zip(definitions(),records):
        if any(r.get(k) != c[k] for k in ('id','category','requirement_index','path','tests','expected')):
            raise MutationEvidenceError('record definition mismatch')
        image = source if c['category'] == 'baseline' else source.replace(c['old'], c['new'])
        if r.get('applied_source_sha256') != n.digest(image.encode()):
            raise MutationEvidenceError('mutant source digest mismatch')
        outcome = assess(r.get('evidence'), c['tests'])
        if outcome != c['expected'] or r.get('outcome') != outcome:
            raise MutationEvidenceError('surviving mutant or failed control: ' + c['id'])


def envelope(root, records, p, source):
    validate_definitions(source,p); validate_records(records,source)
    snapshot = n.source_snapshot(root,SOURCE_PATHS)
    for path,expected in p['dependencies']['code_reuse'].items():
        if snapshot['source_sha256'].get(path) != expected:
            raise MutationEvidenceError('verification helper dependency differs')
    return {'artifact_id':n.STEM+'_mutations_v1','preregistration_sha256':n.FREEZE_DIGEST,
            'anchor':n.ANCHOR,'source_snapshot':snapshot,'requirements':p['mutation_requirements'],
            'first_introductions':n.verify_implementation_chronology(root, (n.MODULE,n.ATTESTATION.as_posix(),n.NOTES[1],n.NOTES[2],SELF,TEST,BEHAVIOR_TEST)),
            'definitions_sha256':n.digest(n.serialize_artifact(definitions()).encode()),
            'production_count':8,'production_killed':8,'family_status':'valid','baseline_survived':True,
            'faulty_calibration_killed':True,'equivalent_control_survived':True,
            'kill_rule':'Designated semantic assertion only; errors, runtime/import/syntax/history/digest failures and skips earn no credit.',
            'review_qualification':p['review_qualification'],'records':records}


def build_artifact(root=n.ROOT):
    p=n.verify_preregistration(root);n.verify_implementation_chronology(root)
    source=(root/n.MODULE).read_text();validate_definitions(source,p)
    n.source_snapshot(root,SOURCE_PATHS)  # Commit sources before executing the family.
    records=[execute(root,c) for c in definitions()]
    return envelope(root,records,p,source)


def check_artifact(root=n.ROOT):
    p=n.verify_preregistration(root);n.verify_implementation_chronology(root)
    source=(root/n.MODULE).read_text();raw=(root/OUTPUT).read_bytes();artifact=n._json(raw)
    expected=envelope(root,artifact.get('records'),p,source)
    if artifact != expected or raw != n.serialize_artifact(expected).encode():
        raise MutationEvidenceError('mutation evidence stale or noncanonical')
    source=expected['source_snapshot']['source_commit_sha']
    artifact_commit=n.source_snapshot(root,(OUTPUT.as_posix(),))['source_commit_sha']
    if source==artifact_commit:raise MutationEvidenceError('mutation artifact must follow committed source')
    n.git(root,'merge-base','--is-ancestor',source,artifact_commit)
    return expected


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args(argv)
    try:
        if args.check:
            check_artifact();print('NIST paired-torque mutation evidence verified: 8/8; valid controls')
        else:
            (n.ROOT/OUTPUT).write_text(n.serialize_artifact(build_artifact()))
    except (MutationEvidenceError,n.FeasibilityError,n.SourceVerificationError,OSError,KeyError,TypeError,ValueError,subprocess.SubprocessError) as error:
        print('torque_mutation_evidence_error: '+str(error),file=sys.stderr);raise SystemExit(1) from error


if __name__ == '__main__':
    main()
