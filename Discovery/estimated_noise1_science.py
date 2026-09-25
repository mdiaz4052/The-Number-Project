"""Private generation and post-seal evaluation. Never staged into either worker."""
import hashlib
import itertools
import math
import statistics

from Discovery.estimated_noise1_calibration import digest, keys, number


def identities():
    return [f'd{i:03d}' for i in range(1, 97)]


def settings(p):
    return {'alpha': p['estimation']['alpha'], 'budgets': p['design']['calibration_budgets'],
            'pair_count': p['design']['calibration_pairs_per_dataset'],
            'pad': p['estimation']['numeric_difference_pad'], 'floor': p['scoring']['numeric_floor'],
            'multiplier': p['scoring']['adequacy_multiplier']}


def policy(p, threshold):
    return {**{k: p['grammar'][k] for k in ('max_factors', 'max_abs_power', 'max_denominator')},
            'complexity_lambda': p['scoring']['complexity_lambda'],
            'approximation_rmse_max': p['scoring']['approximation_rmse_max'],
            'acceptance_validation_rmse': threshold}


def expected_signatures(p):
    """Independent integer enumeration from declared dimensions, not engine count."""
    g, features = p['grammar'], p['features']
    if g['max_denominator'] != 1:
        raise ValueError('this contract requires integer exponents')
    axes = set(g['target']['dimension']) | {a for f in features.values() for a in f['dimension']}
    names = sorted(features)
    result = {}
    for exps in itertools.product(range(-g['max_abs_power'], g['max_abs_power']+1), repeat=len(names)):
        if sum(e != 0 for e in exps) > g['max_factors']:
            continue
        if all(sum(e*features[k]['dimension'].get(a, 0) for k, e in zip(names, exps)) ==
               g['target']['dimension'].get(a, 0) for a in axes):
            sig = {k: str(e) for k, e in zip(names, exps) if e}
            result['|'.join(k+':'+e for k, e in sig.items()) or '1'] = sig
    return result


def generate(p, seed):
    from Discovery.symbolic_suite_worlds import Stream
    if type(seed) is not str or len(seed) != 64 or any(c not in '0123456789abcdef' for c in seed):
        raise ValueError('invalid master seed')
    g, d = p['generation'], p['design']
    tuples = list(itertools.product(range(d['independent_blocks']), range(2), range(3)))
    tuples.sort(key=lambda t: (hashlib.sha256(
        (seed+':estimated-noise1:anon:'+':'.join(map(str, t))).encode()).hexdigest(), t))
    mapping = {t: f'd{i+1:03d}' for i, t in enumerate(tuples)}
    public, calibration, heldout, truths, blocks = {}, {}, {}, {}, {}
    for b, exponent in enumerate(d['stratified_exponents']):
        child = hashlib.sha256(f'{seed}:estimated-noise1:block:{b}'.encode()).hexdigest()
        law = Stream(child, 'law')
        coefficient = math.exp(law.uniform(*g['coefficient_log_range']))
        centers = {k: law.uniform(*g['scale_center_log_ranges'][k]) for k in g['feature_order']}
        splits = {}
        for split, count in d['discovery_rows'].items():
            inputs, noise = Stream(child, split+':inputs'), Stream(child, split+':noise')
            ranges = g['heldout_offset_log_ranges' if split == 'heldout' else 'base_offset_log_ranges']
            splits[split] = [{'features': {k: math.exp(centers[k]+inputs.uniform(*ranges[k]))
                for k in g['feature_order']}, 'u': noise.uniform(-1, 1)} for _ in range(count)]
        inputs = Stream(child, 'calibration:inputs')
        n1, n2 = Stream(child, 'calibration:noise:1'), Stream(child, 'calibration:noise:2')
        pairs = [{'pair_id': f'p{i+1:03d}', 'features': {
                    k: math.exp(centers[k]+inputs.uniform(*g['base_offset_log_ranges'][k]))
                    for k in g['feature_order']}, 'u1': n1.uniform(-1, 1), 'u2': n2.uniform(-1, 1)}
                 for i in range(d['calibration_pairs_per_dataset'])]
        blocks[str(b)] = {'child_seed': child, 'coefficient': coefficient, 'centers': centers,
                          'exponent': exponent, 'splits': splits, 'calibration': pairs}
        for c, condition in enumerate(d['conditions']):
            beta = g['adequate_beta'] if condition == 'adequate' else g['curved_beta']
            for ni, epsilon in enumerate(d['noise_half_widths']):
                rid = mapping[b, c, ni]
                def clean(v):
                    return (math.log(coefficient)+math.log(v['x'])-2*math.log(v['t'])+
                            exponent*math.log(v['z'])+beta*math.log(v['z'])**2)
                rows = {split: [{'features': dict(r['features']),
                         'target': math.exp(clean(r['features'])+epsilon*r['u']),
                         'group': 'g0'} for r in bank] for split, bank in splits.items()}
                public[rid] = {'features': p['features'], 'target': p['grammar']['target'],
                               'train': rows['train'], 'validation': rows['validation']}
                heldout[rid] = rows['heldout']
                calibration[rid] = [{'pair_id': r['pair_id'],
                    'response_1': math.exp(clean(r['features'])+epsilon*r['u1']),
                    'response_2': math.exp(clean(r['features'])+epsilon*r['u2'])} for r in pairs]
                truths[rid] = {'block': b, 'condition': condition, 'noise_index': ni,
                    'epsilon': epsilon, 'coefficient': coefficient, 'exponent': exponent,
                    'beta': beta, 'in_family': condition == 'adequate',
                    'base_signature': {'t': '-2', 'x': '1', 'z': str(exponent)}}
    return public, calibration, heldout, {'seed': seed, 'generator_version': g['version'],
                                        'blocks': blocks, 'datasets': truths}


def assess(ranking, threshold):
    number(threshold)
    if not ranking or threshold < 0:
        raise ValueError('assessment requires complete family and nonnegative threshold')
    family = min(c['validation_rmse'] for c in ranking)
    top = ranking[0]['validation_rmse']
    return {'threshold': threshold, 'family_validation_rmse': family,
            'rank1_validation_rmse': top, 'family_margin': family-threshold,
            'rank1_margin': top-threshold, 'family_rejected': family > threshold,
            'rank1_decision': 'stable_candidate' if top <= threshold else 'no_stable_law'}


def operational(p, discovery, estimates):
    ranking = discovery['ranking']
    inventory = expected_signatures(p)
    if (len(ranking) != len(inventory) or len(inventory) != 5 or
            {c['class_id']: c['expanded'] for c in ranking} != inventory or
            discovery['class_count'] != 5):
        raise ValueError('complete independent five-signature inventory required')
    if list(ranking) != sorted(ranking, key=lambda c: (c['rank_score'], c['expanded_complexity'], c['class_id'])):
        raise ValueError('ranking order invalid')
    for rank, c in enumerate(ranking, 1):
        complexity = sum(abs(int(e)) for e in c['expanded'].values())
        if (c['representative'] != c['expanded'] or c['members'] != [c['expanded']] or
                c['rank'] != rank or c['expanded_complexity'] != complexity or
                c['rank_score'] != c['validation_rmse']+p['scoring']['complexity_lambda']*complexity or
                c['evidence_class'] != 'GENERATED/FITTED CANDIDATE' or c['scientific_significance'] != 'not_assigned'):
            raise ValueError('candidate expression/complexity/ranking contract')
    if (discovery['surface_count'] != 5 or discovery['top_class'] != ranking[0]['class_id'] or
            discovery['equivalence_map'] != {c['class_id']: c['members'] for c in ranking}):
        raise ValueError('candidate inventory metadata')
    rules = {}
    for m in p['design']['calibration_budgets']:
        e = estimates[str(m)]
        for method in p['design']['estimated_methods']:
            rule = assess(ranking, e[method+'_threshold'])
            rule['ablations'] = {}
            for atom in sorted(p['features']):
                remaining = [c for c in ranking if any(atom not in member for member in c['members'])]
                top = remaining[0] if remaining else None
                rule['ablations'][atom] = {'removed_features': [atom],
                    'top_class': top['class_id'] if top else None,
                    'decision': 'stable_candidate' if top and top['validation_rmse'] <= rule['threshold'] else 'no_stable_law'}
            rules[f'{method}/{m}'] = rule
    primary = rules['upper95/64']
    if (discovery['decision'] != primary['rank1_decision'] or
            discovery['family_assessment'] != ('family_inadequate_on_validation' if primary['family_rejected']
                                               else 'contains_validation_adequate_member') or
            discovery['ablations'] != primary['ablations'] or discovery['structural_recovery_claim'] is not False):
        raise ValueError('primary policy disagreement')
    return {'rules': rules, 'rank1_class': ranking[0]['class_id'],
            'approximation': ranking[0]['validation_rmse'] <= p['scoring']['approximation_rmse_max'],
            'independent_inventory': inventory}


def rmse(candidate, rows):
    return math.sqrt(math.fsum((candidate['log_coefficient'] + math.fsum(
        int(e)*math.log(r['features'][k]) for k, e in candidate['expanded'].items()) -
        math.log(r['target']))**2 for r in rows)/len(rows))


def credit(in_family, signature_match, stable, errors, threshold, relative, provenance, relative_max=0.04):
    return bool(in_family and signature_match and stable and max(errors) <= threshold and
                relative <= relative_max and provenance)


def evaluate(p, selection, truth, heldout, estimates):
    ranking, op = selection['worker']['discovery']['ranking'], selection['operational']
    candidates = [{**c, 'heldout_rmse': rmse(c, heldout),
                   'base_signature_match': c['expanded'] == truth['base_signature'],
                   'exact_structural_match': truth['in_family'] and c['expanded'] == truth['base_signature']}
                  for c in ranking]
    top = candidates[0]
    relative = abs(top['coefficient']/truth['coefficient']-1)
    methods = {**op['rules'], 'known_noise': assess(ranking,
        p['scoring']['adequacy_multiplier']*truth['epsilon']+p['scoring']['numeric_floor'])}
    evaluated = {}
    for name, rule in methods.items():
        stable = rule['rank1_decision'] == 'stable_candidate'
        evaluated[name] = {**rule,
            'structural_credit': credit(truth['in_family'], top['base_signature_match'], stable,
                [top['training_rmse'], top['validation_rmse'], top['heldout_rmse']],
                rule['threshold'], relative, True, p['scoring']['coefficient_relative_error_max']),
            'curved_family_rejection': not truth['in_family'] and rule['family_rejected'],
            'curved_missed_inadequacy': not truth['in_family'] and not rule['family_rejected'],
            'adequate_family_rejection': truth['in_family'] and rule['family_rejected'],
            'adequate_rank1_abstention': truth['in_family'] and not stable,
            'stable_selection_omits_curvature': not truth['in_family'] and stable,
            'reference_disagreement': ('same' if rule['family_rejected'] == methods['known_noise']['family_rejected']
                else 'reference_reject_estimated_nonreject' if methods['known_noise']['family_rejected']
                else 'reference_nonreject_estimated_reject')}
    ratios = {}
    for budget, e in estimates.items():
        ratios[budget] = {k+'_ratio': e[k]/truth['epsilon'] for k in ('point', 'ideal_upper', 'padded_upper')}
        ratios[budget].update(ideal_covered=e['ideal_upper'] >= truth['epsilon'],
            padded_covered=e['padded_upper'] >= truth['epsilon'], ideal_width=e['ideal_upper'],
            padded_width=e['padded_upper'],
            point_threshold_ratio=e['point_threshold']/methods['known_noise']['threshold'],
            upper95_threshold_ratio=e['upper95_threshold']/methods['known_noise']['threshold'])
    return {'block': truth['block'], 'condition': truth['condition'], 'noise_index': truth['noise_index'],
            'epsilon': truth['epsilon'], 'exponent': truth['exponent'], 'interpretable': True,
            'integrity_pass': True, 'candidates': candidates, 'methods': evaluated, 'ratios': ratios,
            'rank1_base_signature_match': top['base_signature_match'],
            'exact_structural_match': top['exact_structural_match'], 'coefficient_relative_error': relative,
            'rank1_heldout_rmse': top['heldout_rmse'],
            'family_minimum_heldout_rmse': min(c['heldout_rmse'] for c in candidates),
            'heldout_approximation': top['heldout_rmse'] <= p['scoring']['approximation_rmse_max']}


def disposition(expected, interpreted, *, violations, missing_evidence, accounted):
    if type(expected) is not int or type(interpreted) is not int or not 0 <= interpreted <= expected:
        raise ValueError('invalid interpretation count')
    if type(violations) is not list or type(missing_evidence) is not list or type(accounted) is not bool:
        raise ValueError('invalid evidence status')
    state = ('FAIL' if violations else 'UNRESOLVED' if missing_evidence or not accounted else
             'NO_GO' if interpreted == 0 else 'PARTIAL' if interpreted < expected else 'COMPLETE')
    return {'disposition': 'ESTIMATED_NOISE_1_'+state,
            'evidence_integrity': 'FAIL' if violations else 'UNRESOLVED' if missing_evidence or not accounted else 'PASS'}


def spread(values):
    return {'n': len(values), 'median': statistics.median(values) if values else None,
            'min': min(values) if values else None, 'max': max(values) if values else None}


def paired(rows, first, second):
    valid = [r for r in rows if r['interpretable'] and first in r['methods'] and second in r['methods']]
    a = [r['methods'][first]['family_rejected'] for r in valid]
    b = [r['methods'][second]['family_rejected'] for r in valid]
    return {'first': first, 'second': second, 'paired_blocks': len(valid),
            'rejection_to_nonrejection': sum(x and not y for x, y in zip(a, b)),
            'nonrejection_to_rejection': sum(not x and y for x, y in zip(a, b)),
            'both_reject': sum(x and y for x, y in zip(a, b)),
            'both_nonreject': sum(not x and not y for x, y in zip(a, b))}


def aggregate(p, rows, statuses, violations, missing_evidence):
    expected = identities()
    complete = [rid for rid in expected if rid in rows and rows[rid]['interpretable'] and
                set(rows[rid]['methods']) == {'known_noise'} | {
                    f'{method}/{m}' for method in p['design']['estimated_methods'] for m in p['design']['calibration_budgets']}]
    invalid = [rid for rid, row in rows.items() if not row['integrity_pass']]
    violations = list(violations) + ['dataset integrity: '+rid for rid in invalid]
    accounted = set(statuses) == set(expected) and all(
        statuses[rid]['state'] == 'INTERPRETABLE' if rid in complete else
        statuses[rid]['state'] in ('FAILED', 'NOT_EXECUTED') and bool(statuses[rid]['reason']) for rid in expected)
    if set(rows)-set(expected):
        violations.append('unexpected dataset identities')
    result = {**disposition(96, len(complete), violations=violations,
        missing_evidence=missing_evidence, accounted=accounted),
        'expected_datasets': 96, 'interpretable_datasets': len(complete),
        'missing_or_failed_ids': [rid for rid in expected if rid not in complete],
        'dataset_status': statuses, 'violations': violations, 'missing_evidence': missing_evidence,
        'review_status': 'PROVISIONAL — INDEPENDENT AUDIT PENDING',
        'independent_blocks': 16, 'completion_is_not_successful_detection': True,
        'cells': {}, 'paired_comparisons': {}, 'budget_changes': {}, 'coverage_vectors': {}}
    labels = p['scoring']['error_labels'][:-1] + ['structural_credit']
    for condition in p['design']['conditions']:
        for ni, epsilon in enumerate(p['design']['noise_half_widths']):
            cell = f'{condition}/n{ni+1}'
            found = sorted((rows[rid] for rid in complete if rows[rid]['condition'] == condition and
                            rows[rid]['noise_index'] == ni), key=lambda r: r['block'])
            result['paired_comparisons'][cell], result['budget_changes'][cell] = {}, {}
            for method in ['known_noise'] + [f'{method}/{m}' for m in p['design']['calibration_budgets']
                                             for method in p['design']['estimated_methods']]:
                result['cells'][cell+'/'+method] = {
                    'expected': 16, 'interpretable': len(found), 'epsilon': epsilon,
                    'counts': {label: sum(r['methods'][method][label] for r in found) for label in labels},
                    'rank1_base_signature_matches': sum(r['rank1_base_signature_match'] for r in found),
                    'block_values': {str(b): next(({'family_rejected': r['methods'][method]['family_rejected'],
                        'rank1_decision': r['methods'][method]['rank1_decision'],
                        'family_margin': r['methods'][method]['family_margin'],
                        'rank1_margin': r['methods'][method]['rank1_margin'],
                        'structural_credit': r['methods'][method]['structural_credit']} for r in found if r['block'] == b), None)
                        for b in range(16)},
                    'exponent_strata': {str(e): {'expected': 4,
                        'interpretable': sum(r['exponent'] == e for r in found),
                        'counts': {label: sum(r['methods'][method][label] for r in found if r['exponent'] == e)
                                   for label in labels}} for e in (-2, -1, 1, 2)}}
                if method != 'known_noise':
                    budget = method.split('/')[1]
                    result['cells'][cell+'/'+method]['calibration'] = {
                        k: spread([r['ratios'][budget][k] for r in found]) for k in (
                            'point_ratio', 'ideal_upper_ratio', 'padded_upper_ratio', 'ideal_width',
                            'padded_width', 'point_threshold_ratio', 'upper95_threshold_ratio')}
            for m in p['design']['calibration_budgets']:
                result['paired_comparisons'][cell][str(m)] = {
                    'upper_vs_point': paired(found, f'upper95/{m}', f'point/{m}'),
                    'upper_vs_known': paired(found, f'upper95/{m}', 'known_noise'),
                    'point_vs_known': paired(found, f'point/{m}', 'known_noise')}
            for method in p['design']['estimated_methods']:
                result['budget_changes'][cell][method] = [paired(found, f'{method}/{a}', f'{method}/{b}')
                                                           for a, b in ((16, 64), (64, 256), (16, 256))]
    for m in p['design']['calibration_budgets']:
        result['coverage_vectors'][str(m)] = {str(b): {
            rid: {k: rows[rid]['ratios'][str(m)][k] for k in ('ideal_covered', 'padded_covered')}
            for rid in complete if rows[rid]['block'] == b} for b in range(16)}
    return result
