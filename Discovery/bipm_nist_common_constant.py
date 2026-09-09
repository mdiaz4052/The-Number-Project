"""Two conditional fixed-summary Gaussian diagnostics; exact decisions, no p-values."""
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
NAME = 'bipm_nist_common_constant'
PREREGISTRATION_PATH = DIRECTORY / (NAME + '_preregistration_v1.json')
ATTESTATION = DIRECTORY / (NAME + '_source_attestation_v1.json')
OUTPUT = DIRECTORY / (NAME + '_v1.json')
BASELINE = '4e8acdebc5b03d03d5039c24a73bcc37e44711e2'
PREREGISTRATION_COMMIT = 'bf310acdbbef61100efa50fe411ae7873593db4c'
PREREGISTRATION_SHA256 = '376af6dad8d6df462eee2f6ed82ae6d168ed7e44afda11d041b401d1e2bfdaca'
EXTERNAL_ANCHOR = {'event': 'draft_pull_request_created',
                   'url': 'https://github.com/mdiaz4052/The-Number-Project/pull/48',
                   'created_at': '2026-09-09T02:59:14Z',
                   'preregistration_commit_sha': PREREGISTRATION_COMMIT,
                   'outcome_blind': False}
MODULE = 'Discovery/bipm_nist_common_constant.py'
HELPERS = ('Discovery/__init__.py', 'Discovery/nist_2026_n4_experimental_estimator.py',
           'Discovery/preregistration_history.py', 'Discovery/source_history.py')
NOTES = ('Notes/BIPMNISTCommonConstantDiagnosticSpecification.md',
         'Notes/BIPMNISTCommonConstantDiagnostic.md')
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


def validate_summary(x, V, w, mean, variance, cells, enclosure):
    check_covariance(V)
    k = len(V)
    require(len(x) == len(w) == len(cells) == k, 'summary dimensions')
    require(all(isinstance(v, (F, int)) and not isinstance(v, bool) for v in (*x, *w, mean, variance)),
            'exact summary required')
    require(sum(w) == 1, 'weight normalization')
    require(variance > 0 and dot(w, x) == mean and quadratic(V, w) == variance, 'summary identities')
    require(mv(V, w) == (variance,) * k, 'weights must be inherited minimum-variance weights')
    require(all(lo <= z <= hi and (lo + hi) / 2 == z for z, (lo, hi) in zip(x, cells)),
            'display cell midpoint')
    require(linear_enclosure(cells, w) == enclosure, 'full unconditioned aggregate enclosure')


def bipm_absolute_variance(b, r, denominator):
    require(b > 0 and r > 0 and denominator == 10**12, 'BIPM common-reference scale')
    return b * b * r / denominator


@dataclass(frozen=True)
class Inputs:
    b: F
    v_b: F
    I_b: tuple
    x: tuple
    V: tuple
    w: tuple
    n: F
    v_n: F
    cells_n: tuple
    I_n: tuple


def validate_projected(p, denominator):
    B, N = p['b_result'], p['n_result']
    require(B['order'] == ['servo', 'cavendish'], 'BIPM order')
    require(N['order'] == ['copper_servo', 'copper_free', 'sapphire_servo', 'sapphire_free'], 'NIST order')
    for role, values in p.items():
        require(type(values['schema']) is int and values['schema'] == 1, 'upstream schema')
        if 'doi' in values:
            require(values['doi'] == ('10.1098/rsta.2014.0032' if role.startswith('b_') else
                                     '10.1088/1681-7575/ae570f'), 'upstream DOI')
    bp = p['b_protocol']['inputs']
    ba = p['b_attestation']['inputs']
    x_b = tuple(decimal_rational(bp[key]['G_decimal_in_1e_minus_11_units']) for key in B['order'])
    require(all(v > 0 for v in x_b), 'positive BIPM coordinates')
    C = matrix(B['C'])
    sb = tuple(decimal_rational(bp[key]['standard_uncertainty_ppm']) for key in B['order'])
    require(all(v > 0 for v in sb), 'positive BIPM uncertainties')
    require(C == ((sb[0]**2, decimal_rational(bp['covariance_ppm_squared'])),
                  (decimal_rational(bp['covariance_ppm_squared']), sb[1]**2)), 'BIPM covariance convention')
    require(p['b_protocol']['order'] == B['order'], 'BIPM protocol order')
    for i, key in enumerate(B['order']):
        require(decimal_rational(ba[key]['value_decimal_in_1e_minus_11_units']) == x_b[i] and
                decimal_rational(ba[key]['relative_standard_uncertainty_ppm']) == sb[i], 'BIPM attestation')
    require(decimal_rational(ba['covariance_ppm_squared']['value']) == C[0][1], 'BIPM covariance attestation')
    w_b = (rational(B['w_servo']), rational(B['w_cavendish']))
    b, r = rational(B['b']), rational(B['r'])
    cb = tuple(interval(B['cells'][key]) for key in B['order'])
    for i, key in enumerate(B['order']):
        digits = bp[key]['printed_decimal_places']
        require(type(digits) is int and digits == ba[key]['printed_decimal_places'] and digits >= 0, 'BIPM precision')
        require(cb[i] == (x_b[i] - F(1, 2 * 10**digits), x_b[i] + F(1, 2 * 10**digits)), 'BIPM cells')
    I_b = interval(B['enclosure'])
    validate_summary(x_b, C, w_b, b, r, cb, I_b)
    np = p['n_protocol']['inputs']
    na = p['n_attestation']
    require(np['order'] == na['order'] == N['order'], 'NIST source order')
    x = tuple(map(rational, N['x']))
    s = tuple(map(rational, N['s']))
    u = tuple(map(rational, N['u']))
    R, V = matrix(N['R']), matrix(N['V'])
    require(len(x) == len(s) == len(u) == 4 and len(R) == 4 and all(len(row) == 4 for row in R), 'NIST dimensions')
    require(all(v > 0 for v in (*x, *s)), 'NIST positive inputs')
    require(u == tuple(x[i] * s[i] / 10**6 for i in range(4)), 'NIST inherited absolute scale')
    require(R == tuple(tuple(decimal_rational(z) for z in row) for row in np['correlation_matrix']) ==
            tuple(tuple(decimal_rational(z) for z in row) for row in na['R']), 'NIST correlation attestation')
    require(all(R[i][i] == 1 and all(abs(v) <= 1 for v in R[i]) for i in range(4)), 'NIST correlation geometry')
    require(V == tuple(tuple(R[i][j] * u[i] * u[j] for j in range(4)) for i in range(4)), 'NIST covariance convention')
    cells = tuple(map(interval, N['cells']))
    require(len(cells) == len(np['measurements']) == 4, 'NIST cells count')
    for i, row in enumerate(np['measurements']):
        require(row['id'] == N['order'][i] == na[f'row_{i}_id'], 'NIST row order')
        require(x[i] == decimal_rational(row['G_decimal_in_1e_minus_11_units']) ==
                decimal_rational(na[f'row_{i}_G_decimal_in_1e_minus_11_units']), 'NIST value attestation')
        require(s[i] == decimal_rational(row['relative_standard_uncertainty_ppm']) ==
                decimal_rational(na['s'][i]), 'NIST precise uncertainty attestation')
        digits = row['printed_decimal_places']
        require(type(digits) is int and digits >= 0, 'NIST precision')
        require(cells[i] == (x[i] - F(1, 2 * 10**digits), x[i] + F(1, 2 * 10**digits)), 'NIST display cells')
    w = tuple(map(rational, N['w']))
    n, v_n = rational(N['n']), rational(N['v'])
    I_n = interval(N['enclosure'])
    validate_summary(x, V, w, n, v_n, cells, I_n)
    auth = {'common_constant_comparison': 'NOT_EVALUATED', 'equation_64_reproduction': 'NOT_AUTHORIZED',
            'experimental_covariance': 'GO', 'published_bayesian_consensus': 'NO_GO'}
    require(p['n_protocol']['authorization'] == N['authorization']['decisions'] == auth, 'upstream authorization')
    require(p['n_feasibility']['decision'] == dict(auth, authorized_next_step=
            'preregister_n4_experimental_covariance_correlated_estimator_certificate'), 'feasibility authorization')
    require(N['decision'] == {'common_constant_comparison': 'NOT_EVALUATED', 'estimator_constructed': True,
            'probabilistic_compatibility': 'NOT_EVALUATED', 'published_equation_64_reproduction': 'NOT_CLAIMED'},
            'upstream estimator claim boundary')
    return Inputs(b, bipm_absolute_variance(b, r, denominator), I_b, x, V, w, n, v_n, cells, I_n)


def select_authorized(source, path):
    return at(source, path)


def project_records(protocol, records):
    """Select only frozen authorized paths; unrelated terminal fields never enter this projection."""
    projected = {}
    require(set(records) == set(protocol['upstream_records']), 'upstream inventory')
    for role, spec in protocol['upstream_records'].items():
        projected[role] = {}
        for name, field in spec['fields'].items():
            value = select_authorized(records[role], field['path'])
            require(value == field['value'], 'upstream authorized field differs: ' + role + '.' + name)
            projected[role][name] = value
    return validate_projected(projected, int(protocol['model']['ppm_squared_denominator']))


def cutoff(protocol, which):
    selected = protocol['calibration']['cutoffs'][which]
    return selected['df'], decimal_rational(selected['value'])


def midpoint_status(value, c):
    return 'FLAGGED_UNDER_DECLARED_MODEL' if value > c else 'NOT_FLAGGED_UNDER_DECLARED_MODEL'


def fitted_residual(x, mean):
    return tuple(v - mean for v in x)


def within_nist(x, V, w, half_widths, c):
    require(len(x) == len(V) == len(w) == len(half_widths) == 4, 'within-NIST dimensions')
    require(all(isinstance(v, (F, int)) and not isinstance(v, bool) for v in (*x, *w, *half_widths, c)), 'exact within-NIST inputs')
    require(c > 0 and all(h >= 0 for h in half_widths), 'within-NIST cutoff/widths')
    check_covariance(V)
    require(sum(w) == 1, 'within-NIST normalized weights')
    variance = quadratic(V, w)
    require(mv(V, w) == (variance,) * 4, 'within-NIST GLS weights')
    inv = inverse_matrix(V)
    z = mv(inv, (F(1),) * 4)
    normalization = sum(z)
    A = tuple(tuple(inv[i][j] - z[i] * z[j] / normalization for j in range(4)) for i in range(4))
    mean = dot(w, x)
    residual = fitted_residual(x, mean)
    Q = quadratic(inv, residual)
    require(Q == quadratic(A, x) and Q >= 0 and mv(A, (F(1),) * 4) == (0,) * 4, 'residual identities')
    # rank(A)=3 follows from the rank-one whitened projection; any principal 3x3 minor is positive.
    require(determinant([list(row[:3]) for row in A[:3]]) > 0 and determinant([list(row) for row in A]) == 0,
            'rank-three residual')
    ax = mv(A, x)
    L = 2 * sum(half_widths[i] * abs(ax[i]) for i in range(4))
    E = sum(half_widths[i] * half_widths[j] * abs(A[i][j]) for i in range(4) for j in range(4))
    bound = max(F(0), Q - L), Q + L + E
    disposition = ('FLAGGED_FOR_ALL_DISPLAY_VALUES' if bound[0] > c else
                   'NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES' if bound[1] <= c else 'UNRESOLVED_BY_DISPLAY_BOUND')
    return {'Q': Q, 'mean': mean, 'A': A, 'A_rank': 3, 'df': 3, 'cutoff': c,
            'L': L, 'E': E, 'display_bound': bound, 'bound_kind': 'certified_outer_bound_not_exact_extrema',
            'midpoint_status': midpoint_status(Q, c), 'display_status': disposition}


def sign(value):
    return (value > 0) - (value < 0)


def radical_sign(a, b, r):
    """Exact sign of a+b*sqrt(r), checking signs before squaring."""
    require(r >= 0, 'negative radicand')
    if r == 0 or b == 0:
        return sign(a)
    if a == 0:
        return sign(b)
    if sign(a) == sign(b):
        return sign(a)
    return sign(a) * sign(a * a - b * b * r)


def algebraic_statistic(d_squared, v_b, v_n, rho, c):
    require(all(isinstance(v, (F, int)) and not isinstance(v, bool) for v in (d_squared, v_b, v_n, rho, c)), 'exact contrast inputs')
    require(v_b > 0 and v_n > 0 and -1 <= rho <= 1 and d_squared >= 0 and c > 0, 'contrast geometry')
    a, b, r = v_b + v_n, -2 * rho, v_b * v_n
    require(radical_sign(a, b, r) > 0, 'zero contrast variance requires singular classification')
    comparison = radical_sign(d_squared - c * a, -c * b, r)
    # This decimal is readability only. Every decision above is exact.
    with localcontext() as ctx:
        ctx.prec = 60
        dec = lambda v: Decimal(v.numerator) / Decimal(v.denominator)
        denom = dec(a) + dec(b) * dec(r).sqrt()
        approximation = format(dec(d_squared) / denom, '.18g') if denom > 0 else None
    return {'numerator': d_squared, 'denominator': {'rational': a, 'sqrt_coefficient': b, 'radicand': r},
            'rho': rho, 'cutoff_comparison': comparison,
            'status': 'FLAGGED_UNDER_DECLARED_MODEL' if comparison > 0 else 'NOT_FLAGGED_UNDER_DECLARED_MODEL',
            'decimal_readability_only': approximation}


def difference_interval(I_b, I_n):
    require(I_b[0] <= I_b[1] and I_n[0] <= I_n[1], 'difference intervals')
    return I_b[0] - I_n[1], I_b[1] - I_n[0]


def absolute_extrema(bounds):
    low, high = bounds
    require(low <= high, 'absolute bounds')
    return (F(0) if low <= 0 <= high else min(abs(low), abs(high))), max(abs(low), abs(high))


def rho_family(bounds, v_b, v_n, c):
    require(v_b > 0 and v_n > 0, 'positive marginal variances')
    amin, amax = absolute_extrema(bounds)
    if v_b == v_n:
        return {'status': 'UNRESOLVED_SINGULAR_ENDPOINT', 'singular_rho': F(1),
                'reason': 'zero contrast variance at rho=1; closed family not classified',
                'minimum_absolute_difference': amin, 'maximum_absolute_difference': amax}
    low = algebraic_statistic(amin**2, v_b, v_n, F(-1), c)
    high = algebraic_statistic(amax**2, v_b, v_n, F(1), c)
    disposition = ('FLAGGED_FOR_ALL_RHO_AND_DISPLAY_VALUES' if low['cutoff_comparison'] > 0 else
                   'NOT_FLAGGED_FOR_ALL_RHO_AND_DISPLAY_VALUES' if high['cutoff_comparison'] <= 0 else
                   'RHO_OR_DISPLAY_DEPENDENT')
    return {'status': disposition, 'T_min': low, 'T_max': high,
            'minimum_absolute_difference': amin, 'maximum_absolute_difference': amax}


def aggregate_contrast(b, n, I_b, I_n, v_b, v_n, c):
    require(I_b[0] <= b <= I_b[1] and I_n[0] <= n <= I_n[1], 'midpoints outside aggregate cells')
    d = b - n
    bounds = difference_interval(I_b, I_n)
    amin, amax = absolute_extrema(bounds)
    zero_low = algebraic_statistic(amin**2, v_b, v_n, F(0), c)
    zero_high = algebraic_statistic(amax**2, v_b, v_n, F(0), c)
    return {'D_midpoint': d, 'difference_enclosure': bounds, 'df': 1, 'cutoff': c,
            'v_B': v_b, 'v_N': v_n, 'rho_domain': (F(-1), F(1)),
            'rho_zero_reference': {'role': 'hypothetical_uncorrelated_not_established_independence',
                'midpoint': algebraic_statistic(d**2, v_b, v_n, F(0), c),
                'display_T_min': zero_low, 'display_T_max': zero_high,
                'display_status': ('FLAGGED_FOR_ALL_DISPLAY_VALUES' if zero_low['cutoff_comparison'] > 0 else
                    'NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES' if zero_high['cutoff_comparison'] <= 0 else
                    'DISPLAY_DEPENDENT')},
            'midpoint_all_rho': rho_family((d, d), v_b, v_n, c),
            'all_rho_all_display': rho_family(bounds, v_b, v_n, c)}


def claim_boundary(protocol, internally_flagged):
    require(all(v is True for v in protocol['claim_limits'].values()), 'claim restrictions must be active')
    return {'status': PROVISIONAL, 'conditional_only': True,
            'calibration': protocol['calibration']['label'], 'limits': protocol['claim_limits'],
            'within_model_challenged': internally_flagged,
            'interpretation': ('The experimental-only NIST model is already flagged internally; the cross-campaign '
                'diagnostic remains conditional under that same model and is not independent confirmation.' if internally_flagged else
                'Non-rejection means only that this diagnostic did not flag the declared model; it does not establish model truth.'),
            'allowed_conclusion': 'The declared model is flagged by this diagnostic under the stated uncertainty/dependence assumptions.'}


def validate_protocol(p):
    require(isinstance(p, dict) and set(p) == PROTOCOL_KEYS, 'preregistration schema')
    require(type(p['schema_version']) is int and p['schema_version'] == 1 and p['experiment_id'] == NAME + '_v1', 'protocol identity')
    require(p['intended_base_sha'] == BASELINE and p['merge_semantics'] == 'true_merge_commit_only', 'base/history policy')
    require(p['unit'] == {'symbol': 'U', 'SI': '10^-11 m^3 kg^-1 s^-2', 'variance_unit': 'U^2'}, 'units')
    require(p['model'] == SUPPORTED_MODEL, 'unsupported model policy')
    require(p['decisions'] == SUPPORTED_DECISIONS and p['claim_limits'] == SUPPORTED_LIMITS, 'decision/claim policy')
    require(p['known_prior_information']['outcome_blind'] is False and bool(p['known_prior_information']['disclosure']), 'prior exposure disclosure')
    require(p['audit_status_at_freeze']['status'] == PROVISIONAL and p['audit_status_at_freeze']['unaudited_dependency_pr'] == 47,
            'inherited provisional dependency')
    require(p['calibration']['tail'] == 'upper' and p['calibration']['flag_rule'] == 'strictly_greater' and
            p['calibration']['p_values'] is False and p['calibration']['joint_error_rate_claim'] is False, 'nominal calibration policy')
    require(cutoff(p, 'within_nist') == (3, F('7.814728')) and cutoff(p, 'aggregate_contrast') == (1, F('3.841459')), 'df/cutoff mapping')
    require('nominal' in p['calibration']['label'], 'nominal calibration label')
    require(p['calibration']['verification'] == CUTOFF_VERIFICATION, 'pre-freeze cutoff verification record')
    require(p['source_review'] == SOURCE_REVIEW, 'bounded review must retain access/absence limits')
    require(p['planned_surfaces'] == PLANNED_SURFACES and p['mutation_requirements'] == MUTATION_REQUIREMENTS, 'frozen inventory')
    require(isinstance(p['objective'], str) and bool(p['objective']), 'objective required')
    require(set(p['upstream_records']) == set(SELECTORS), 'seven frozen upstream records required')
    for role, spec in p['upstream_records'].items():
        require(set(spec) == {'path', 'sha256', 'fields'} and spec['path'] == UPSTREAM_PATHS[role], 'upstream path schema')
        require(re.fullmatch('[0-9a-f]{64}', spec['sha256']) is not None, 'upstream digest')
        require(set(spec['fields']) == set(SELECTORS[role]), 'authorized field inventory')
        for key, entry in spec['fields'].items():
            require(set(entry) == {'path', 'value'} and entry['path'] == SELECTORS[role][key], 'authorized projection path')
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
    # Every result-bearing/source addition is checked, not just the calculator module.
    for path in (MODULE, ATTESTATION.as_posix(), NOTES[1], OUTPUT.as_posix(),
                 'Experiments/GMeasurements/bipm_nist_common_constant_mutations_v1.json'):
        events = git(root, 'log', '--full-history', '--diff-filter=A', '--format=%H%x00%aI%x00%cI', '--', path).decode().splitlines()
        if not events:
            require(path in (OUTPUT.as_posix(), 'Experiments/GMeasurements/bipm_nist_common_constant_mutations_v1.json'),
                    'source introduction must be committed')
        for event in events:
            sha, authored, committed = event.split('\0')
            require(stamp(authored) > anchor and stamp(committed) > anchor, 'result-driving addition precedes anchor')
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


def build_artifact(root=ROOT):
    protocol = verify_preregistration(root)
    verify_implementation_chronology(root)
    snapshot = source_snapshot(root, source_paths(protocol))
    attestation = _json((root / ATTESTATION).read_bytes())
    require(attestation == {'schema_version': 1, 'artifact_id': NAME + '_source_attestation_v1',
            'preregistration_sha256': PREREGISTRATION_SHA256, 'external_anchor': EXTERNAL_ANCHOR,
            'review': protocol['source_review'], 'preparation_phase': 'review_before_freeze_attestation_serialized_after_anchor'},
            'source attestation differs from frozen bounded review')
    inputs = project_records(protocol, load_records(protocol, root))
    within = within_nist(inputs.x, inputs.V, inputs.w,
                         tuple((hi - lo) / 2 for lo, hi in inputs.cells_n), cutoff(protocol, 'within_nist')[1])
    cross = aggregate_contrast(inputs.b, inputs.n, inputs.I_b, inputs.I_n, inputs.v_b, inputs.v_n,
                               cutoff(protocol, 'aggregate_contrast')[1])
    return {'schema_version': 1, 'artifact_id': NAME + '_v1', 'kind': protocol['model']['id'],
            'unit': protocol['unit'], 'model': protocol['model'], 'calibration': protocol['calibration'],
            'within_nist': exact_tree(within), 'aggregate_contrast': exact_tree(cross),
            'readability_only': {'Q_N': decimal_text(within['Q']),
                'Q_N_display_bound': [decimal_text(v) for v in within['display_bound']],
                'D_midpoint_U': decimal_text(cross['D_midpoint']),
                'D_display_bound_U': [decimal_text(v) for v in cross['difference_enclosure']]},
            'claim_boundary': claim_boundary(protocol, within['midpoint_status'] == 'FLAGGED_UNDER_DECLARED_MODEL'),
            'audit_status_at_freeze': protocol['audit_status_at_freeze'],
            'known_prior_information': protocol['known_prior_information'], 'source_review': protocol['source_review'],
            'upstream_pins_and_projections': protocol['upstream_records'],
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
            print('BIPM-NIST conditional diagnostic verified')
        else:
            (args.output or ROOT / OUTPUT).write_text(serialize_artifact(build_artifact()))
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        print(f'bipm_nist_diagnostic_invalid: {error}', file=sys.stderr)
        raise SystemExit(1) from error

# Frozen supported grammar and policy descriptors follow. Numerical operands are
# parsed/consumed from the validated protocol, not selected from these descriptors.

PROTOCOL_KEYS = {'audit_status_at_freeze',
 'calibration',
 'claim_limits',
 'decisions',
 'experiment_id',
 'intended_base_sha',
 'known_prior_information',
 'merge_semantics',
 'model',
 'mutation_requirements',
 'objective',
 'planned_surfaces',
 'schema_version',
 'source_review',
 'unit',
 'upstream_records'}

SUPPORTED_MODEL = {'bipm_reference': 'frozen_reconstructed_midpoint',
 'bipm_scaling': 'b_squared_times_relative_covariance_over_10^12',
 'continuous_extrema': 'analytic_absolute_difference_and_variance_endpoints',
 'covariance': 'fixed_known_working_assumption',
 'cross_variance': 'v_B+v_N-2*rho*sqrt(v_B*v_N)',
 'display_covariance_weights': 'fixed_at_displayed_midpoints',
 'gaussian_errors': 'joint_zero_mean',
 'id': 'fixed_summary_gaussian_common_mean_and_aggregate_contrast_v1',
 'invalid_input_policy': 'validation_error',
 'nist_scaling': 'inherited_x_i_times_s_i_over_10^6',
 'numerical_comparison': 'exact_sign_aware_rational_plus_rational_sqrt',
 'ppm_squared_denominator': '1000000000000',
 'rho_interval': ['-1', '1'],
 'rho_reference': '0',
 'rho_reference_role': 'hypothetical_uncorrelated_not_established_independence',
 'singular_policy': 'UNRESOLVED_SINGULAR_ENDPOINT',
 'within_display_bound': 'max(0,Q-L),Q+L+E',
 'within_nist': 'fitted_common_mean_residual_quadratic'}

SUPPORTED_DECISIONS = {'cross_family': ['FLAGGED_FOR_ALL_RHO_AND_DISPLAY_VALUES',
                  'NOT_FLAGGED_FOR_ALL_RHO_AND_DISPLAY_VALUES',
                  'RHO_OR_DISPLAY_DEPENDENT',
                  'UNRESOLVED_SINGULAR_ENDPOINT'],
 'midpoint': ['FLAGGED_UNDER_DECLARED_MODEL', 'NOT_FLAGGED_UNDER_DECLARED_MODEL'],
 'nist_display': ['FLAGGED_FOR_ALL_DISPLAY_VALUES',
                  'NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES',
                  'UNRESOLVED_BY_DISPLAY_BOUND']}

SUPPORTED_LIMITS = {'conditional_model_only': True,
 'inherited_provisional_status': True,
 'no_apparatus_or_physical_cause_identification': True,
 'no_bayesian_or_equation64_reproduction': True,
 'no_combined_test_or_independent_confirmation': True,
 'no_outcome_blind_discovery': True,
 'no_pooled_G_estimate': True,
 'no_universality_probability': True,
 'no_variance_inflation_or_configuration_removal': True,
 'nominal_not_experimental_error_guarantee': True,
 'preserve_upstream_not_evaluated_no_go': True,
 'publication_cells_are_deterministic_sensitivity': True}

CUTOFF_VERIFICATION = {'method': 'Data-free 60-step bisection of F1(t)=erf(sqrt(t/2)); F3(t)=F1(t)-sqrt(2t/pi)*exp(-t/2), using Python '
           'math. NIST table independently cross-checks three-decimal references. Diagnostic decisions use exact '
           'operational rationals, never these numerical CDF values.',
 'reference': 'https://www.itl.nist.gov/div898/handbook/eda/section3/eda3674.htm',
 'results': [{'cutoff_cdf': '0.9500000053468043',
              'df': 1,
              'lower_last_digit_cdf': '0.9499999755273371',
              'operational_cutoff': '3.841459',
              'quantile_approximation': '3.841458820694123'},
             {'cutoff_cdf': '0.9500000021680338',
              'df': 3,
              'lower_last_digit_cdf': '0.9499999797591373',
              'operational_cutoff': '7.814728',
              'quantile_approximation': '7.814727903251173'}]}

SOURCE_REVIEW = {'cross_campaign_covariance_status': 'NOT_IDENTIFIED_IN_REVIEWED_MATERIAL',
 'evidence_access': 'NIST full relevant PDF passages accessible; BIPM publisher full-page/PDF access failed '
                    '(403/internal error), with relevant indexed publisher passages available and existing '
                    'corrected attestation inherited. No new BIPM PDF-byte/transcription verification claimed.',
 'numerical_covariance': None,
 'prepared_utc_date': '2026-09-09',
 'review_scope': 'Bounded passages only; not exhaustive absence. Full rho envelope retained regardless of source '
                 'suggestions.',
 'sources': [{'access': 'indexed passages plus frozen upstream attestation; full publisher response inaccessible',
              'doi': '10.1098/rsta.2014.0032',
              'locators': ['section 11(d), equations 11.14d and 11.15a-b', 'section 12; Table 1, p.26'],
              'positive_statements': 'Indexed publisher passages describe covariance from shared input '
                                     'sensitivities, a variance-minimizing unbiased weighted mean, and Table 1 '
                                     'uncertainties 61/54 ppm with covariance -2080 ppm squared. This is '
                                     'within-BIPM combination information.',
              'url': 'https://royalsocietypublishing.org/rsta/article/372/2026/20140032/58577/The-BIPM-measurements-of-the-Newtonian-constant-of',
              'version': '2014 corrected detailed treatment; correction DOI 10.1103/PhysRevLett.113.039901 '
                         'inherited'},
             {'access': 'PDF text pp.3-5,25-28 and Table 18/19 page screenshots inspected',
              'doi': '10.1088/1681-7575/ae570f',
              'locators': ['printed pp.3-5 apparatus lineage',
                           'section 9, pp.25-27; Tables 16-19',
                           'section 10, pp.27-28'],
              'positive_statements': 'The apparatus moved to NIST; a collaborator contributed to both efforts. '
                                     'Table 18 describes correlations among four NIST determinations. The '
                                     'conclusion discusses unresolved discrepancy and added dark uncertainty. '
                                     'These passages do not identify an aggregate cross-campaign covariance.',
              'url': 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075',
              'version': 'Metrologia 63 (2026) 025012; published 2026-04-16; NIST-hosted publisher PDF, cover '
                         'downloaded 2026-05-02'}]}

PLANNED_SURFACES = {'modified': ['.github/workflows/verify.yml'],
 'new': ['Discovery/bipm_nist_common_constant.py',
         'Discovery/bipm_nist_common_constant_mutations.py',
         'Experiments/GMeasurements/bipm_nist_common_constant_preregistration_v1.json',
         'Experiments/GMeasurements/bipm_nist_common_constant_source_attestation_v1.json',
         'Experiments/GMeasurements/bipm_nist_common_constant_v1.json',
         'Experiments/GMeasurements/bipm_nist_common_constant_mutations_v1.json',
         'Notes/BIPMNISTCommonConstantDiagnosticSpecification.md',
         'Notes/BIPMNISTCommonConstantDiagnostic.md',
         'Notes/BIPMNISTCommonConstantMutationValidation.md',
         'tests/test_bipm_nist_common_constant.py',
         'tests/test_bipm_nist_common_constant_mutations.py']}

MUTATION_REQUIREMENTS = [{'id': 'covariance_off_diagonal',
  'test': 'tests.test_bipm_nist_common_constant_mutations.DiagnosticMutationBehaviorTests.test_covariance'},
 {'id': 'bipm_ppm_squared_scaling',
  'test': 'tests.test_bipm_nist_common_constant_mutations.DiagnosticMutationBehaviorTests.test_bipm_scaling'},
 {'id': 'cross_covariance_sign',
  'test': 'tests.test_bipm_nist_common_constant_mutations.DiagnosticMutationBehaviorTests.test_rho_sign'},
 {'id': 'display_cell_collapse',
  'test': 'tests.test_bipm_nist_common_constant_mutations.DiagnosticMutationBehaviorTests.test_display_bound'},
 {'id': 'df_cutoff_mapping',
  'test': 'tests.test_bipm_nist_common_constant_mutations.DiagnosticMutationBehaviorTests.test_cutoff_mapping'},
 {'id': 'omitted_mean_fitting',
  'test': 'tests.test_bipm_nist_common_constant_mutations.DiagnosticMutationBehaviorTests.test_mean_fitting'},
 {'id': 'forbidden_terminal_consumption',
  'test': 'tests.test_bipm_nist_common_constant_mutations.DiagnosticMutationBehaviorTests.test_terminal_invariance'},
 {'id': 'unsupported_claim_promotion',
  'test': 'tests.test_bipm_nist_common_constant_mutations.DiagnosticMutationBehaviorTests.test_claim_boundary'}]

SELECTORS = {'b_attestation': {'correction': ['correction_provenance'],
                   'doi': ['primary_source', 'doi'],
                   'identity': ['artifact_id'],
                   'inputs': ['transcription', 'estimator_inputs'],
                   'schema': ['schema_version']},
 'b_protocol': {'doi': ['primary_source', 'doi'],
                'identity': ['experiment_id'],
                'inputs': ['source_projection', 'estimator_inputs'],
                'order': ['mathematical_model', 'input_order'],
                'schema': ['schema_version']},
 'b_result': {'C': ['estimator', 'covariance_matrix_ppm_squared'],
              'b': ['representation', 'midpoint_aggregate_in_1e_minus_11_units'],
              'cells': ['representation', 'input_cells_in_1e_minus_11_units'],
              'doi': ['source', 'doi'],
              'enclosure': ['representation', 'aggregate_enclosure_in_1e_minus_11_units'],
              'identity': ['artifact_id'],
              'model': ['kind'],
              'order': ['estimator', 'input_order'],
              'r': ['estimator', 'combined_relative_variance_ppm_squared'],
              'schema': ['schema_version'],
              'w_cavendish': ['estimator', 'derived_weights', 'cavendish'],
              'w_servo': ['estimator', 'derived_weights', 'servo']},
 'n_attestation': {'R': ['experimental_layer', 'table_18', 'correlation_matrix'],
                   'doi': ['source', 'doi'],
                   'identity': ['artifact_id'],
                   'order': ['experimental_layer', 'input_order'],
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
                   'schema': ['schema_version']},
 'n_feasibility': {'decision': ['decision'], 'identity': ['artifact_id'], 'schema': ['schema_version']},
 'n_protocol': {'authorization': ['upstream_authorization', 'required_decisions'],
                'doi': ['source', 'doi'],
                'identity': ['experiment_id'],
                'inputs': ['input_projection'],
                'model': ['estimator_definition'],
                'schema': ['schema_version']},
 'n_result': {'R': ['estimator', 'correlation_matrix'],
              'V': ['estimator', 'absolute_covariance_matrix_in_1e_minus_11_units_squared'],
              'authorization': ['upstream_authorization'],
              'cells': ['finite_resolution', 'input_cells_in_1e_minus_11_units'],
              'decision': ['decision'],
              'doi': ['source', 'doi'],
              'enclosure': ['finite_resolution', 'aggregate_enclosure_in_1e_minus_11_units'],
              'identity': ['artifact_id'],
              'model': ['kind'],
              'n': ['estimator', 'point_estimate_in_1e_minus_11_units'],
              'order': ['estimator', 'input_order'],
              's': ['estimator', 'relative_standard_uncertainty_ppm'],
              'schema': ['schema_version'],
              'u': ['estimator', 'absolute_standard_uncertainty_in_1e_minus_11_units'],
              'v': ['estimator', 'combined_variance_in_1e_minus_11_units_squared'],
              'w': ['estimator', 'weights'],
              'x': ['estimator', 'displayed_values_in_1e_minus_11_units']}}

UPSTREAM_PATHS = {'b_attestation': 'Experiments/GMeasurements/bipm_2014_correlated_estimator_source_attestation_v1.json',
 'b_protocol': 'Experiments/GMeasurements/bipm_2014_correlated_estimator_preregistration_v1.json',
 'b_result': 'Experiments/GMeasurements/bipm_2014_correlated_estimator_v1.json',
 'n_attestation': 'Experiments/GMeasurements/nist_2026_estimator_source_attestation_v1.json',
 'n_feasibility': 'Experiments/GMeasurements/nist_2026_estimator_feasibility_v1.json',
 'n_protocol': 'Experiments/GMeasurements/nist_2026_n4_experimental_estimator_preregistration_v1.json',
 'n_result': 'Experiments/GMeasurements/nist_2026_n4_experimental_estimator_v1.json'}

if __name__ == '__main__':
    main()
