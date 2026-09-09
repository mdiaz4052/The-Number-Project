"""Exact restricted-mean diagnostics for four already-seen NIST summaries."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from Discovery.nist_2026_n4_experimental_estimator import solve_exact, determinant, linear_enclosure
from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import SourceVerificationError

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path('Experiments/GMeasurements')
NAME = 'nist_2026_configuration_models'
PREREGISTRATION_PATH = DIRECTORY / (NAME + '_preregistration_v1.json')
ATTESTATION = DIRECTORY / (NAME + '_source_attestation_v1.json')
OUTPUT = DIRECTORY / (NAME + '_v1.json')
MUTATION_OUTPUT = DIRECTORY / (NAME + '_mutations_v1.json')
BASELINE = '61b7b2a0b0136b4859c52a56a8ab8a501284f244'
PREREGISTRATION_COMMIT = '9b15de44f1fef889ae8744e4e7e4e4c4b60a12b0'
PREREGISTRATION_SHA256 = 'e19a32c3f6c6ed190a7c6593b77a37b1d44b1b6f586734489e9c30c742fa6a2d'
EXTERNAL_ANCHOR = {'event': 'draft_pull_request_created',
                   'url': 'https://github.com/mdiaz4052/The-Number-Project/pull/49',
                   'created_at': '2026-09-09T14:29:55Z',
                   'preregistration_commit_sha': PREREGISTRATION_COMMIT,
                   'outcome_blind': False}
MODULE = 'Discovery/nist_2026_configuration_models.py'
HELPERS = ('Discovery/__init__.py', 'Discovery/nist_2026_n4_experimental_estimator.py',
           'Discovery/preregistration_history.py', 'Discovery/source_history.py')
NOTES = ('Notes/NIST2026ConfigurationModelsSpecification.md', 'Notes/NIST2026ConfigurationModels.md')
PROVISIONAL = 'PROVISIONAL — INDEPENDENT AUDIT PENDING'


class DiagnosticError(ValueError):
    """A computational/contract failure, never a scientific non-rejection."""


def require(condition, message):
    if not condition:
        raise DiagnosticError(message)


def serialize_artifact(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _json(data):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    def invalid(value):
        raise DiagnosticError('nonfinite JSON constant: ' + value)
    try:
        return json.loads(data, object_pairs_hook=unique, parse_constant=invalid)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise DiagnosticError('malformed JSON') from error


def rational(value):
    require(isinstance(value, dict) and set(value) == {'numerator', 'denominator'}, 'rational schema')
    n, d = value['numerator'], value['denominator']
    require(isinstance(n, str) and re.fullmatch(r'-?(0|[1-9][0-9]*)', n) is not None, 'rational numerator')
    require(isinstance(d, str) and re.fullmatch(r'[1-9][0-9]*', d) is not None, 'rational denominator')
    result = F(int(n), int(d))
    require(record(result) == value, 'rational must be canonical')
    return result


def decimal_rational(value):
    require(isinstance(value, str) and re.fullmatch(r'-?[0-9]+(?:\.[0-9]+)?', value) is not None,
            'finite decimal string required')
    return F(value)


def record(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def exact_tree(value):
    if isinstance(value, F):
        return record(value)
    if isinstance(value, (tuple, list)):
        return [exact_tree(x) for x in value]
    if isinstance(value, dict):
        return {k: exact_tree(v) for k, v in value.items()}
    return value


def decimal_text(value):
    with localcontext() as ctx:
        ctx.prec = 60
        return format(Decimal(value.numerator) / Decimal(value.denominator), '.18g')


def at(value, path):
    try:
        for key in path:
            value = value[key]
        return value
    except (KeyError, IndexError, TypeError) as error:
        raise DiagnosticError('missing frozen field path') from error


def interval(value):
    require(isinstance(value, dict) and set(value) == {'low', 'high'}, 'interval schema')
    result = rational(value['low']), rational(value['high'])
    require(result[0] <= result[1], 'reversed interval')
    return result


def matrix(value):
    require(isinstance(value, list) and value and all(isinstance(r, list) for r in value), 'matrix schema')
    return tuple(tuple(rational(x) for x in row) for row in value)


def check_covariance(V):
    k = len(V)
    require(k > 0 and all(len(row) == k for row in V), 'covariance dimension')
    require(all(isinstance(x, (F, int)) and not isinstance(x, bool) for row in V for x in row),
            'exact covariance required')
    require(all(V[i][j] == V[j][i] for i in range(k) for j in range(k)), 'covariance symmetry')
    require(all(determinant([list(row[:s]) for row in V[:s]]) > 0 for s in range(1, k + 1)),
            'covariance positive definiteness')


def inverse_matrix(V):
    check_covariance(V)
    k = len(V)
    columns = [solve_exact([list(row) for row in V], [F(i == j) for i in range(k)]) for j in range(k)]
    return tuple(tuple(columns[j][i] for j in range(k)) for i in range(k))


def dot(x, y):
    require(len(x) == len(y), 'dot dimensions')
    return sum((a * b for a, b in zip(x, y)), F(0))


def mv(V, x):
    return tuple(dot(row, x) for row in V)


def quadratic(V, x):
    return dot(x, mv(V, x))


def transpose(M):
    require(M and all(len(row) == len(M[0]) for row in M), 'rectangular matrix required')
    return tuple(zip(*M))


def mm(A, B):
    return tuple(tuple(dot(row, col) for col in transpose(B)) for row in A)


def subtract(A, B):
    require(len(A) == len(B) and all(len(a) == len(b) for a, b in zip(A, B)), 'matrix dimensions')
    return tuple(tuple(x - y for x, y in zip(a, b)) for a, b in zip(A, B))


def identity(n):
    return tuple(tuple(F(i == j) for j in range(n)) for i in range(n))


def check_exact_vector(x, size):
    require(len(x) == size and all(isinstance(z, (F, int)) and not isinstance(z, bool) for z in x),
            'exact vector and dimensions required')


def contrast_geometry(protocol):
    names = tuple(row['name'] for row in protocol['contrasts'])
    L = tuple(tuple(F(z) for z in row['row']) for row in protocol['contrasts'])
    require(len(set(names)) == len(L) == 3, 'three named contrasts required')
    for row in L:
        check_exact_vector(row, 4)
        require(sum(row) == 0, 'contrasts must annihilate common mode')
    check_covariance(mm(L, transpose(L)))  # Gram matrix proves row rank three.
    return names, L


def selected_rows(names, L, model):
    return tuple(L[names.index(name)] for name in model['constraints'])


def model_df(model, R):
    df = model['residual_df']
    require(type(df) is int and df == len(R) and 1 <= df <= 3, 'residual df must equal constraint rank')
    return df


def cutoff(protocol, df):
    return decimal_rational(protocol['calibration']['cutoffs_by_df'][str(df)])


def constrained_covariance(R, V):
    return mm(mm(R, V), transpose(R))


def contrast_state(x, V, R):
    check_covariance(V)
    check_exact_vector(x, len(V))
    require(R and all(len(row) == len(x) for row in R), 'constraint dimensions')
    for row in R:
        check_exact_vector(row, len(x))
        require(sum(row) == 0, 'common mean must remain free')
    C = constrained_covariance(R, V)
    inverse = inverse_matrix(C)  # Positive definite iff R has full row rank.
    y = mv(R, x)
    A = mm(mm(transpose(R), inverse), R)
    Q = dot(y, mv(inverse, y))
    require(Q >= 0 and quadratic(A, x) == Q, 'nonnegative exact residual identity')
    return {'y': y, 'C': C, 'A': A, 'Q': Q, 'rank': len(R)}


def gls_profile(x, V, X):
    """Independent mean-space formula; nuisance coefficients are profiled, not fixed."""
    W = inverse_matrix(V)
    XtW = mm(transpose(X), W)
    normal = mm(XtW, X)
    beta = mv(inverse_matrix(normal), mv(XtW, x))
    residual = tuple(z - fit for z, fit in zip(x, mv(X, beta)))
    return quadratic(W, residual)


def certify_display(A, x, h):
    check_exact_vector(h, len(x))
    require(all(z >= 0 for z in h), 'display half widths must be nonnegative')
    Q = quadratic(A, x)
    B = 2 * sum((w * abs(z) for w, z in zip(h, mv(A, x))), F(0))
    E = sum((h[i] * h[j] * abs(A[i][j]) for i in range(len(h)) for j in range(len(h))), F(0))
    return {'B': B, 'E': E, 'bounds': (max(F(0), Q - B), Q + B + E)}


def classify_display(bounds, c, policy):
    low, high = bounds
    require(F(0) <= low <= high and c > 0, 'ordered nonnegative bounds and positive cutoff')
    if low > c:
        return policy['display_flagged']
    if high <= c:
        return policy['display_not_flagged']
    return policy['display_unresolved']


def midpoint_status(Q, c, policy):
    return policy['midpoint_flagged'] if Q > c else policy['midpoint_not_flagged']


def saturated_control(protocol):
    """Synthetic zero vector with identity covariance and four free mean columns."""
    q = gls_profile((F(0),) * 4, identity(4), identity(4))
    require(q == 0, 'synthetic saturated identity')
    return {'role': 'synthetic_control_only', 'residual_df': 0, 'Q': q,
            'status': protocol['mathematical_policy']['saturated'], 'scientific_acceptance': False}


@dataclass(frozen=True)
class Inputs:
    x: tuple
    V: tuple
    cells: tuple
    order: tuple


def select_authorized(source, path):
    return at(source, path)


def project_records(protocol, records):
    """Numerical selector boundary is independent of whole-container hash validation."""
    require(set(records) == set(UPSTREAM_PATHS), 'upstream record inventory')
    projected = {}
    for role, spec in protocol['upstream_records'].items():
        selected = {}
        for name, entry in spec['fields'].items():
            value = select_authorized(records[role], entry['path'])
            require(value == entry['value'], 'frozen selected field changed: ' + role + '.' + name)
            selected[name] = value
        projected[role] = selected
    e = projected['certificate']
    x = tuple(map(rational, e['x']))
    V = matrix(e['V'])  # Inherited V is the numerical authority; never replace it.
    cells = tuple(map(interval, e['cells']))
    s = tuple(map(rational, e['s']))
    rho = matrix(e['rho'])
    require(e['order'] == protocol['input_order'] and len(x) == len(cells) == len(s) == 4, 'input order/dimensions')
    check_covariance(V)
    require(all(lo <= z <= hi and (lo + hi) / 2 == z for z, (lo, hi) in zip(x, cells)), 'display midpoints')
    frozen = projected['protocol']['inputs']
    source = projected['source']
    require(frozen['order'] == source['order'] == e['order'], 'source configuration order')
    for i in range(4):
        row = frozen['measurements'][i]
        require(row['id'] == source[f'row_{i}_id'] == e['order'][i], 'source row identity')
        require(x[i] == decimal_rational(row['G_decimal_in_1e_minus_11_units']) ==
                decimal_rational(source[f'row_{i}_G_decimal_in_1e_minus_11_units']), 'source central value')
        require(s[i] > 0 and s[i] == decimal_rational(row['relative_standard_uncertainty_ppm']) ==
                decimal_rational(source['s'][i]), 'precise uncertainty cross-check')
        require(cells[i][1] - cells[i][0] == F(1, 10**row['printed_decimal_places']), 'display cell precision')
        for j in range(4):
            require(rho[i][j] == decimal_rational(frozen['correlation_matrix'][i][j]) ==
                    decimal_rational(source['rho'][i][j]), 'correlation cross-check')
            require(V[i][j] == rho[i][j] * (x[i] * s[i] / 10**6) * (x[j] * s[j] / 10**6),
                    'inherited absolute covariance cross-check')
    required = projected['protocol']['authorization']
    for key, value in required.items():
        require(projected['authorization']['decision'][key] == e['authorization']['decisions'][key] == value,
                'authorization disposition changed')
    return Inputs(x, V, cells, tuple(e['order']))


def evaluate(protocol, inputs):
    names, L = contrast_geometry(protocol)
    x, V, cells = inputs.x, inputs.V, inputs.cells
    require(tuple(protocol['input_order']) == inputs.order, 'ordered input contract')
    h = tuple((hi - lo) / 2 for lo, hi in cells)
    S = constrained_covariance(L, V)
    check_covariance(S)
    d = mv(L, x)
    enclosures = tuple(linear_enclosure(cells, row) for row in L)
    models = []
    for model in protocol['models']:
        R = selected_rows(names, L, model)
        df = model_df(model, R)
        state = contrast_state(x, V, R)
        X = transpose(tuple(tuple(F(z) for z in protocol['allowed_mean_columns'][col])
                            for col in model['allowed_columns']))
        require(mm(R, X) == tuple((F(0),) * len(model['allowed_columns']) for _ in R), 'allowed nullspace')
        require(len(model['allowed_columns']) + df == 4, 'nullspace dimension')
        require(state['Q'] == gls_profile(x, V, X), 'independent GLS profiling identity')
        bound = certify_display(state['A'], x, h)
        c = cutoff(protocol, df)
        models.append({'id': model['id'], 'constraints': model['constraints'], 'residual_df': df,
                       **state, 'cutoff': c, 'display': bound,
                       'midpoint_status': midpoint_status(state['Q'], c, protocol['decision_policy']),
                       'display_status': classify_display(bound['bounds'], c, protocol['decision_policy']),
                       'GLS_identity_verified': True})
    q = {m['id']: m['Q'] for m in models}
    require(q['M0'] >= q['M_method'] >= q['M_additive'] and
            q['M0'] >= q['M_material'] >= q['M_additive'], 'nested residual monotonicity')
    return {'contrasts': {'order': names, 'L': L, 'd': d, 'S': S, 'display_enclosures': enclosures,
                         'independence_assumed': False}, 'models': models,
            'common_mode': {'L_times_one': mv(L, (F(1),) * 4),
                'identity': '(L1)=0 => L(x+a1)=Lx; L(V+t11^T)L^T=LVL^T for t>=0',
                'limit': 'Only exactly equal additive G-unit loadings; unequal sensitivities, multiplicative and time-varying effects remain possible.'},
            'saturated_control': saturated_control(protocol)}


def validate_protocol(p):
    require(isinstance(p, dict) and set(p) == set(SUPPORTED_CONTRACT) | {'upstream_records'}, 'protocol schema')
    # Every fixed choice is declared before implementation, checked here and consumed below.
    for key, value in SUPPORTED_CONTRACT.items():
        require(p[key] == value, 'unsupported frozen contract: ' + key)
    require(p['known_prior_information']['outcome_blind'] is False, 'prior exposure disclosure')
    require(set(p['upstream_records']) == set(UPSTREAM_PATHS), 'upstream roles')
    for role, spec in p['upstream_records'].items():
        require(set(spec) == {'path', 'sha256', 'fields'} and spec['path'] == UPSTREAM_PATHS[role], 'upstream path')
        require(re.fullmatch('[0-9a-f]{64}', spec['sha256']) is not None, 'upstream digest')
        require(set(spec['fields']) == set(SELECTORS[role]), 'authorized field inventory')
        for key, entry in spec['fields'].items():
            require(set(entry) == {'path', 'value'} and entry['path'] == SELECTORS[role][key], 'authorized selector')
    return p


def verify_preregistration(root=ROOT):
    try:
        data = verify_preregistration_freeze(root, baseline=BASELINE, commit=PREREGISTRATION_COMMIT,
            path=PREREGISTRATION_PATH.as_posix(), sha256=PREREGISTRATION_SHA256)
    except SourceVerificationError as error:
        raise DiagnosticError(str(error)) from error
    return validate_protocol(_json(data))


def source_paths(protocol):
    return (MODULE, *HELPERS, *NOTES, PREREGISTRATION_PATH.as_posix(), ATTESTATION.as_posix(),
            *(v['path'] for v in protocol['upstream_records'].values()))


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True).stdout


def verify_implementation_chronology(root=ROOT):
    stamp = lambda s: datetime.fromisoformat(s.replace('Z', '+00:00'))
    anchor = stamp(EXTERNAL_ANCHOR['created_at'])
    stamps = git(root, 'show', '-s', '--format=%aI%x00%cI', PREREGISTRATION_COMMIT).decode().strip().split('\0')
    require(len(stamps) == 2 and all(stamp(t) < anchor for t in stamps), 'freeze precedes anchor')
    for path in (MODULE, ATTESTATION.as_posix(), *NOTES, OUTPUT.as_posix(), MUTATION_OUTPUT.as_posix()):
        events = git(root, 'log', '--full-history', '--diff-filter=A', '--format=%H%x00%aI%x00%cI', '--', path).decode().splitlines()
        if not events:
            require(path in (OUTPUT.as_posix(), MUTATION_OUTPUT.as_posix()), 'source introduction must be committed')
        for event in events:
            sha, authored, committed = event.split('\0')
            require(stamp(authored) > anchor and stamp(committed) > anchor, 'post-anchor source/result introduction')
            git(root, 'merge-base', '--is-ancestor', PREREGISTRATION_COMMIT, sha)


def source_snapshot(root, paths):
    commit = git(root, 'log', '-1', '--format=%H', '--', *paths).decode().strip()
    files = []
    for path in paths:
        data = (root / path).read_bytes()
        require(git(root, 'show', f'{commit}:{path}') == data, 'commit all result-driving source before emission')
        files.append({'path': path, 'sha256': digest(data)})
    return {'source_commit_sha': commit, 'files': files}


def load_records(protocol, root=ROOT):
    records = {}
    for role, spec in protocol['upstream_records'].items():
        data = (root / spec['path']).read_bytes()
        require(digest(data) == spec['sha256'], 'upstream digest changed')
        require(git(root, 'show', f'{BASELINE}:{spec["path"]}') == data, 'upstream baseline bytes changed')
        records[role] = _json(data)
    return records


def expected_attestation(protocol):
    return {'schema_version': 1, 'artifact_id': NAME + '_source_attestation_v1',
            'preregistration_sha256': PREREGISTRATION_SHA256, 'external_anchor': EXTERNAL_ANCHOR,
            'review': protocol['source_review'],
            'preparation_phase': 'input_projection_before_freeze_attestation_serialized_after_anchor',
            'access_attribution': 'Earlier planning inspection attributed explicitly; no new visual or raw-PDF hash claim.'}


def build_artifact(root=ROOT):
    protocol = verify_preregistration(root)
    verify_implementation_chronology(root)
    snapshot = source_snapshot(root, source_paths(protocol))
    require(_json((root / ATTESTATION).read_bytes()) == expected_attestation(protocol), 'source attestation contract')
    inputs = project_records(protocol, load_records(protocol, root))
    result = evaluate(protocol, inputs)
    return {'schema_version': 1, 'artifact_id': protocol['experiment_id'], 'kind': 'restricted_mean_contrast_diagnostics',
            'objective': protocol['objective'], 'unit': protocol['unit'], 'results': exact_tree(result),
            'readability_only': {'contrasts_U': [decimal_text(z) for z in result['contrasts']['d']],
                'contrast_covariance_U_squared': [[decimal_text(z) for z in row] for row in result['contrasts']['S']],
                'contrast_enclosures_U': [[decimal_text(z) for z in row] for row in result['contrasts']['display_enclosures']],
                'models': [{'id': m['id'], 'Q': decimal_text(m['Q']),
                            'display_bound': [decimal_text(z) for z in m['display']['bounds']]} for m in result['models']]},
            'model_inventory': protocol['models'], 'mathematical_policy': protocol['mathematical_policy'],
            'decision_policy': protocol['decision_policy'], 'calibration': protocol['calibration'],
            'claim_limits': protocol['claim_limits'], 'audit_status_at_freeze': protocol['audit_status_at_freeze'],
            'known_prior_information': protocol['known_prior_information'], 'source_review': protocol['source_review'],
            'upstream_pins_and_projections': protocol['upstream_records'],
            'verification_only_context': 'PR #48 NIST baseline is checked in tests, never opened by production; shared data, not additional evidence.',
            'integrity': {'baseline_main_sha': BASELINE, 'preregistration_commit_sha': PREREGISTRATION_COMMIT,
                'preregistration_sha256': PREREGISTRATION_SHA256, 'external_anchor': EXTERNAL_ANCHOR,
                'source_snapshot': snapshot}}


def check_artifact(root=ROOT):
    expected = build_artifact(root)
    data = (root / OUTPUT).read_text()
    require(_json(data) == expected and data == serialize_artifact(expected), 'diagnostic artifact stale or malformed')
    return expected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.check:
            check_artifact()
            print('NIST configuration-model diagnostic verified')
        else:
            (args.output or ROOT / OUTPUT).write_text(serialize_artifact(build_artifact()))
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        print(f'nist_configuration_models_invalid: {error}', file=sys.stderr)
        raise SystemExit(1) from error


# Supported v1 contract copied from the published freeze, not later model choices.
SUPPORTED_CONTRACT = {'allowed_mean_columns': {'common': ['1', '1', '1', '1'],
                          'material': ['1', '1', '0', '0'],
                          'method': ['0', '1', '0', '1']},
 'audit_status_at_freeze': {'current_drive_id': '1flh4pHVdz80ClLZO5IQo2xG63EGWVsN0',
                            'dependency_head': '621f5ddc938bc62273eac42004e56d940ef376fa',
                            'dependency_merge': '4e8acdebc5b03d03d5039c24a73bcc37e44711e2',
                            'direct_scientific_dependency_pr': 47,
                            'handoff_drive_id': '145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd',
                            'last_audited_pr': 46,
                            'routing': 'E-001 outside read/claim closure. DM-073 input diagonals and '
                                       'blockers frozen; DM-070/077 production read closure instrumented; '
                                       'DM-075 full-history chronology; DM-076 frozen-field consumption; '
                                       'DM-078 source limits retained. Prior repair dispositions remain '
                                       'Claude-owned; no IDs assigned or closed. Current and handoff '
                                       'retrieved September 9; no new independent audit.',
                            'status': 'PROVISIONAL — INDEPENDENT AUDIT PENDING'},
 'calibration': {'cutoffs_by_df': {'1': '3.841459', '2': '5.991465', '3': '7.814728'},
                 'joint_error_rate_claim': False,
                 'nominal_alpha': '0.05',
                 'one_three_df_policy': 'inherit prior upward-rounded operational conventions',
                 'separate_diagnostics': True,
                 'tail': 'upper',
                 'two_df_prefreeze_check': {'decision_authority': 'exact operational rational; Decimal check '
                                                                  'is calibration corroboration only',
                                            'method': 'data-free Decimal at 70 digits: 2*ln(20); 5.991464 < '
                                                      '2*ln(20) < 5.991465',
                                            'operational_cutoff': '5.991465',
                                            'quantile_decimal': '5.991464547107981986870447152285081551353203245978056460308015820921932'}},
 'claim_limits': {'conditional_only': True,
                  'no_Bayesian_consensus_reproduction': True,
                  'no_causal_identification': True,
                  'no_composition_dependent_gravity_claim': True,
                  'no_configuration_removal': True,
                  'no_corrected_or_pooled_G': True,
                  'no_equal_torque_inference': True,
                  'no_independent_confirmation': True,
                  'no_joint_familywise_error_rate': True,
                  'no_model_selection_guarantee': True,
                  'no_new_observations': True,
                  'no_newly_discovered_author_missed_effect': True,
                  'no_p_value': True,
                  'no_probability_of_universality': True,
                  'no_variance_inflation': True,
                  'no_winning_model': True},
 'contrasts': [{'meaning': 'copper minus sapphire, averaged over methods',
                'name': 'material',
                'row': ['1/2', '1/2', '-1/2', '-1/2']},
               {'meaning': 'free minus servo, averaged over source materials',
                'name': 'method',
                'row': ['-1/2', '1/2', '-1/2', '1/2']},
               {'meaning': 'copper method gap minus sapphire method gap',
                'name': 'interaction',
                'row': ['-1', '1', '1', '-1']}],
 'decision_policy': {'B': '2*sum_i h_i*abs((A*x)_i)',
                     'E': 'sum_ij h_i*h_j*abs(A_ij)',
                     'bound_interpretation': 'conservative_outer_bounds_not_attained_extrema',
                     'display_flagged': 'FLAGGED_FOR_ALL_DISPLAY_VALUES',
                     'display_not_flagged': 'NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES',
                     'display_unresolved': 'UNRESOLVED_FROM_CERTIFIED_BOUNDS',
                     'equality': 'not_flagged',
                     'flag_rule': 'strictly_greater',
                     'lower': 'max(0,Q-B)',
                     'midpoint_flagged': 'FLAGGED_UNDER_DECLARED_MODEL',
                     'midpoint_not_flagged': 'NOT_FLAGGED_UNDER_DECLARED_MODEL',
                     'unresolved_interpretation': 'does_not_establish_attainable_outcomes_on_both_sides',
                     'upper': 'Q+B+E'},
 'experiment_id': 'nist_2026_configuration_models_v1',
 'input_order': ['copper_servo', 'copper_free', 'sapphire_servo', 'sapphire_free'],
 'intended_base_sha': '61b7b2a0b0136b4859c52a56a8ab8a501284f244',
 'known_prior_information': {'disclosure': 'The four source summaries, PR #48 common-mean Q, and published '
                                           'servo/free offset discussion are known. No new candidate-model '
                                           'statistics were computed before this freeze. The freeze controls '
                                           'subsequent implementation, not historical exposure or hypothesis '
                                           'discovery.',
                             'outcome_blind': False},
 'mathematical_policy': {'A': 'R^T*(R*V*R^T)^-1*R',
                         'Q': '(R*x)^T*(R*V*R^T)^-1*(R*x)',
                         'common_mode': 'L*1=0; x+a*1 and V+t*11^T for t>=0 preserve every contrast '
                                        'diagnostic',
                         'contrast_covariance': 'full_marginal_R_V_R_transpose',
                         'covariance': 'inherited_absolute_V_fixed_at_midpoint',
                         'covariance_assumption': 'fixed_known_working_summary_model',
                         'display': 'central_value_cells_only',
                         'errors': 'contract_or_computation_failure_is_error',
                         'gaussian_null': 'joint_normal_with_mean_in_declared_subspace',
                         'nuisance': 'profile_allowed_mean_subspace',
                         'reference': 'chi_square_rank_R',
                         'saturated': 'NOT_TESTABLE_ZERO_RESIDUAL_DF'},
 'merge_semantics': 'true_merge_commit_only',
 'models': [{'allowed_columns': ['common'],
             'constraints': ['material', 'method', 'interaction'],
             'id': 'M0',
             'residual_df': 3},
            {'allowed_columns': ['common', 'method'],
             'constraints': ['material', 'interaction'],
             'id': 'M_method',
             'residual_df': 2},
            {'allowed_columns': ['common', 'material'],
             'constraints': ['method', 'interaction'],
             'id': 'M_material',
             'residual_df': 2},
            {'allowed_columns': ['common', 'method', 'material'],
             'constraints': ['interaction'],
             'id': 'M_additive',
             'residual_df': 1}],
 'mutation_requirements': [{'id': 'contrast_order',
                            'test': 'tests.test_nist_2026_configuration_models_mutations.ConfigurationMutationBehaviorTests.test_contrast_order'},
                           {'id': 'dropped_covariance',
                            'test': 'tests.test_nist_2026_configuration_models_mutations.ConfigurationMutationBehaviorTests.test_full_covariance'},
                           {'id': 'conditional_covariance',
                            'test': 'tests.test_nist_2026_configuration_models_mutations.ConfigurationMutationBehaviorTests.test_marginal_covariance'},
                           {'id': 'rank_df_policy',
                            'test': 'tests.test_nist_2026_configuration_models_mutations.ConfigurationMutationBehaviorTests.test_rank_df_policy'},
                           {'id': 'forbidden_input_conditioning',
                            'test': 'tests.test_nist_2026_configuration_models_mutations.ConfigurationMutationBehaviorTests.test_forbidden_input_invariance'},
                           {'id': 'saturated_acceptance',
                            'test': 'tests.test_nist_2026_configuration_models_mutations.ConfigurationMutationBehaviorTests.test_saturated_non_test'},
                           {'id': 'unsound_display_classification',
                            'test': 'tests.test_nist_2026_configuration_models_mutations.ConfigurationMutationBehaviorTests.test_display_classification'},
                           {'id': 'frozen_cutoff_policy',
                            'test': 'tests.test_nist_2026_configuration_models_mutations.ConfigurationMutationBehaviorTests.test_frozen_cutoff_policy'}],
 'objective': 'Diagnose residual lack of fit under the four fixed NIST mean restrictions; project-defined '
              'descriptive models only.',
 'planned_surfaces': {'existing': {'.github/workflows/verify.yml': 'exactly two added read-only --check '
                                                                   'entries'},
                      'new': ['Discovery/nist_2026_configuration_models.py',
                              'Discovery/nist_2026_configuration_models_mutations.py',
                              'tests/test_nist_2026_configuration_models.py',
                              'tests/test_nist_2026_configuration_models_mutations.py',
                              'Experiments/GMeasurements/nist_2026_configuration_models_preregistration_v1.json',
                              'Experiments/GMeasurements/nist_2026_configuration_models_source_attestation_v1.json',
                              'Experiments/GMeasurements/nist_2026_configuration_models_v1.json',
                              'Experiments/GMeasurements/nist_2026_configuration_models_mutations_v1.json',
                              'Notes/NIST2026ConfigurationModelsSpecification.md',
                              'Notes/NIST2026ConfigurationModels.md',
                              'Notes/NIST2026ConfigurationModelsMutationValidation.md']},
 'schema_version': 1,
 'serialization': {'decision_arithmetic': 'Fraction only',
                   'exact': 'reduced numerator/denominator decimal strings, positive denominator',
                   'json': 'UTF-8, indent=2, sorted keys, no NaN, terminal newline',
                   'readability_only': 'Decimal 60 digit context; 18 significant digits; never controls a '
                                       'verdict'},
 'source_review': {'doi': '10.1088/1681-7575/ae570f',
                   'independent_audit_claim': False,
                   'labels': 'copper/sapphire are source-mass configurations, not suspension-fibre '
                             'materials; servo/free are electrostatic-servo/free-deflection',
                   'limitations': 'published method offsets have unresolved origin; equal G-unit offsets are '
                                  'not equal parasitic torques; a torque model requires separately '
                                  'authorized mapping through configuration aggregation; source does not '
                                  'endorse these tests',
                   'planning_inspection': 'September 9 planning review as recorded in the supplied '
                                          'specification and existing handoff: GPT obtained and visually '
                                          'inspected PDF indices 25 and 26, printed pages 25 and 26, Tables '
                                          '16 and 18. This implementation attributes that earlier check; it '
                                          'does not claim a second visual check.',
                   'preserve_earlier_corrections': True,
                   'primary_pdf': 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075',
                   'raw_pdf_hash_claim': False},
 'unit': {'SI': '10^-11 m^3 kg^-1 s^-2', 'symbol': 'U', 'variance_unit': 'U^2'},
 'verification_only_baseline': {'field': ['within_nist', 'Q'],
                                'path': 'Experiments/GMeasurements/bipm_nist_common_constant_v1.json',
                                'role': 'verification_only_not_production_numerical_input',
                                'sha256': 'c9c46b7b5b39a74f12d0b5434a8f10c509bcc6ff7705292814e60f3682eaafe5',
                                'shared_data_not_additional_evidence': True,
                                'source_head': 'f3efeedb5b34bb051ce0c10d60dd14c1b8b8a87a',
                                'value': {'denominator': '881203500622795443319456087491213698992553564981517656789889',
                                          'numerator': '22063903657668443425767398062229151670397955346250000000000000'}}}
UPSTREAM_PATHS = {'authorization': 'Experiments/GMeasurements/nist_2026_estimator_feasibility_v1.json', 'certificate': 'Experiments/GMeasurements/nist_2026_n4_experimental_estimator_v1.json', 'protocol': 'Experiments/GMeasurements/nist_2026_n4_experimental_estimator_preregistration_v1.json', 'source': 'Experiments/GMeasurements/nist_2026_estimator_source_attestation_v1.json'}
SELECTORS = {'authorization': {'decision': ['decision'], 'identity': ['artifact_id'], 'schema': ['schema_version']},
 'certificate': {'V': ['estimator', 'absolute_covariance_matrix_in_1e_minus_11_units_squared'],
                 'authorization': ['upstream_authorization'],
                 'cells': ['finite_resolution', 'input_cells_in_1e_minus_11_units'],
                 'identity': ['artifact_id'],
                 'order': ['estimator', 'input_order'],
                 'rho': ['estimator', 'correlation_matrix'],
                 's': ['estimator', 'relative_standard_uncertainty_ppm'],
                 'schema': ['schema_version'],
                 'x': ['estimator', 'displayed_values_in_1e_minus_11_units']},
 'protocol': {'authorization': ['upstream_authorization', 'required_decisions'],
              'doi': ['source', 'doi'],
              'identity': ['experiment_id'],
              'inputs': ['input_projection'],
              'schema': ['schema_version']},
 'source': {'doi': ['source', 'doi'],
            'identity': ['artifact_id'],
            'order': ['experimental_layer', 'input_order'],
            'rho': ['experimental_layer', 'table_18', 'correlation_matrix'],
            'row_0_G_decimal_in_1e_minus_11_units': ['experimental_layer',
                                                     'table_16',
                                                     'measurements',
                                                     0,
                                                     'G_decimal_in_1e_minus_11_units'],
            'row_0_id': ['experimental_layer', 'table_16', 'measurements', 0, 'id'],
            'row_1_G_decimal_in_1e_minus_11_units': ['experimental_layer',
                                                     'table_16',
                                                     'measurements',
                                                     1,
                                                     'G_decimal_in_1e_minus_11_units'],
            'row_1_id': ['experimental_layer', 'table_16', 'measurements', 1, 'id'],
            'row_2_G_decimal_in_1e_minus_11_units': ['experimental_layer',
                                                     'table_16',
                                                     'measurements',
                                                     2,
                                                     'G_decimal_in_1e_minus_11_units'],
            'row_2_id': ['experimental_layer', 'table_16', 'measurements', 2, 'id'],
            'row_3_G_decimal_in_1e_minus_11_units': ['experimental_layer',
                                                     'table_16',
                                                     'measurements',
                                                     3,
                                                     'G_decimal_in_1e_minus_11_units'],
            'row_3_id': ['experimental_layer', 'table_16', 'measurements', 3, 'id'],
            's': ['experimental_layer', 'table_18', 'diagonal_relative_standard_uncertainty_ppm'],
            'schema': ['schema_version']}}


if __name__ == '__main__':
    main()
