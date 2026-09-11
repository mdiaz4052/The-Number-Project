"""Conditional, exact full-box certificates for published NIST covariance precision.

No upstream evaluator is imported. All scientific reads pass through frozen
selectors; prior model results are verification-only inputs to the test suite.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
from itertools import product
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import verify_committed_source_state, SourceVerificationError

ROOT = Path(__file__).resolve().parents[1]
STEM = 'nist_2026_covariance_precision'
DIRECTORY = Path('Experiments/GMeasurements')
PREREGISTRATION_PATH = DIRECTORY / (STEM + '_preregistration_v1.json')
ATTESTATION = DIRECTORY / (STEM + '_source_attestation_v1.json')
OUTPUT = DIRECTORY / (STEM + '_v1.json')
MUTATION_OUTPUT = DIRECTORY / (STEM + '_mutations_v1.json')
MODULE = 'Discovery/' + STEM + '.py'
MUTATOR = 'Discovery/' + STEM + '_mutations.py'
TESTS = ('tests/test_' + STEM + '.py', 'tests/test_' + STEM + '_mutations.py')
SPEC = 'Notes/NIST2026CovariancePrecisionSpecification.md'
NOTE = 'Notes/NIST2026CovariancePrecision.md'
IMAGE = 'Experiments/GMeasurements/SourceEvidence/nist_2026_table18_miguel_20260910.png'
RECEIPT = 'Experiments/GMeasurements/SourceEvidence/nist_2026_table18_receipt_20260910.json'
BASE = '13c6b7b3bcaedda9acb1318c8a96ae39e18f538f'
FREEZE = '6496188c17c82410241d2d703121aa1e9d048c6a'
FREEZE_DIGEST = '242551394632421d2362a57bab43f7eb1729f61620166244055bb26d141262f5'
ANCHOR = {'event': 'draft_pull_request_created', 'url': 'https://github.com/mdiaz4052/The-Number-Project/pull/52',
          'created_at': '2026-09-11T19:01:42Z', 'freeze_head': FREEZE, 'outcome_blind': False}
PROVISIONAL = 'PROVISIONAL — INDEPENDENT AUDIT PENDING'
PAIRS = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
FLAG = 'FLAGGED_FOR_ALL_PRECISION_VALUES'
NONFLAG = 'NOT_FLAGGED_FOR_ALL_PRECISION_VALUES'
VARIATION = 'CLASSIFICATION_VARIATION_WITNESSED'
UNRESOLVED = 'UNRESOLVED_FROM_CERTIFIED_BOUNDS'
DOMAIN = 'UNRESOLVED_COVARIANCE_DOMAIN'


class PrecisionError(ValueError):
    """Contract/computation failure; never a scientific unresolved disposition."""


def require(condition, message):
    if not condition:
        raise PrecisionError(message)


def serialize_artifact(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(raw):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    def invalid(value):
        raise PrecisionError('nonfinite JSON constant ' + value)
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise PrecisionError('malformed JSON') from error


def rational(x):
    if isinstance(x, F) or type(x) is int:
        return F(x)
    if isinstance(x, str):
        require(re.fullmatch(r'-?(0|[1-9][0-9]*)(?:\.[0-9]+|/[1-9][0-9]*)?', x), 'exact number string')
        return F(x)
    require(isinstance(x, dict) and set(x) == {'numerator', 'denominator'}, 'rational schema')
    require(type(x['numerator']) is str and re.fullmatch(r'-?(0|[1-9][0-9]*)', x['numerator']), 'numerator')
    require(type(x['denominator']) is str and re.fullmatch(r'[1-9][0-9]*', x['denominator']), 'denominator')
    result = F(int(x['numerator']), int(x['denominator']))
    require(record(result) == x, 'noncanonical rational')
    return result


def record(x):
    return {'numerator': str(x.numerator), 'denominator': str(x.denominator)}


def exact_tree(x):
    if isinstance(x, F):
        return record(x)
    if isinstance(x, (list, tuple)):
        return [exact_tree(v) for v in x]
    if isinstance(x, dict):
        return {k: exact_tree(v) for k, v in x.items()}
    return x


def at(obj, path):
    try:
        for key in path:
            obj = obj[key]
        return obj
    except (KeyError, IndexError, TypeError) as error:
        raise PrecisionError('missing projected field') from error


def matrix(M):
    require(isinstance(M, (list, tuple)) and M and all(isinstance(r, (list, tuple)) for r in M), 'matrix schema')
    require(len(M[0]) > 0 and all(len(r) == len(M[0]) for r in M), 'rectangular matrix')
    return tuple(tuple(rational(x) for x in row) for row in M)


def transpose(A):
    return tuple(zip(*matrix(A)))


def dot(x, y):
    require(len(x) == len(y), 'dot shape')
    return sum((a * b for a, b in zip(x, y)), F(0))


def mv(A, x):
    return tuple(dot(row, x) for row in A)


def mm(A, B):
    return tuple(tuple(dot(row, col) for col in transpose(B)) for row in A)


def eye(n):
    return tuple(tuple(F(i == j) for j in range(n)) for i in range(n))


def diag(d):
    return tuple(tuple(v if i == j else F(0) for j in range(len(d))) for i, v in enumerate(d))


def quadratic(A, x):
    return dot(x, mv(A, x))


def abs_matrix(A):
    return tuple(tuple(abs(v) for v in row) for row in A)


def determinant(A):
    A = [list(row) for row in matrix(A)]
    n = len(A)
    require(all(len(row) == n for row in A), 'square determinant')
    result = F(1)
    for c in range(n):
        pivot = next((i for i in range(c, n) if A[i][c]), None)
        if pivot is None:
            return F(0)
        if pivot != c:
            A[c], A[pivot] = A[pivot], A[c]
            result = -result
        p = A[c][c]
        result *= p
        for i in range(c + 1, n):
            f = A[i][c] / p
            for j in range(c + 1, n):
                A[i][j] -= f * A[c][j]
    return result


def minors(A):
    A = matrix(A)
    require(A == transpose(A), 'symmetric square matrix required')
    return tuple(determinant(tuple(row[:k] for row in A[:k])) for k in range(1, len(A) + 1))


def inverse(A):
    A = matrix(A)
    n = len(A)
    require(len(A[0]) == n, 'square inverse')
    rows = [list(row) + list(e) for row, e in zip(A, eye(n))]
    for c in range(n):
        pivot = next((i for i in range(c, n) if rows[i][c]), None)
        require(pivot is not None, 'singular matrix; no pseudoinverse')
        rows[c], rows[pivot] = rows[pivot], rows[c]
        p = rows[c][c]
        rows[c] = [v / p for v in rows[c]]
        for i in range(n):
            if i != c:
                f = rows[i][c]
                rows[i] = [a - f * b for a, b in zip(rows[i], rows[c])]
    result = tuple(tuple(row[n:]) for row in rows)
    require(mm(A, result) == eye(n), 'inverse identity')
    return result


def ldl(A):
    A = matrix(A)
    require(A == transpose(A), 'symmetric LDL')
    n = len(A)
    L = [list(row) for row in eye(n)]
    d = []
    for j in range(n):
        pivot = A[j][j] - sum((L[j][k] ** 2 * d[k] for k in range(j)), F(0))
        require(pivot > 0, 'LDL requires positive pivots')
        d.append(pivot)
        for i in range(j + 1, n):
            L[i][j] = (A[i][j] - sum((L[i][k] * L[j][k] * d[k] for k in range(j)), F(0))) / pivot
    L = matrix(L)
    T = inverse(L)
    require(mm(mm(L, diag(d)), transpose(L)) == A, 'LDL reconstruction')
    require(mm(mm(T, A), transpose(T)) == diag(d), 'LDL congruence')
    return L, tuple(d), T


def cell(center, half_width):
    center, half_width = rational(center), rational(half_width)
    require(half_width >= 0, 'nonnegative half width')
    return center - half_width, center + half_width


def interval_product(left, right):
    require(left[0] <= left[1] and right[0] <= right[1], 'interval order')
    products = [a * b for a in left for b in right]
    return min(products), max(products)


def correlation(rho, pairs=PAIRS):
    require(len(rho) == len(pairs) == 6 and set(pairs) == set(PAIRS), 'six shared correlations')
    P = [list(row) for row in eye(4)]
    for (i, j), value in zip(pairs, rho):
        require(-1 <= value <= 1, 'correlation range')
        P[i][j] = P[j][i] = value
    return matrix(P)


def covariance(a, parameters, pairs=PAIRS):
    require(len(a) == 4 and len(parameters) == 10 and all(v > 0 for v in a), 'positive fixed anchors')
    s, rho = parameters[:4], parameters[4:]
    require(all(v > 0 for v in s), 'positive relative uncertainty')
    P = correlation(rho, pairs)
    return tuple(tuple(a[i] * a[j] * s[i] * s[j] * P[i][j] / 10**12 for j in range(4)) for i in range(4))


def covariance_enclosure(a, box, pairs=PAIRS):
    require(len(box) == 10 and all(lo <= hi for lo, hi in box), 'ten ordered cells')
    require(all(lo > 0 for lo, _ in box[:4]), 'positive s box')
    low = [[F(0)] * 4 for _ in range(4)]
    high = [[F(0)] * 4 for _ in range(4)]
    for i in range(4):
        low[i][i], high[i][i] = (a[i] ** 2 * s ** 2 / 10**12 for s in box[i])
    for k, (i, j) in enumerate(pairs):
        lo, hi = interval_product(interval_product(box[i], box[j]), box[4 + k])
        factor = a[i] * a[j] / 10**12
        low[i][j] = low[j][i] = factor * lo
        high[i][j] = high[j][i] = factor * hi
    center = tuple((lo + hi) / 2 for lo, hi in box)
    Vc = covariance(a, center, pairs)
    E = tuple(tuple(max(abs(low[i][j] - Vc[i][j]), abs(high[i][j] - Vc[i][j])) for j in range(4)) for i in range(4))
    return {'V_minus': matrix(low), 'V_plus': matrix(high), 'parameters_center': center, 'Vc': Vc, 'E': E}


def family_validity(box, pairs=PAIRS):
    require(len(box) == 10 and all(lo <= hi for lo, hi in box), 'family cells')
    require(all(lo > 0 for lo, _ in box[:4]), 'nonpositive s endpoint is malformed policy')
    require(all(-1 <= lo <= hi <= 1 for lo, hi in box[4:]), 'invalid rho endpoint')
    corners = []
    for bits in product((0, 1), repeat=6):
        rho = tuple(box[4 + k][b] for k, b in enumerate(bits))
        P = correlation(rho, pairs)
        leading = minors(P)
        corners.append({'bits': bits, 'rho': rho, 'P': P, 'leading_principal_minors': leading,
                        'positive_definite': all(x > 0 for x in leading)})
    good = all(c['positive_definite'] for c in corners)
    return {'status': 'POSITIVE_DEFINITE_FULL_BOX' if good else 'BOX_CONTAINS_NON_PD', 'corners': corners,
            'offending_corners': [i for i, c in enumerate(corners) if not c['positive_definite']],
            'proof': 'Affine correlation box is convex hull of these 64 matrices; SPD cone is convex. Positive D and full-row-rank R preserve SPD.',
            'PD_subset_analyzed_if_box_invalid': False}


def display_terms(H, a, h):
    q = quadratic(H, a)
    B = 2 * sum((w * abs(z) for w, z in zip(h, mv(H, a))), F(0))
    E = sum((h[i] * h[j] * abs(H[i][j]) for i in range(len(h)) for j in range(len(h))), F(0))
    require(q >= 0 and all(v >= 0 for v in h), 'PSD center and nonnegative widths')
    return {'H': H, 'q': q, 'B': B, 'E': E, 'lower': max(F(0), q - B), 'upper': q + B + E}


def sandwich(R, Vc, E):
    Cc = mm(mm(R, Vc), transpose(R))
    L, d, T = ldl(Cc)
    Z = mm(T, R)
    radius = mm(mm(abs_matrix(Z), E), transpose(abs_matrix(Z)))
    g = tuple(sum(row, F(0)) for row in radius)
    require(all(v >= 0 for row in radius for v in row) and radius == transpose(radius), 'nonnegative symmetric radius')
    lower_denominators = tuple(x + y for x, y in zip(d, g))
    upper_denominators = tuple(x - y for x, y in zip(d, g))
    Hlower = mm(mm(transpose(Z), diag(tuple(1 / x for x in lower_denominators))), Z)
    Hupper = None
    if all(x > 0 for x in upper_denominators):
        Hupper = mm(mm(transpose(Z), diag(tuple(1 / x for x in upper_denominators))), Z)
    return {'Cc': Cc, 'L': L, 'd': d, 'T': T, 'Z': Z, 'F': radius, 'g': g,
            'd_plus_g': lower_denominators, 'd_minus_g': upper_denominators,
            'H_lower': Hlower, 'H_upper': Hupper,
            'upper_unavailable_reason': None if Hupper is not None else 'nonpositive_d_minus_g_method_inconclusive_not_covariance_singularity'}


def local_certificate(R, enclosure, a, h):
    proof = sandwich(R, enclosure['Vc'], enclosure['E'])
    lower = display_terms(proof['H_lower'], a, h)
    upper = display_terms(proof['H_upper'], a, h) if proof['H_upper'] is not None else None
    return {'sandwich': proof, 'display_lower': lower, 'display_upper': upper,
            'bounds': (lower['lower'], upper['upper'] if upper else None),
            'upper_unavailable_reason': proof['upper_unavailable_reason']}


@dataclass(frozen=True)
class Family:
    a: tuple
    h: tuple
    box: tuple
    models: tuple
    pairs: tuple = PAIRS


def model_geometry(p):
    contrasts = {row['name']: tuple(map(rational, row['row'])) for row in p['contrasts']}
    out = []
    for model in p['models']:
        R = tuple(contrasts[name] for name in model['constraints'])
        X = transpose(tuple(tuple(map(rational, p['allowed_mean_columns'][name])) for name in model['allowed_columns']))
        require(all(x > 0 for x in minors(mm(R, transpose(R)))), 'contrast rank')
        require(all(x > 0 for x in minors(mm(transpose(X), X))), 'mean-column rank')
        require(len(R) == model['residual_df'] and len(R) + len(X[0]) == 4, 'rank/nullspace dimension')
        require(not any(x for row in mm(R, X) for x in row), 'allowed nullspace')
        out.append({'id': model['id'], 'R': R, 'X': X, 'df': len(R), 'cutoff': rational(p['cutoffs'][str(len(R))]),
                    'rank_and_nullspace_verified': True})
    return tuple(out)


def family_from_projection(p, projected):
    f = p['family']
    e, s = projected['certificate'], projected['source']
    a = tuple(map(rational, e['x']))
    sc = tuple(map(rational, e['s']))
    P = matrix(e['rho'])
    pairs = tuple(map(tuple, f['rho_pairs']))
    rc = tuple(P[i][j] for i, j in pairs)
    require(a == tuple(map(rational, f['fixed_anchors'])) and sc == tuple(map(rational, f['s_center_ppm']))
            and rc == tuple(map(rational, f['rho_center'])), 'family centers differ from projection')
    require(P == correlation(rc, pairs) and matrix(e['V']) == covariance(a, sc + rc, pairs), 'baseline absolute V identity')
    require(e['order'] == s['order'] == f['input_order'], 'input order')
    inherited = projected['protocol']['inputs']
    require(inherited['order'] == e['order'], 'frozen order')
    for i, row in enumerate(inherited['measurements']):
        require(row['id'] == s[f'row_{i}_id'] == e['order'][i], 'row association')
        require(rational(row['G_decimal_in_1e_minus_11_units']) == a[i] == rational(s[f'row_{i}_G_decimal_in_1e_minus_11_units']), 'Table16 values')
        require(rational(row['relative_standard_uncertainty_ppm']) == sc[i] == rational(s['s'][i]), 'Table18 diagonal')
        require(tuple(map(rational, inherited['correlation_matrix'][i])) == P[i] == tuple(map(rational, s['rho'][i])), 'Table18 correlations')
        inherited_cell = e['cells'][i]
        require((rational(inherited_cell['low']), rational(inherited_cell['high'])) == cell(a[i], f['x_half_width']), 'central display cells')
    for k, value in projected['protocol']['authorization'].items():
        require(e['authorization']['decisions'][k] == projected['authorization']['decision'][k] == value, 'authorization')
    for key in ('contrasts', 'models', 'allowed_mean_columns', 'cutoffs'):
        require(projected['models'][key] == p[key], 'inherited model restriction')
    h = (rational(f['x_half_width']),) * 4
    box = tuple(cell(v, f['s_half_width_ppm']) for v in sc) + tuple(cell(v, f['rho_half_width']) for v in rc)
    return Family(a, h, box, model_geometry(p), pairs)


def intersect_bounds(local, parent):
    lo = max(local[0], parent[0])
    available = [v for v in (local[1], parent[1]) if v is not None]
    hi = min(available) if available else None
    require(hi is None or lo <= hi, 'contradictory certified bounds')
    return lo, hi


def classify(bounds, cutoff, witness_classes):
    lo, hi = bounds
    require(lo >= 0 and (hi is None or lo <= hi), 'valid bounds')
    require(set(witness_classes) <= {'flagged', 'not_flagged'}, 'witness classes')
    if lo > cutoff:
        require('not_flagged' not in witness_classes, 'universal flag contradicts witness')
        return FLAG
    if hi is not None and hi <= cutoff:
        require('flagged' not in witness_classes, 'universal nonflag contradicts witness')
        return NONFLAG
    if {'flagged', 'not_flagged'} <= set(witness_classes):
        return VARIATION
    return UNRESOLVED


def splittable_dimension(box, original):
    candidates = [i for i in range(len(box)) if box[i][1] > box[i][0] and original[i][1] > original[i][0]]
    if not candidates:
        return None
    return max(candidates, key=lambda i: ((box[i][1] - box[i][0]) / (original[i][1] - original[i][0]), -i))


def child_boxes(box, dimension):
    lo, hi = box[dimension]
    mid = (lo + hi) / 2
    require(lo < mid < hi, 'positive split width')
    left, right = list(box), list(box)
    left[dimension], right[dimension] = (lo, mid), (mid, hi)
    return tuple(left), tuple(right)


def ordered_paths(paths):
    return sorted(paths, key=lambda path: (len(path), path))


def validate_cover(nodes, frontier, root_box):
    require('' in nodes and len(frontier) == len(set(frontier)), 'unique frontier and root')
    seen = set()
    leaves = []
    def visit(path, expected):
        require(path in nodes and path not in seen, 'missing/cyclic tree node')
        seen.add(path)
        node = nodes[path]
        require(node['box'] == expected, 'node box does not cover declared parent')
        dimension = node['split_dimension']
        if dimension is None:
            leaves.append(path)
        else:
            require(dimension == splittable_dimension(expected, root_box), 'normalized split order')
            children = child_boxes(expected, dimension)
            for bit, box in zip('01', children):
                visit(path + bit, box)
    visit('', root_box)
    require(seen == set(nodes), 'orphan nodes')
    require(set(frontier) == set(leaves), 'frontier must cover every branch')
    return True


def global_bounds(nodes, frontier, ident):
    bounds = [nodes[path]['models'][ident]['effective_bounds'] for path in frontier]
    return min(b[0] for b in bounds), None if any(b[1] is None for b in bounds) else max(b[1] for b in bounds)


def point_state(family, model, parameters, x, V=None, W=None):
    require(all(lo <= v <= hi for v, (lo, hi) in zip(parameters, family.box)), 'witness covariance membership')
    require(len(x) == 4 and all(a - h <= v <= a + h for a, h, v in zip(family.a, family.h, x)), 'witness x membership')
    actual = covariance(family.a, parameters, family.pairs)
    require(V is None or V == actual, 'witness must be actual source candidate')
    V = actual
    P = correlation(parameters[4:], family.pairs)
    require(all(v > 0 for v in minors(P)) and all(v > 0 for v in minors(V)), 'witness SPD')
    C = mm(mm(model['R'], V), transpose(model['R']))
    if W is None:
        W = inverse(C)
    require(mm(C, W) == eye(len(C)), 'witness inverse')
    y = mv(model['R'], x)
    Q = quadratic(W, y)
    return {'x': x, 's': parameters[:4], 'rho': parameters[4:], 'V': V, 'C': C, 'Q': Q,
            'cutoff': model['cutoff'], 'classification': 'flagged' if Q > model['cutoff'] else 'not_flagged',
            'parameter_membership_verified': True, 'P_leading_minors': minors(P), 'V_leading_minors': minors(V)}


def verify_witness(family, model, witness):
    actual = point_state(family, model, witness['s'] + witness['rho'], witness['x'])
    require(actual == {k: v for k, v in witness.items() if k not in ('node', 'attempt_index')}, 'witness arithmetic/metadata')
    return actual['classification']


def witness_x_points(family):
    vertices = product(*(cell(a, h) for a, h in zip(family.a, family.h)))
    return tuple(dict.fromkeys((family.a, *vertices)))


def evaluate(family, max_splits=255):
    require(type(max_splits) is int and 0 <= max_splits <= 255, 'bounded split budget')
    require(len(family.a) == len(family.h) == 4 and all(h >= 0 for h in family.h), 'central family')
    validity = family_validity(family.box, family.pairs)
    ids = [m['id'] for m in family.models]
    require(len(ids) == len(set(ids)) and ids, 'unique model inventory')
    if validity['status'] != 'POSITIVE_DEFINITE_FULL_BOX':
        return {'family_validity': validity, 'models': {i: {'disposition': DOMAIN, 'bounds': (F(0), None),
                'upper_unavailable_reason': 'declared_box_contains_non_PD_corner_PD_subset_not_analyzed'} for i in ids},
                'nodes': {}, 'frontier': [], 'splits': 0, 'evaluated_nodes': 0, 'stop_reason': 'invalid_covariance_domain'}
    nodes, witnesses, baseline = {}, {i: {} for i in ids}, {}
    status = {i: UNRESOLVED for i in ids}
    points = witness_x_points(family)
    def add(path, box):
        enclosure = covariance_enclosure(family.a, box, family.pairs)
        parent = nodes[path[:-1]] if path else None
        node = {'box': box, 'parent': path[:-1] if path else None, 'split_dimension': None,
                'enclosure': enclosure, 'models': {}, 'witness_attempts': {}}
        for model in family.models:
            ident = model['id']
            proof = local_certificate(model['R'], enclosure, family.a, family.h)
            inherited = parent['models'][ident]['effective_bounds'] if parent else (F(0), None)
            effective = intersect_bounds(proof['bounds'], inherited)
            node['models'][ident] = {'local': proof, 'effective_bounds': effective, 'parent_proof': path[:-1] if path else None}
            parameters, V = enclosure['parameters_center'], enclosure['Vc']
            W = inverse(mm(mm(model['R'], V), transpose(model['R'])))
            if not path:
                baseline[ident] = point_state(family, model, parameters, family.a, V, W)
            attempts = 0
            if status[ident] == UNRESOLVED:
                for index, x in enumerate(points):
                    witness = point_state(family, model, parameters, x, V, W)
                    attempts += 1
                    Q = witness['Q']
                    require(effective[0] <= Q and (effective[1] is None or Q <= effective[1]), 'witness escapes certificate')
                    cls = witness['classification']
                    if cls not in witnesses[ident]:
                        witnesses[ident][cls] = {**witness, 'node': path, 'attempt_index': index}
                node['witness_attempts'][ident] = attempts
            else:
                node['witness_attempts'][ident] = 0
        nodes[path] = node
    add('', family.box)
    frontier = ['']
    splits = 0
    while True:
        validate_cover(nodes, frontier, family.box)
        for model in family.models:
            ident = model['id']
            for witness in witnesses[ident].values():
                verify_witness(family, model, witness)
            bounds = global_bounds(nodes, frontier, ident)
            for witness in witnesses[ident].values():
                require(bounds[0] <= witness['Q'] and (bounds[1] is None or witness['Q'] <= bounds[1]), 'global certificate contradiction')
            status[ident] = classify(bounds, model['cutoff'], witnesses[ident])
        if all(s != UNRESOLVED for s in status.values()):
            stop = 'all_models_resolved'
            break
        if splits == max_splits:
            stop = 'frozen_split_budget_exhausted'
            break
        eligible = []
        for path in ordered_paths(frontier):
            node = nodes[path]
            if splittable_dimension(node['box'], family.box) is not None and any(
                status[m['id']] == UNRESOLVED and classify(node['models'][m['id']]['effective_bounds'], m['cutoff'], {}) == UNRESOLVED
                for m in family.models):
                eligible.append(path)
        if not eligible:
            stop = 'no_eligible_splittable_leaf'
            break
        path = eligible[0]
        dimension = splittable_dimension(nodes[path]['box'], family.box)
        nodes[path]['split_dimension'] = dimension
        for bit, box in zip('01', child_boxes(nodes[path]['box'], dimension)):
            add(path + bit, box)
        frontier = ordered_paths([p for p in frontier if p != path] + [path + '0', path + '1'])
        splits += 1
    results = {}
    for model in family.models:
        ident = model['id']
        bounds = global_bounds(nodes, frontier, ident)
        results[ident] = {'disposition': status[ident], 'bounds': bounds, 'cutoff': model['cutoff'],
                         'upper_unavailable_reason': None if bounds[1] is not None else 'at_least_one_frontier_upper_unavailable',
                         'witnesses': witnesses[ident], 'midpoint': baseline[ident]}
    return {'family_validity': validity, 'models': results, 'nodes': nodes, 'frontier': frontier,
            'splits': splits, 'evaluated_nodes': len(nodes), 'final_leaves': len(frontier), 'stop_reason': stop,
            'complete_cover_verified': validate_cover(nodes, frontier, family.box), 'budget_limit': max_splits}


def validate_protocol(p):
    require(isinstance(p, dict) and digest(serialize_artifact(p).encode()) == FREEZE_DIGEST,
            'unsupported or incomplete v1 frozen protocol/schema')
    return p


def project_records(p, records):
    """Container hashes provide custody; only these selectors enter computation."""
    require(set(records) == set(p['upstream_records']), 'upstream role inventory')
    projected = {}
    for role, pin in p['upstream_records'].items():
        fields = {}
        for key, field in pin['fields'].items():
            value = at(records[role], field['path'])
            require(value == field['value'], 'changed selected field: ' + role + '.' + key)
            fields[key] = value
        projected[role] = fields
    return projected


def expected_attestation(p):
    return {'schema_version': 1, 'artifact_id': STEM + '_source_attestation_v1',
            'freeze_sha256': FREEZE_DIGEST, 'anchor': ANCHOR, 'review_qualification': PROVISIONAL,
            'source_evidence': p['source_evidence'], 'rounding_policy_origin': p['family']['rounding_policy_origin'],
            'source_rounding_convention_verified': False,
            'serialization_phase': 'after_GitHub_anchor; earlier_receipt_and_authorship_dates_retained',
            'machine_validation_limit': 'Semantic agreement and byte custody do not authenticate the publication or complete independent audit.'}


def validate_evidence(p, attestation, receipt_raw, image_raw):
    require(attestation == expected_attestation(p), 'structured source/reader/locator attribution differs')
    e = p['source_evidence']
    require(digest(receipt_raw) == e['receipt_sha256'] and _json(receipt_raw) == e['receipt'], 'original receipt differs')
    require(digest(image_raw) == e['receipt']['image']['sha256'] and len(image_raw) == e['receipt']['image']['size_bytes'], 'PNG byte custody')
    t = e['receipt']['gpt_image_transcription_and_comparison']
    f = p['family']
    require(t['order'] == f['input_order'] and t['relative_standard_uncertainty_ppm'] == f['s_center_ppm'], 'crop diagonal association')
    require([(r['i'], r['j']) for r in t['upper_triangle']] == [tuple(pair) for pair in f['rho_pairs']], 'crop pair association')
    require([r['value'] for r in t['upper_triangle']] == f['rho_center'], 'crop pair value')
    require(e['image_repository_path'] == IMAGE and e['receipt_repository_path'] == RECEIPT, 'capsule path mapping')
    return True


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True).stdout


def verify_preregistration(root=ROOT):
    raw = verify_preregistration_freeze(root, baseline=BASE, commit=FREEZE,
                                       path=PREREGISTRATION_PATH.as_posix(), sha256=FREEZE_DIGEST)
    return validate_protocol(_json(raw))


def first_introductions(root, paths, freeze=FREEZE, anchor=ANCHOR):
    found = {}
    stamp = lambda s: datetime.fromisoformat(s.replace('Z', '+00:00'))
    anchor_time = stamp(anchor['created_at'])
    require(anchor['event'] == 'draft_pull_request_created' and anchor['freeze_head'] == freeze
            and anchor['outcome_blind'] is False, 'anchor identity')
    for t in git(root, 'show', '-s', '--format=%aI%n%cI', freeze).decode().splitlines():
        require(stamp(t) < anchor_time, 'freeze precedes actual draft creation')
    for path in paths:
        candidates = git(root, 'log', '--full-history', '--diff-filter=A', '--format=%H', '--', path).decode().splitlines()
        additions = []
        for sha in dict.fromkeys(candidates):
            parents = git(root, 'rev-list', '--parents', '-n', '1', sha).decode().split()[1:]
            if not any(subprocess.run(['git', '-C', str(root), 'cat-file', '-e', parent + ':' + path],
                                       capture_output=True).returncode == 0 for parent in parents):
                additions.append(sha)
        require(len(additions) == 1, 'unique full-history source introduction: ' + path)
        sha = additions[0]
        require(sha != freeze, 'source cannot precede external anchor')
        git(root, 'merge-base', '--is-ancestor', freeze, sha)
        for t in git(root, 'show', '-s', '--format=%aI%n%cI', sha).decode().splitlines():
            require(stamp(t) > anchor_time, 'source/result introduction after anchor')
        found[path] = sha
    return found


def verify_implementation_chronology(root=ROOT):
    require(ANCHOR['url'] == 'https://github.com/mdiaz4052/The-Number-Project/pull/52'
            and ANCHOR['created_at'] == '2026-09-11T19:01:42Z', 'recorded GitHub anchor')
    return first_introductions(root, (MODULE, MUTATOR, *TESTS, ATTESTATION.as_posix(), IMAGE, RECEIPT, SPEC))


def source_snapshot(root, paths):
    """A pure merge inheriting every relevant path is not a new source state."""
    candidates = git(root, 'log', '--full-history', '--format=%H', '--', *paths).decode().splitlines()
    sha = None
    for candidate in candidates:
        parents = git(root, 'rev-list', '--parents', '-n', '1', candidate).decode().split()[1:]
        inherited = False
        for parent in parents:
            diff = subprocess.run(['git', '-C', str(root), 'diff', '--quiet', parent, candidate, '--', *paths], capture_output=True)
            require(diff.returncode in (0, 1), 'parent-state comparison')
            if diff.returncode == 0:
                inherited = True
                break
        if not inherited:
            sha = candidate
            break
    require(sha is not None, 'committed source state required')
    verify_committed_source_state(root, sha, source_paths=paths, artifact_label=STEM)
    hashes = {}
    for path in paths:
        raw = (root / path).read_bytes()
        require(raw == git(root, 'show', sha + ':' + path), 'commit all source bytes before emission: ' + path)
        hashes[path] = digest(raw)
    return {'source_commit_sha': sha, 'source_sha256': hashes}


def load_records(p, root=ROOT):
    records = {}
    for role, pin in p['upstream_records'].items():
        raw = (root / pin['path']).read_bytes()
        require(pin['base_sha'] == BASE and digest(raw) == pin['sha256'], 'upstream base/digest pin')
        require(raw == git(root, 'show', BASE + ':' + pin['path']), 'upstream original bytes')
        records[role] = _json(raw)
    return records


def prepare(root=ROOT):
    p = verify_preregistration(root)
    require(tuple(p['closure']['source_snapshot']) == SOURCE_PATHS, 'declared source closure')
    chronology = verify_implementation_chronology(root)
    snapshot = source_snapshot(root, SOURCE_PATHS)
    for path, sha in p['planned_surfaces']['helper_sha256'].items():
        require(snapshot['source_sha256'][path] == sha, 'shared helper changed')
    require(snapshot['source_sha256'][SPEC] == p['source_evidence']['specification_delivered_sha256'], 'supplied specification custody')
    validate_evidence(p, _json((root / ATTESTATION).read_bytes()), (root / RECEIPT).read_bytes(), (root / IMAGE).read_bytes())
    return p, chronology, snapshot


def outward_decimal(x, upper=False):
    if x is None:
        return None
    with localcontext() as c:
        c.prec = 30
        c.rounding = ROUND_CEILING if upper else ROUND_FLOOR
        return format(Decimal(x.numerator) / Decimal(x.denominator), 'f')


def build_artifact(root=ROOT):
    p, chronology, snapshot = prepare(root)
    projected = project_records(p, load_records(p, root))
    family = family_from_projection(p, projected)
    result = evaluate(family, p['refinement']['max_binary_splits'])
    return {'schema_version': 1, 'artifact_id': p['experiment_id'], 'objective': p['objective'], 'outcome_blind': False,
            'review_qualification': PROVISIONAL, 'input_projection': projected, 'family_policy': p['family'],
            'exact_family': exact_tree({'anchors': family.a, 'x_half_widths': family.h, 'covariance_parameter_cells': family.box,
                                       'models': family.models, 'pairs': family.pairs}),
            'results': exact_tree(result), 'readability_only_outward_bounds': {
                ident: [outward_decimal(row['bounds'][0]), outward_decimal(row['bounds'][1], True)]
                for ident, row in result['models'].items()},
            'method': p['method'], 'refinement': p['refinement'], 'decision_policy': p['decisions'],
            'source_evidence': p['source_evidence'], 'claim_limits': p['claim_limits'], 'inherited_review': p['review'],
            'prior_knowledge_disclosure_only': p['prior_knowledge'], 'read_closure': p['closure'],
            'provenance': {'base': BASE, 'freeze': FREEZE, 'freeze_sha256': FREEZE_DIGEST, 'anchor': ANCHOR,
                           'first_introductions': chronology, **snapshot}}


def render_note(artifact):
    result = artifact['results']
    lines = ['# NIST published-covariance precision robustness', '', PROVISIONAL, '',
             'Under the project-declared nearest-rounding enclosure and fixed displayed-midpoint normalization:', '',
             '| Model | Certified outer Q bounds | Cutoff | Disposition |', '|---|---|---|---|']
    for ident, row in result['models'].items():
        lo, hi = artifact['readability_only_outward_bounds'][ident]
        cutoff = outward_decimal(rational(row['cutoff'])) if 'cutoff' in row else 'not evaluated'
        lines.append(f"| {ident} | [{lo}, {hi if hi is not None else 'upper unavailable'}] | {cutoff} | {row['disposition']} |")
    lines += ['', 'A robust flag means every member of this declared precision family exceeds that model’s cutoff. '
              'A robust non-flag means none exceeds it; this is not model acceptance. Variation requires two checked '
              'admissible point witnesses on opposite sides. Straddling outer bounds alone are inconclusive.', '',
              f"The study used {result['splits']} of 255 shared binary splits and {result['evaluated_nodes']} evaluated nodes. "
              f"Stop reason: `{result['stop_reason']}`. Covariance validity: `{result['family_validity']['status']}`.", '',
              'The exact JSON contains the full partition, retained frontier, exact rational proof terms and witnesses. '
              'Decimals above round outward and are readability only. Bounds need not be attained extrema.', '',
              '## Certificate argument', '',
              'The correlation matrix is affine in six shared off-diagonal entries. The 64 corner matrices have their '
              'exact leading principal minors recorded. If all are positive, their convex hull is positive definite. '
              'Positive diagonal D and full-row-rank R then give positive-definite V and C throughout. '
              'This corner argument certifies matrix validity, not extrema of Q.', '',
              'At each covariance subbox center, exact LDL gives Cc=L diag(d) Lᵀ and T=L⁻¹. With Z=TR, '
              'entrywise interval arithmetic provides |V−Vc|≤E. Thus |Z(V−Vc)Zᵀ|≤F=|Z|E|Z|ᵀ. '
              'Writing g as F’s row sums, symmetry and 2|vᵢvⱼ|≤vᵢ²+vⱼ² give |vᵀWv|≤Σgᵢvᵢ². '
              'Hence diag(d−g)≤TCTᵀ≤diag(d+g) in matrix order. Positive-definite inversion reverses '
              'order: conjugate by a square root to reduce to eigenvalues ≥1, whose reciprocals are ≤1. '
              'The identity Q=(TRx)ᵀ(TCTᵀ)⁻¹(TRx) therefore yields the recorded Hlower/Hupper. '
              'If any d−g is nonpositive, this upper method is unavailable; the real covariance can still be positive definite.', '',
              'For x=a+δ, |δᵢ|≤hᵢ, expand xᵀHx=aᵀHa+2δᵀHa+δᵀHδ. PSD makes the last term nonnegative '
              'for the lower bound. The upper bound retains both B=2Σhᵢ|(Ha)ᵢ| and E=Σhᵢhⱼ|Hᵢⱼ|. '
              'The resulting full central-box interval is [max(0,q−B),q+B+E]. Parent bounds intersect child bounds; '
              'every retained leaf remains in the full cover. Zero covariance widths reproduce the #49 display enclosure exactly.', '',
              '## Meaning and provenance', '',
              'The 14-parameter box simultaneously encloses printed x, s and rho at half-widths 0.0000005 U, 0.05 ppm '
              'and 0.005. It is a deterministic conditional enclosure, not extra experimental uncertainty or a probability '
              'distribution. The source caption does not establish nearest rounding. D uses immutable a, never perturbed x; '
              'other normalization rules and hidden author values are not certified. All four restrictions use full marginal '
              'RVRᵀ, profiled nuisance means and the inherited strict Q>cutoff convention; equality is not flagged.', '',
              'Miguel reported reading the NIST-served PDF on September 10, 2026 at 12:04 PM, timezone unspecified. '
              'His report arrived at 16:13:05Z and image at 16:15:53Z. GPT’s image comparison separately reconciled '
              'rho03=0.12 and rho12=0.23 against the transposed typed report; the original text is retained unchanged. '
              'Claude inspected the supplied crop in the September 10 supplemental audit and accepted the earlier #49 '
              'numerical/behavior layer. That is inherited coverage, not independent review of this PR.', '',
              'The new attestation maps the unchanged receipt and PNG into the repository. Image hashes bind PNG bytes '
              'only. Document identity, URL and page are attributed; the crop does not show them. Table 16 central values '
              'remain inherited from the pinned records. No original-PDF authentication, independent retrieval, new human '
              'confirmation or Claude-owned finding closure is claimed.', '',
              'No new/corrected G, covariance completion, model selection, p-value, confidence interval, posterior, '
              'causal explanation or universality inference is produced. The Gaussian/known-covariance interpretation '
              'is an inherited working assumption at each candidate. Omitted physical uncertainty and the parked '
              'torque-response/campaign-uncertainty NO-GOs remain outside this result. No outreach or correspondence.', '',
              f"Base: `{BASE}`. Freeze: `{FREEZE}`. Actual GitHub draft creation: `{ANCHOR['created_at']}`. "
              f"Source snapshot: `{artifact['provenance']['source_commit_sha']}`. `outcome_blind=false`.", '',
              'Use a true merge commit; preserve freeze, source and artifact ancestry.']
    return '\n'.join(lines) + '\n'


def verify_output_chronology(root, source, paths):
    first_introductions(root, paths)
    output_state = source_snapshot(root, paths)['source_commit_sha']
    require(output_state != source, 'outputs must follow committed sources')
    git(root, 'merge-base', '--is-ancestor', source, output_state)


def check_artifact(root=ROOT):
    expected = build_artifact(root)
    raw = (root / OUTPUT).read_bytes()
    require(_json(raw) == expected and raw == serialize_artifact(expected).encode(), 'stale/noncanonical or invalid saved certificate')
    require((root / NOTE).read_text() == render_note(expected), 'generated note stale')
    verify_output_chronology(root, expected['provenance']['source_commit_sha'], (OUTPUT.as_posix(), NOTE))
    return expected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.check:
            artifact = check_artifact()
            print('NIST covariance precision certificate verified: ' + ', '.join(
                key + '=' + row['disposition'] for key, row in artifact['results']['models'].items()))
        else:
            artifact = build_artifact()
            (ROOT / OUTPUT).write_text(serialize_artifact(artifact))
            (ROOT / NOTE).write_text(render_note(artifact))
    except (PrecisionError, SourceVerificationError, OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as error:
        print('nist_covariance_precision_invalid: ' + str(error), file=sys.stderr)
        raise SystemExit(1) from error


SOURCE_PATHS = ('Discovery/nist_2026_covariance_precision.py',
 'Discovery/nist_2026_covariance_precision_mutations.py',
 'tests/test_nist_2026_covariance_precision.py',
 'tests/test_nist_2026_covariance_precision_mutations.py',
 'Experiments/GMeasurements/nist_2026_covariance_precision_preregistration_v1.json',
 'Experiments/GMeasurements/nist_2026_covariance_precision_source_attestation_v1.json',
 'Experiments/GMeasurements/SourceEvidence/nist_2026_table18_miguel_20260910.png',
 'Experiments/GMeasurements/SourceEvidence/nist_2026_table18_receipt_20260910.json',
 'Notes/NIST2026CovariancePrecisionSpecification.md',
 'Discovery/__init__.py',
 'Discovery/preregistration_history.py',
 'Discovery/source_history.py',
 'Discovery/mutation_test_runner.py',
 'Experiments/GMeasurements/nist_2026_estimator_feasibility_v1.json',
 'Experiments/GMeasurements/nist_2026_n4_experimental_estimator_v1.json',
 'Experiments/GMeasurements/nist_2026_n4_experimental_estimator_preregistration_v1.json',
 'Experiments/GMeasurements/nist_2026_estimator_source_attestation_v1.json',
 'Experiments/GMeasurements/nist_2026_configuration_models_preregistration_v1.json')


if __name__ == "__main__":
    main()
