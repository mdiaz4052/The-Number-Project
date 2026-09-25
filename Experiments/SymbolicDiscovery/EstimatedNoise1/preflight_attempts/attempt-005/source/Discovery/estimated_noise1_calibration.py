"""Pair-only estimator. This entire module is safe for the calibration stage.

No generator, discovery, filesystem, truth, or project-policy imports. Settings
are the five declared estimator constants, not the full preregistration.
"""
import hashlib
import json
import math


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def loads(raw):
    def bad(value):
        raise ValueError('nonfinite JSON: ' + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad)


def keys(obj, names):
    if type(obj) is not dict or set(obj) != set(names):
        raise ValueError('missing or extra schema fields')


def number(value, *, positive=False):
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ValueError('finite non-boolean number required')
    if positive and value <= 0:
        raise ValueError('positive observation required')
    return value


def validate(payload):
    keys(payload, ('dataset_id', 'pairs', 'settings'))
    if type(payload['dataset_id']) is not str or not payload['dataset_id']:
        raise ValueError('dataset identity required')
    s = payload['settings']
    keys(s, ('alpha', 'budgets', 'pair_count', 'pad', 'floor', 'multiplier'))
    if not 0 < number(s['alpha']) < 1:
        raise ValueError('invalid alpha')
    if type(s['pair_count']) is not int or s['pair_count'] < 1:
        raise ValueError('invalid pair count')
    if (type(s['budgets']) is not list or not s['budgets'] or
            any(type(m) is not int or not 1 <= m <= s['pair_count'] for m in s['budgets']) or
            sorted(set(s['budgets'])) != s['budgets']):
        raise ValueError('invalid fixed prefixes')
    if number(s['pad']) < 0 or number(s['floor']) < 0 or number(s['multiplier']) <= 0:
        raise ValueError('invalid numerical policy')
    pairs = payload['pairs']
    if type(pairs) is not list or len(pairs) != s['pair_count']:
        raise ValueError('wrong pair inventory')
    for i, pair in enumerate(pairs):
        keys(pair, ('pair_id', 'response_1', 'response_2'))
        if pair['pair_id'] != f'p{i+1:03d}':
            raise ValueError('unordered or duplicate pair identity')
        number(pair['response_1'], positive=True)
        number(pair['response_2'], positive=True)
    return s, pairs


def estimate(payload):
    s, pairs = validate(payload)
    estimates = {}
    for m in s['budgets']:
        prefix = pairs[:m]
        differences = [math.log(p['response_1']) - math.log(p['response_2']) for p in prefix]
        sumsq = math.fsum(d*d for d in differences)
        maximum = max(abs(d) for d in differences)
        q = 1 - math.sqrt(-math.expm1(math.log(s['alpha']) / m))
        if not math.isfinite(q) or not 0 < q < 1:
            raise ValueError('invalid upper quantile')
        point = math.sqrt(1.5 * sumsq / m)
        ideal = maximum / (2*q)
        upper = (maximum + s['pad']) / (2*q)
        estimates[str(m)] = {
            'n': m, 'prefix_sha256': digest(prefix), 'sum_squared_differences': sumsq,
            'maximum_absolute_difference': maximum, 'point': point, 'q': q,
            'ideal_upper': ideal, 'padded_upper': upper, 'pad': s['pad'],
            'point_threshold': s['multiplier']*point + s['floor'],
            'upper95_threshold': s['multiplier']*upper + s['floor']}
    return {'dataset_id': payload['dataset_id'], 'input_sha256': digest(payload),
            'estimates': estimates}
