"""Deterministic engineering fixtures, never prospective scientific observations."""
import copy
import itertools
import math
from pathlib import Path

from Discovery.estimated_noise1_calibration import loads, estimate
from Discovery import estimated_noise1_science as science
from Discovery import estimated_noise1_reference as reference
from Discovery import estimated_noise1_schema as schema

ROOT = Path(__file__).resolve().parents[1]


def policy():
    return loads((ROOT/'Experiments/SymbolicDiscovery/EstimatedNoise1/preregistration.v1.json').read_bytes())['science']


def pair_payload(*, alpha=0.05, budgets=None, pad=1e-12):
    # Deliberately different prefix distributions make magnitude selection detectable.
    differences = [0.0002*(1+i%7) if i < 64 else 0.01*(1+i%3) for i in range(256)]
    return {'dataset_id': 'engineering-pairs',
        'pairs': [{'pair_id': f'p{i+1:03d}', 'response_1': math.exp(d), 'response_2': 1.0}
                  for i, d in enumerate(differences)],
        'settings': {'alpha': alpha, 'budgets': budgets or [16, 64, 256], 'pair_count': 256,
                     'pad': pad, 'floor': 1e-9, 'multiplier': 2.0}}


def observations(p=None, *, exponent=-2, beta=0., epsilon=0.0016, coefficient=1.):
    p = p or policy()
    result = {}
    for si, (split, count) in enumerate((('train', 64), ('validation', 48), ('heldout', 64))):
        rows = []
        for i in range(count):
            # Analytic grid; no scientific Stream/seed or historical outcome input.
            x = math.exp(-1+2*((i*7+si)%count)/(count-1))
            t = math.exp(-.6+1.2*((i*11+si)%count)/(count-1))
            z = math.exp(-1+2*((i*13+si)%count)/(count-1))
            u = -1+2*((i*17+si)%count)/(count-1)
            logy = math.log(coefficient)+math.log(x)-2*math.log(t)+exponent*math.log(z)+beta*math.log(z)**2
            rows.append({'features': {'x': x, 't': t, 'z': z},
                         'target': math.exp(logy+epsilon*u), 'group': 'g0'})
        result[split] = rows
    public = {'features': p['features'], 'target': p['grammar']['target'],
              'train': result['train'], 'validation': result['validation']}
    truth = {'block': 0, 'condition': 'adequate' if beta == 0 else 'curved', 'noise_index': 1,
             'epsilon': epsilon, 'coefficient': coefficient, 'exponent': exponent, 'beta': beta,
             'in_family': beta == 0, 'base_signature': {'t': '-2', 'x': '1', 'z': str(exponent)}}
    return public, result['heldout'], truth


def discovery_payload(public, p, threshold):
    schema.validate(public, schema.PUBLIC)
    return {**public, 'policy': science.policy(p, threshold)}


def numerical_corners():
    p = policy()
    reports = []
    # Every corner of coefficient/feature ranges, both laws, all exponent strata,
    # all scientific epsilons plus exact-zero and tiny-error safeguards.
    for logk, xlog, tlog, zlog, exponent, beta, epsilon in itertools.product(
            (-3., 3.), (-3., 3.), (-1.6, 1.6), (-1., 1.), (-2, -1, 1, 2),
            (0., .01), (0., 1e-16, .0001, .0016, .005)):
        clean = logk+xlog-2*tlog+exponent*zlog+beta*zlog*zlog
        payload = pair_payload()
        pairs, intended = [], []
        for i in range(256):
            u1, u2 = ((-1., 1.) if i%3 == 0 else (1., -1.) if i%3 == 1 else (.5, .5))
            pairs.append({'pair_id': f'p{i+1:03d}', 'response_1': math.exp(clean+epsilon*u1),
                          'response_2': math.exp(clean+epsilon*u2)})
            intended.append(epsilon*(u1-u2))
        payload['pairs'] = pairs
        e = estimate(payload)
        reports.append(reference.calibration(pairs, payload['settings'], e['estimates'], intended))
    alternate = []
    for alpha, budgets in ((.1, [3, 17, 127]), (.01, [1, 32, 256])):
        payload = pair_payload(alpha=alpha, budgets=budgets)
        alternate.append(reference.calibration(payload['pairs'], payload['settings'], estimate(payload)['estimates']))
    return {'corners': len(reports), 'pass': all(r['pass'] for r in reports+alternate),
            'max_log_difference_error': max(r['max_observed_log_difference_error'] for r in reports),
            'max_intended_difference_error': max(r['max_intended_difference_error'] for r in reports),
            'alternate_policy_cases': len(alternate)}
