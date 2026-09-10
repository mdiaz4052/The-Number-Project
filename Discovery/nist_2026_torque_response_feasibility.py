"""NIST operational torque response: exact reported-input feasibility, no data fit."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import verify_committed_source_state, SourceVerificationError

ROOT = Path(__file__).resolve().parents[1]
STEM = 'nist_2026_torque_response_feasibility'
DIRECTORY = Path('Experiments/GMeasurements')
PREREGISTRATION_PATH = DIRECTORY / (STEM + '_preregistration_v1.json')
ATTESTATION = DIRECTORY / (STEM + '_source_attestation_v1.json')
OUTPUT = DIRECTORY / (STEM + '_v1.json')
MODULE = 'Discovery/' + STEM + '.py'
HELPERS = ('Discovery/preregistration_history.py', 'Discovery/source_history.py')
NOTES = ('Notes/NIST2026TorqueResponseFeasibilitySpecification.md', 'Notes/NIST2026TorqueResponseFeasibility.md')
BASE = '81169a9d54e1540d82b4ad14ffa7dcd6d4fd3c77'
FREEZE = 'daf900f5fdac06d47b13c9de9272b9e734245cd6'
FREEZE_DIGEST = '44f56d0e889474765910439329f81896db61df75d48d7a7e379ea233ff2802bb'
ANCHOR = {'pr_number': 50, 'created_at': '2026-09-10T01:49:24Z', 'head_sha_at_creation': FREEZE,
          'url': 'https://github.com/mdiaz4052/The-Number-Project/pull/50', 'provider': 'GitHub'}
# The nonnumeric contract is supported exactly; changed policy must fail, not go unused.
SUPPORTED_POLICY_DIGEST = '9e7da9f29985d85351a35e5126c1b676ca93bb790bd37709c6c6e5238d595b2c'
SOURCE_PATHS = (MODULE, *HELPERS, *NOTES, PREREGISTRATION_PATH.as_posix(), ATTESTATION.as_posix())


class FeasibilityError(ValueError):
    """A contract/evidence error is never a scientific NO-GO."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def serialize_artifact(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + '\n'


def _json(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise FeasibilityError('duplicate JSON key: ' + k)
            result[k] = v
        return result
    def invalid(value):
        raise FeasibilityError('nonfinite JSON: ' + value)
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            invalid(value)
        return parsed
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite_float)


def rational(value):
    if isinstance(value, bool) or isinstance(value, float) or not isinstance(value, (str, int, F)):
        raise FeasibilityError('finite exact rational input required')
    try:
        return F(value)
    except (ValueError, ZeroDivisionError) as error:
        raise FeasibilityError('invalid finite rational input') from error


def record(value):
    value = rational(value)
    return {'numerator': value.numerator, 'denominator': value.denominator}


def records(values):
    return [record(v) for v in values]


def validate_protocol(p):
    if not isinstance(p, dict):
        raise FeasibilityError('protocol object required')
    fixed = copy.deepcopy(p)
    projection = fixed.pop('permitted_input_projection', None)
    fixed.pop('excluded_context', None)
    if digest(serialize_artifact(fixed).encode()) != SUPPORTED_POLICY_DIGEST:
        raise FeasibilityError('unsupported frozen policy or missing field')
    if not isinstance(projection, dict) or set(projection) != {'test_mass_g', 'source_masses_g', 'campaigns'}:
        raise FeasibilityError('input projection fields differ')
    if set(projection['source_masses_g']) != {'copper', 'sapphire'}:
        raise FeasibilityError('source mass labels differ')
    values = [projection['test_mass_g'], *projection['source_masses_g'].values()]
    campaigns = projection['campaigns']
    expected = [('copper_0', 'copper'), ('copper_120', 'copper'), ('copper_240', 'copper'), ('sapphire', 'sapphire')]
    if len(campaigns) != 4:
        raise FeasibilityError('four campaign geometries required')
    for row, (name, material) in zip(campaigns, expected):
        if set(row) != {'id', 'material', 'Rs_mm', 'Gamma_table15'} or (row['id'], row['material']) != (name, material):
            raise FeasibilityError('campaign order/geometry contract differs')
        values.extend([row['Rs_mm'], row['Gamma_table15']])
    if any(rational(v) <= 0 for v in values):
        raise FeasibilityError('masses and geometry must be positive')
    return p


def preliminary_response(p):
    """Only mass/geometry fields enter gains; no measured torque or G is read."""
    validate_protocol(p)
    source = p['permitted_input_projection']
    units = p['units']
    mt = rational(source['test_mass_g']) * rational(units['gram_to_kg'])
    result = []
    for k, original in enumerate(source['campaigns']):
        row = original
        ms = rational(source['source_masses_g'][row['material']]) * rational(units['gram_to_kg'])
        radius = rational(row['Rs_mm']) * rational(units['mm_to_m'])
        gamma = rational(row['Gamma_table15'])
        K = 16 * ms * mt * gamma / radius
        for method in range(2):
            i = 2 * k + method
            b = rational(p['intervention']['b'][i])
            response = b / K
            display = response * rational(units['pNm_to_Nm']) / rational(units['U_to_SI_G'])
            result.append({'campaign': original['id'], 'preliminary_label': p['orders']['preliminary'][i],
                           'paper_table15_index': p['orders']['canonical_to_paper_indices'][i],
                           'b': record(b), 'K_SI': record(K), 'd_SI': record(response),
                           'd_U_per_pNm': record(display),
                           'convention': p['mathematical_policy']['preliminary_convention'],
                           'stage': 'preliminary_reported_input_only'})
    return result


def transpose(A):
    return tuple(zip(*A))


def mv(A, x):
    return tuple(sum((rational(a) * rational(b) for a, b in zip(row, x)), F(0)) for row in A)


def mm(A, B):
    return tuple(tuple(sum((a * b for a, b in zip(row, col)), F(0)) for col in transpose(B)) for row in A)


def rref(A):
    if not A or not A[0] or any(len(row) != len(A[0]) for row in A):
        raise FeasibilityError('nonempty rectangular matrix required')
    M = [[rational(x) for x in row] for row in A]
    rank = 0
    for c in range(len(M[0])):
        pivot = next((i for i in range(rank, len(M)) if M[i][c]), None)
        if pivot is None:
            continue
        M[rank], M[pivot] = M[pivot], M[rank]
        div = M[rank][c]
        M[rank] = [x / div for x in M[rank]]
        for i in range(len(M)):
            if i != rank:
                scale = M[i][c]
                M[i] = [x - scale * y for x, y in zip(M[i], M[rank])]
        rank += 1
        if rank == len(M):
            break
    return tuple(tuple(row) for row in M if any(row))


def inverse(A):
    n = len(A)
    if not n or any(len(row) != n for row in A):
        raise FeasibilityError('square matrix required')
    R = rref([list(row) + [F(i == j) for j in range(n)] for i, row in enumerate(A)])
    if len(R) != n or tuple(row[:n] for row in R) != tuple(tuple(F(i == j) for j in range(n)) for i in range(n)):
        raise FeasibilityError('singular normal matrix')
    return tuple(row[n:] for row in R)


def mean_subspace(a):
    if len(a) != 4:
        raise FeasibilityError('four-summary representative required')
    return rref(((F(1),) * 4, tuple(rational(v) for v in a)))


def same_subspace(a, b):
    return mean_subspace(a) == mean_subspace(b)


def affine_response(H, d):
    if any(len(row) != len(d) for row in H):
        raise FeasibilityError('affine response dimension mismatch')
    return mv(H, d)


def posterior_linear_map(X, weights, prior_precision):
    """Synthetic Gaussian posterior mean map; never consumes real outcomes.

    Precision-zero intercepts denote flat priors with a proper posterior when
    the normal matrix is nonsingular. Harmonic priors are separately fixed.
    """
    X = tuple(tuple(rational(v) for v in row) for row in X)
    w = tuple(rational(v) for v in weights)
    lam = tuple(rational(v) for v in prior_precision)
    if not X or len(w) != len(X) or len(lam) != len(X[0]) or any(v <= 0 for v in w) or any(v < 0 for v in lam):
        raise FeasibilityError('invalid synthetic Gaussian design')
    XtW = tuple(tuple(x * z for x, z in zip(row, w)) for row in transpose(X))
    N = mm(XtW, X)
    N = tuple(tuple(v + (lam[i] if i == j else 0) for j, v in enumerate(row)) for i, row in enumerate(N))
    return mm(inverse(N), XtW)


def coupled_response(H, d):
    response = affine_response(H, d)
    return response


def final_copper_response(kind, d, H=None):
    if kind == 'source_identified_global' and H is not None:
        return affine_response(H, d)
    return None  # No unlicensed equal-weight substitution.


def mapping_disposition(p, evidence):
    """Separate evidence errors, restricted mappings, access and identification."""
    validate_protocol(p)
    required = {'essential_access', 'locators', 'stage', 'domain', 'source_authorized',
                'all_admissible_same', 'representatives', 'absolute_identified', 'obstruction'}
    if set(evidence) != required or not evidence['locators'] or not all(isinstance(v, str) and v for v in evidence['locators']):
        raise FeasibilityError('complete stage evidence with positive locators required')
    for key in ('essential_access', 'source_authorized', 'all_admissible_same', 'absolute_identified'):
        if type(evidence[key]) is not bool:
            raise FeasibilityError('evidence flags must be booleans')
    policy = p['decision_policy']
    if not evidence['essential_access']:
        return {'disposition': policy['access'], 'response': None, 'subspace': None, 'contrast_status': 'UNKNOWN'}
    reps = evidence['representatives']
    if evidence['stage'] not in ('preliminary', 'local', 'assumed', 'family', 'final') or evidence['domain'] not in ('global', 'local', 'bounded'):
        raise FeasibilityError('unknown stage/domain')
    if evidence['stage'] != 'final' or evidence['domain'] != 'global':
        return {'disposition': policy['conditional'], 'response': None, 'subspace': None, 'contrast_status': 'NOT_AUTHORIZED'}
    if not reps:
        if not evidence['obstruction'] or evidence['absolute_identified'] or evidence['all_admissible_same']:
            raise FeasibilityError('missing representatives need explicit unresolved evidence')
        return {'disposition': policy['unidentified'], 'response': None, 'subspace': None, 'contrast_status': 'UNKNOWN'}
    subspaces = [mean_subspace(a) for a in reps]
    if any(len(s) == 1 for s in subspaces):
        return {'disposition': policy['unidentified'], 'response': None, 'subspace': None, 'contrast_status': policy['confounded']}
    same = all(same_subspace(reps[0], a) for a in reps)
    if evidence['all_admissible_same'] and not same:
        raise FeasibilityError('claimed universal equivalence contradicted by representatives')
    if not same or not evidence['source_authorized'] or not evidence['all_admissible_same']:
        return {'disposition': policy['unidentified'], 'response': None, 'subspace': None, 'contrast_status': 'UNIDENTIFIED'}
    if evidence['absolute_identified'] and any(a != reps[0] for a in reps):
        raise FeasibilityError('absolute identification contradicted by alternatives')
    return {'disposition': policy['full'] if evidence['absolute_identified'] else policy['shape'],
            'response': records(reps[0]) if evidence['absolute_identified'] else None,
            'subspace': [records(row) for row in subspaces[0]], 'contrast_status': 'RANK_TWO',
            'future_residual_df': 2}


def synthetic_certificate(p):
    s = p['synthetic_policy']
    X = tuple(tuple(rational(v) for v in row) for row in s['design_rows'])
    direction = tuple(rational(v) for v in s['servo_direction'])
    alternatives = []
    for lam in s['prior_precision_alternatives']:
        H = posterior_linear_map(X, s['weights'], lam)
        response = coupled_response(H, direction)
        a = response[:2] + tuple(rational(v) for v in s['sapphire_direction'])
        alternatives.append({'prior_precision': records(lam), 'posterior_parameter_response': records(response),
                             'synthetic_four_summary_response': records(a),
                             'subspace': [records(row) for row in mean_subspace(a)]})
    different = alternatives[0]['subspace'] != alternatives[1]['subspace']
    return {'classification': 'SYNTHETIC_CONTRACT_COMPLETIONS_ONLY', 'alternatives': alternatives,
            'different_mean_subspaces': different,
            'constraints_satisfied': ['shared sine/cosine nuisance at three clockings', 'two method intercepts',
                                     'posterior means', 'fixed Gaussian likelihood for one synthetic error design',
                                     'fixed priors; no observed outcomes used to choose them'],
            'limits': 'Completes the published qualitative model on synthetic inputs; does not match or reproduce any NIST numerical posterior, plot, covariance, or final value.'}


def result_from_inputs(p, attestation):
    validate_protocol(p)
    expected = {'anchor': ANCHOR, 'source_access': p['corpus']['source_access'],
                'permitted_input_projection': p['permitted_input_projection'],
                'evidence_inventory': p['evidence_inventory'],
                'specification_authorship': p['prior_knowledge']['specification_authorship'],
                'audit_context': 'Current last independent audit #46; #47-49 provisionally merged. E-001 excluded. Routed DM detail searches returned no directly relevant detail files; Current supplies routing. No Claude-owned item closed.'}
    if attestation != expected:
        raise FeasibilityError('source attestation differs from frozen projection/access/anchor')
    rows = []
    for category, item in p['evidence_inventory'].items():
        if not item['locator'] or not item['supplies'] or not item['unspecified']:
            raise FeasibilityError('stage evidence needs positive description and bounded absence')
        unresolved = category in ('copper', 'sapphire')
        rows.append({'category': category, 'source': p['corpus']['doi'], **item,
                     'absolute_response_relevance': 'unresolved summary functional' if unresolved else 'supports declared preliminary convention or boundary',
                     'mean_subspace_relevance': 'no universal equivariance contract' if unresolved else 'does not alone authorize final subspace',
                     'stage_disposition': 'UNIDENTIFIED_FROM_REVIEWED_PASSAGES' if unresolved else 'BOUNDED_SOURCE_SUPPORT'})
    preliminary = preliminary_response(p)
    d = tuple(F(row['d_SI']['numerator'], row['d_SI']['denominator']) for row in preliminary)
    copper = final_copper_response('unidentified_posterior', d[:6])
    if copper is not None:
        raise FeasibilityError('unlicensed copper final mapping')
    evidence = {'essential_access': not p['corpus']['known_essential_unreviewed_material'],
                'locators': [p['evidence_inventory'][k]['locator'] for k in ('copper', 'sapphire')],
                'stage': 'final', 'domain': 'global', 'source_authorized': False,
                'all_admissible_same': False, 'representatives': [], 'absolute_identified': False,
                'obstruction': 'The reviewed copper posterior and sapphire summary descriptions do not specify an aggregation functional or prove the required directional equivariance. Unequal campaign gains preclude treating the injected servo direction as a uniform intercept translation.'}
    disposition = mapping_disposition(p, evidence)
    synthetic = synthetic_certificate(p)
    if not synthetic['different_mean_subspaces']:
        raise FeasibilityError('synthetic alternative certificate failed its algebraic obligation')
    return {'intervention': p['intervention'], 'units': p['units'], 'orders': p['orders'],
            'permitted_input_projection': p['permitted_input_projection'], 'preliminary_response': preliminary,
            'preliminary_status': 'AVAILABLE_TABLE15_REPORTED_CONVERSION_ONLY',
            'aggregation_findings': rows, 'final_mapping_evidence': evidence,
            'identification': disposition, 'synthetic_certificate': synthetic,
            'limitations': [p['mathematical_policy']['precision'], p['corpus']['associated_material_check'],
                            'No physical DC torque, cause, unbiased common mean, or sampling distribution identified.',
                            'No global impossibility claim; obtain copper likelihood/prior or a directional-equivariance proof and sapphire summary map.',
                            'The equation-(64) consensus NO-GO is neither an input nor a blocker for this earlier stage.'],
            'prohibited_action_flags': {k: v for k, v in p['constraints'].items() if k != 'prohibited'},
            'review_qualification': p['review_qualification']}


def git(root, *args):
    completed = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True)
    return completed.stdout


def verify_preregistration(root=ROOT):
    raw = verify_preregistration_freeze(root, baseline=BASE, commit=FREEZE,
                                       path=PREREGISTRATION_PATH.as_posix(), sha256=FREEZE_DIGEST)
    p = _json(raw)
    validate_protocol(p)
    return p


def verify_implementation_chronology(root=ROOT):
    # Full-history path additions are candidates; first-introduction predicates
    # are checked against all parents. --full-history avoids path simplification.
    found = {}
    for path in (MODULE, ATTESTATION.as_posix(), NOTES[1]):
        candidates = git(root, 'log', '--full-history', '--diff-filter=A', '--format=%H', '--', path).decode().splitlines()
        true_additions = []
        for sha in dict.fromkeys(candidates):
            parents = git(root, 'rev-list', '--parents', '-n', '1', sha).decode().split()[1:]
            if not any(subprocess.run(['git', '-C', str(root), 'cat-file', '-e', parent + ':' + path], capture_output=True).returncode == 0 for parent in parents):
                true_additions.append(sha)
        if len(true_additions) != 1:
            raise FeasibilityError('unique full-history first introduction required: ' + path)
        sha = true_additions[0]
        git(root, 'merge-base', '--is-ancestor', FREEZE, sha)
        dates = git(root, 'show', '-s', '--format=%aI%n%cI', sha).decode().splitlines()
        if any(datetime.fromisoformat(t) <= datetime.fromisoformat(ANCHOR['created_at'].replace('Z', '+00:00')) for t in dates):
            raise FeasibilityError('implementation introduction predates draft anchor')
        found[path] = sha
    freeze_time = git(root, 'show', '-s', '--format=%cI', FREEZE).decode().strip()
    if datetime.fromisoformat(freeze_time) > datetime.fromisoformat(ANCHOR['created_at'].replace('Z', '+00:00')):
        raise FeasibilityError('freeze postdates draft anchor')
    return found


def source_snapshot(root, paths=SOURCE_PATHS):
    # Latest commit touching result-driving paths (full history), not current HEAD.
    sha = git(root, 'log', '--full-history', '-1', '--format=%H', '--', *paths).decode().strip()
    verify_committed_source_state(root, sha, source_paths=paths, artifact_label=STEM)
    hashes = {}
    for path in paths:
        raw = (root / path).read_bytes()
        if raw != git(root, 'show', sha + ':' + path):
            raise FeasibilityError('source blob/current bytes differ: ' + path)
        hashes[path] = digest(raw)
    return {'source_commit_sha': sha, 'source_sha256': hashes}


def build_artifact(root=ROOT):
    p = verify_preregistration(root)
    chronology = verify_implementation_chronology(root)
    snapshot = source_snapshot(root)
    for path in HELPERS:
        if snapshot['source_sha256'][path] != p['dependencies']['code_reuse'][path]:
            raise FeasibilityError('helper dependency pin differs')
    attestation = _json((root / ATTESTATION).read_bytes())
    result = result_from_inputs(p, attestation)
    return {'schema_version': p['schema_version'], 'protocol_id': p['experiment_id'],
            'objective': p['objective'], 'source_identity': p['corpus'],
            'provenance': {'base': BASE, 'freeze_commit': FREEZE, 'freeze_sha256': FREEZE_DIGEST,
                           'anchor': ANCHOR, 'first_introductions': chronology, **snapshot},
            'prior_knowledge': p['prior_knowledge'], 'outcome_blind': p['outcome_blind'],
            'dependencies': p['dependencies'], 'mathematical_policy': p['mathematical_policy'],
            'decision_policy': p['decision_policy'], 'validation_contract': {
                key: p[key] for key in ('focused_requirements', 'mutation_requirements', 'planned_surfaces', 'acceptance_criteria')},
            'excluded_numerical_fields': p['constraints']['prohibited'], **result}


def check_artifact(root=ROOT):
    expected = build_artifact(root)
    raw = (root / OUTPUT).read_bytes()
    if _json(raw) != expected or raw != serialize_artifact(expected).encode():
        raise FeasibilityError('feasibility artifact stale or noncanonical')
    source = expected['provenance']['source_commit_sha']
    additions = git(root, 'log', '--full-history', '-1', '--format=%H', '--', OUTPUT.as_posix()).decode().splitlines()
    if not additions or any(sha == source for sha in additions):
        raise FeasibilityError('artifact must be committed after its source snapshot')
    for sha in additions:
        git(root, 'merge-base', '--is-ancestor', source, sha)
    return expected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.check:
            result = check_artifact()
            print('NIST torque response feasibility verified: ' + result['identification']['disposition'])
        else:
            result = build_artifact()
            (ROOT / OUTPUT).write_text(serialize_artifact(result))
    except (FeasibilityError, SourceVerificationError, OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as error:
        print('torque_response_contract_error: ' + str(error), file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == '__main__':
    main()
