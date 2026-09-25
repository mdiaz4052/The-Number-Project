"""Forward Suite 1 interpretation of the unchanged internal observation adapter.

No generator, oracle, realization identity, files, or heldout API. Finite-data
family adequacy and useful approximation are separate, sealed observations.
"""
from Discovery.symbolic_benchmark_engine import discover as baseline_discover
from Discovery.symbolic_benchmark_engine import prepare as baseline_prepare
from Discovery.symbolic_benchmark_engine import exact_keys, digest

EXTRA_POLICY = {'approximation_rmse_max'}


def base_payload(payload):
    result = dict(payload)
    result['policy'] = {k: v for k, v in payload['policy'].items() if k not in EXTRA_POLICY}
    return result


def prepare(raw):
    payload, eligibility = baseline_prepare(base_payload(raw))
    payload['policy'].update({k: raw['policy'][k] for k in EXTRA_POLICY})
    return payload, eligibility


def discover(payload):
    import math
    from Discovery.symbolic_benchmark_engine import POLICY_KEYS
    exact_keys(payload['policy'], POLICY_KEYS | EXTRA_POLICY)
    approximation = payload['policy']['approximation_rmse_max']
    if type(approximation) not in (float, int) or not math.isfinite(approximation) or approximation < 0:
        raise ValueError('invalid approximation policy')
    result = baseline_discover(base_payload(payload))
    result['input_sha256'] = digest(payload)
    ranking = result['ranking']
    best = min((c['validation_rmse'] for c in ranking), default=None)
    result['family_assessment'] = ('no_candidate_capability' if best is None else
        'family_inadequate_on_validation' if best > payload['policy']['acceptance_validation_rmse'] else
        'contains_validation_adequate_member')
    result['minimum_validation_rmse'] = best
    result['approximation_status'] = ('predictive_approximation' if ranking and
        ranking[0]['validation_rmse'] <= approximation else 'poor_approximation')
    result['structural_recovery_claim'] = False
    return result
