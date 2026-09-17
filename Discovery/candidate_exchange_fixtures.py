"""Visible deterministic fixtures, never generated scientific observations."""
from copy import deepcopy
import json
from pathlib import Path
from Discovery import candidate_exchange as cx

PACKAGE = Path(__file__).resolve().parents[1] / 'Experiments/SymbolicDiscovery/CandidateExchange1'


def manifest(dimensionless=False):
    acc = {} if dimensionless else {'L': 1, 'T': -2}
    def q(role, dimension, definition=None, domain='real'):
        return {'role': role, 'dimension': dimension, 'unit': 'dimensionless' if not dimension else 'coherent_si',
                'domain': domain, 'definition': definition, 'dependencies': list(definition or {})}
    inp = cx.sha(b'visible fixture input context; no observations or fitting')
    return {'schema': cx.NS + '/manifest', 'target': 'y',
        'quantities': {'x': q('observed', {} if dimensionless else {'L': 1}),
            't': q('observed', {} if dimensionless else {'T': 1}), 'z': q('observed', {}),
            'y': q('target', acc), 'direct': q('derived', acc, {'y': 1}),
            'transitive': q('alias', acc, {'direct': 1})},
        'parameters': {'k': {'dimension': {}, 'unit': 'dimensionless', 'role': 'training_fitted',
            'fit_context': {'split': 'fixture_training', 'input_digest': inp}}},
        'sources': ['visible_fixture_definition'], 'splits': {'training': 'fixture_training',
            'validation': 'fixture_validation', 'withheld': 'withheld_not_supplied'},
        'input_digest': inp, 'uncertainty': {'status': 'exact_by_design', 'references': ['fixture_design']},
        'dependence': {'status': 'unknown', 'references': []}, 'allowed_ops': cx.OPS, 'opaque': {}}


def lit(n, d=1): return {'op': 'literal', 'number': {'kind': 'exact', 'numerator': n, 'denominator': d}}
def var(name): return {'op': 'variable', 'name': name}
def power(arg, exponent): return {'op': 'power', 'arg': arg, 'exponent': exponent}
def mul(*args): return {'op': 'multiply', 'args': list(args)}
def add(*args): return {'op': 'add', 'args': list(args)}
def div(a, b): return {'op': 'divide', 'numerator': a, 'denominator': b}
def log(a): return {'op': 'log', 'arg': a}
def exp(a): return {'op': 'exp', 'arg': a}


def tree_item(expression, params=None, claims=None):
    return {'id': 'visible-case', 'expression': expression, 'parameters': params or {},
            'diagnostics': {}, 'claims': claims or {}, 'display': 'inert display', 'opaque': {}}


def raw(items, m, fmt='mock-tree/1', status='success', failure=None):
    return cx.encoded({'schema': fmt, 'manifest_digest': cx.digest(m), 'manifest_echo': None,
        'items': items, 'status': status, 'failure': failure, 'metadata': {}})


def paired():
    return json.loads((PACKAGE / 'mock_pairs.json').read_text())


def fixed_points():
    return [{'name': 'two', 'values': {'x': 8.0, 't': 2.0, 'z': 1.0}},
            {'name': 'log_e', 'values': {'x': 18.0, 't': 3.0, 'z': 2.718281828459045}}]
