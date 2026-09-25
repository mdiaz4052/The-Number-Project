"""Ten source-mutated semantic engineering checks; exceptions are not kills."""
import copy
import math
from pathlib import Path
import types

from Discovery import estimated_noise1_calibration as calibration
from Discovery import estimated_noise1_science as science
from Discovery import estimated_noise1_selection as selection
from Discovery import estimated_noise1_fixtures as fixtures


class SemanticFailure(AssertionError): pass


def assertion(test, name):
    if not test: raise SemanticFailure(name)


def mutated(module, old, new):
    text = Path(module.__file__).read_text()
    if text.count(old) != 1: raise RuntimeError('mutation target must be unique')
    altered = text.replace(old, new)
    copy_module = types.ModuleType(module.__name__+'_engineering_mutant')
    copy_module.__file__ = module.__file__
    exec(compile(altered, '<estimated-noise1-engineering-mutant>', 'exec'), copy_module.__dict__)
    return copy_module


def rejected(call):
    try: call()
    except ValueError: return True
    return False


def check_estimator(module, mode):
    payload = fixtures.pair_payload()
    expected = calibration.estimate(payload)
    if mode == 'M4':
        payload['true_epsilon'] = .000123
        assertion(rejected(lambda: module.estimate(payload)), 'PAIR_ONLY_SCHEMA')
        return
    actual = module.estimate(payload)
    for m in ('16', '64', '256'):
        a, e = actual['estimates'][m], expected['estimates'][m]
        key, label = {'M1': ('point', 'HALF_WIDTH_MOMENT'), 'M2': ('q', 'LOWER_TAIL_QUANTILE'),
                      'M3': ('padded_upper', 'PRESCRIBED_PAD'), 'M5': ('prefix_sha256', 'FIXED_PREFIX')}[mode]
        assertion(a[key] == e[key], label)


def check_science(module, mode):
    if mode == 'M6':
        ranking = [{'validation_rmse': .02}, {'validation_rmse': .01}]
        assertion(module.assess(ranking, .015)['family_rejected'] is False, 'FAMILY_MINIMUM_NOT_RANK1')
    elif mode == 'M7':
        r = module.assess([{'validation_rmse': .02}], .02)
        assertion(r['family_rejected'] is False and r['rank1_decision'] == 'stable_candidate', 'EQUALITY_ACCEPTED')
    elif mode == 'M9':
        assertion(module.credit(False, True, True, [.001]*3, .01, 0., True) is False, 'CURVATURE_NEVER_EXACT_CREDIT')
    elif mode == 'M10':
        assertion(module.disposition(96, 0, violations=[], missing_evidence=[], accounted=True)['disposition'] ==
                  'ESTIMATED_NOISE_1_NO_GO', 'FAILURE_CANNOT_BECOME_COMPLETE')
        assertion(module.disposition(96, 96, violations=['contract'], missing_evidence=['missing'], accounted=True)['disposition'] ==
                  'ESTIMATED_NOISE_1_FAIL', 'FAILURE_CANNOT_BECOME_COMPLETE')


def check_heldout(module):
    p = fixtures.policy()
    public, heldout, _ = fixtures.observations(p)
    poisoned = {**public, 'heldout': heldout}
    assertion(rejected(lambda: module.discovery_payload(poisoned, science.policy(p, .01))), 'HELDOUT_INPUT_DENIED')


SPECS = {
    'M1': (calibration, 'point = math.sqrt(1.5 * sumsq / m)', 'point = math.sqrt(0.5 * sumsq / m)', 'HALF_WIDTH_MOMENT'),
    'M2': (calibration, 'math.log(s[\'alpha\']) / m', 'math.log(1-s[\'alpha\']) / m', 'LOWER_TAIL_QUANTILE'),
    'M3': (calibration, "upper = (maximum + s['pad']) / (2*q)", 'upper = maximum / (2*q)', 'PRESCRIBED_PAD'),
    'M4': (calibration, "keys(payload, ('dataset_id', 'pairs', 'settings'))",
           "keys({k: v for k, v in payload.items() if k != 'true_epsilon'}, ('dataset_id', 'pairs', 'settings'))", 'PAIR_ONLY_SCHEMA'),
    'M5': (calibration, 'prefix = pairs[:m]',
           "prefix = sorted(pairs, key=lambda p: abs(math.log(p['response_1'])-math.log(p['response_2'])), reverse=True)[:m]", 'FIXED_PREFIX'),
    'M6': (science, "family = min(c['validation_rmse'] for c in ranking)", "family = ranking[0]['validation_rmse']", 'FAMILY_MINIMUM_NOT_RANK1'),
    'M7': (science, "'family_rejected': family > threshold", "'family_rejected': family >= threshold", 'EQUALITY_ACCEPTED'),
    'M8': (selection, 'schema.validate(public, schema.PUBLIC)',
           "public = {**public, 'train': public['train']+public.get('heldout', [])}\n    public.pop('heldout', None)\n    schema.validate(public, schema.PUBLIC)", 'HELDOUT_INPUT_DENIED'),
    'M9': (science, 'return bool(in_family and signature_match', 'return bool(signature_match', 'CURVATURE_NEVER_EXACT_CREDIT'),
    'M10': (science, "'disposition': 'ESTIMATED_NOISE_1_'+state", "'disposition': 'ESTIMATED_NOISE_1_COMPLETE'", 'FAILURE_CANNOT_BECOME_COMPLETE')}


def execute_check(module, mid):
    if mid in ('M1', 'M2', 'M3', 'M4', 'M5'): check_estimator(module, mid)
    elif mid == 'M8': check_heldout(module)
    else: check_science(module, mid)


def run():
    for mid, (module, _, _, _) in SPECS.items(): execute_check(module, mid)
    equivalent = mutated(calibration, 'point = math.sqrt(1.5 * sumsq / m)',
                         'point = math.sqrt((1.5 * sumsq) / m)')
    for mid in ('M1', 'M2', 'M3', 'M4', 'M5'): execute_check(equivalent, mid)
    results = {}
    for mid, (module, old, new, label) in SPECS.items():
        try:
            execute_check(mutated(module, old, new), mid)
        except SemanticFailure as exc:
            if str(exc) != label: raise RuntimeError('wrong designated mutation assertion') from exc
            results[mid] = {'status': 'KILLED', 'designated_assertion': label, 'observed_assertion': str(exc)}
        except Exception as exc:
            raise RuntimeError(mid+' crashed before its designated assertion; not a kill') from exc
        else:
            raise RuntimeError(mid+' survived its designated semantic assertion')
    return {'baseline': 'SURVIVED', 'equivalent_control': 'SURVIVED', 'mutants': results}


if __name__ == '__main__':
    from Discovery.estimated_noise1_calibration import encoded
    print(encoded(run()).decode(), end='')
