"""Frozen margin-study mathematics. Generator truth never enters staged discovery."""
import math
import hashlib
from Discovery.symbolic_suite_worlds import Stream, policy_for
from Discovery.symbolic_suite_evaluation import candidate_metrics
from Discovery.symbolic_benchmark_engine import class_id, signature


def threshold_metrics(error, epsilon, scoring):
    m, delta = scoring['adequacy_noise_multiplier'], scoring['numeric_floor']
    if not all(math.isfinite(v) for v in (error, epsilon, m, delta)) or min(error, epsilon, delta) < 0 or m <= 0:
        raise ValueError('invalid adequacy inputs')
    bound = m * epsilon + delta
    critical = (error - delta) / m
    return {'known_noise': epsilon, 'error': error, 'adequacy_bound': bound,
            'signed_margin': error - bound, 'error_bound_ratio': error / bound if bound else None,
            'inadequate': error > bound, 'critical_assumed_noise': critical,
            'critical_original_noise_ratio': critical / epsilon if epsilon else None,
            'critical_domain': 'no_nonnegative_inadequacy_region' if critical <= 0 else
                               'inadequate_below_critical_equality_adequate',
            'zero_original_noise': epsilon == 0}


def dataset_ids(p):
    return [f'b{b+1:02d}-{condition}-n{n+1}' for b in range(p['design']['independent_blocks'])
            for condition in p['design']['conditions'] for n in range(len(p['design']['noise_levels']))]


def block_seed(seed, block):
    return hashlib.sha256(f'{seed}:margin1:block:{block}'.encode()).hexdigest()


def generate(p, seed):
    if len(seed) != 64 or any(c not in '0123456789abcdef' for c in seed):
        raise ValueError('invalid seed')
    g, design = p['generation'], p['design']
    if len(design['stratified_exponents']) != design['independent_blocks']:
        raise ValueError('stratum coverage mismatch')
    public, heldout, truths = {}, {}, {}
    for b, exponent in enumerate(design['stratified_exponents']):
        child = block_seed(seed, b)
        law = Stream(child, 'law')
        coefficient = math.exp(law.uniform(*g['coefficient_log_range']))
        centers = {k: law.uniform(*g['scale_center_log_ranges'][k]) for k in ('x', 't', 'z')}
        matched = {}
        for split, count in g['sample_counts'].items():
            inputs, noise = Stream(child, split + ':inputs'), Stream(child, split + ':noise')
            ranges = g['heldout_offset_log_ranges' if split == 'heldout' else 'base_offset_log_ranges']
            matched[split] = [({k: math.exp(centers[k] + inputs.uniform(*ranges[k])) for k in ('x', 't', 'z')},
                              noise.uniform(-1, 1)) for _ in range(count)]
        for condition in design['conditions']:
            beta = g['adequate_beta'] if condition == 'adequate' else g['curvature_beta']
            for n, epsilon in enumerate(design['noise_levels']):
                rid = f'b{b+1:02d}-{condition}-n{n+1}'
                splits = {}
                for split, rows in matched.items():
                    splits[split] = []
                    for values, noise in rows:
                        clean = (math.log(coefficient) + math.log(values['x']) - 2 * math.log(values['t'])
                                 + exponent * math.log(values['z']) + beta * math.log(values['z'])**2)
                        splits[split].append({'features': dict(values), 'target': math.exp(clean + epsilon * noise), 'group': 'g0'})
                public[rid] = {'features': p['features'], 'target': p['grammar']['target'],
                               'train': splits['train'], 'validation': splits['validation'], 'policy': policy_for(p, epsilon)}
                heldout[rid] = splits['heldout']
                truths[rid] = {'block': b, 'condition': condition, 'noise_index': n, 'epsilon': epsilon,
                               'child_seed': child, 'coefficient': coefficient, 'scale_centers': centers,
                               'exponent': exponent, 'curve_beta': beta, 'in_family': condition == 'adequate',
                               'base_signature': {'x': '1', 't': '-2', 'z': str(exponent)},
                               'irrelevant_atoms': [], 'forbidden_features': [],
                               'wrong_grammar_proof': g['proof'] if condition == 'curved' else None}
    return public, heldout, {'seed': seed, 'generator_version': g['version'], 'realizations': truths}


def retrospective(p, old_pre, oracle, selections, policies):
    s = old_pre['scoring']
    rows = {}
    for rid, wrapped in selections.items():
        ranking = wrapped['discovery']['ranking']
        epsilon = oracle['realizations'][rid]['epsilon']
        bound = s['adequacy_noise_multiplier'] * epsilon + s['numeric_floor']
        if policies[rid]['policy']['acceptance_validation_rmse'] != bound:
            raise ValueError('Suite1 frozen policy disagrees')
        if not ranking:
            raise ValueError('retrospective source has empty family')
        family = min(c['validation_rmse'] for c in ranking)
        rows[rid] = {'cell': oracle['realizations'][rid]['cell'], 'retrospective_only': True,
                     'family': threshold_metrics(family, epsilon, s),
                     'rank1': threshold_metrics(ranking[0]['validation_rmse'], epsilon, s),
                     'counterfactuals': [{'assumed_noise': e,
                         'family_inadequate': family > s['adequacy_noise_multiplier'] * e + s['numeric_floor'],
                         'rank1_unstable': ranking[0]['validation_rmse'] > s['adequacy_noise_multiplier'] * e + s['numeric_floor']}
                         for e in p['retrospective']['counterfactual_assumed_noise']]}
    return {'schema': 'tnp-margin1/retrospective-v1', 'source_sha': p['retrospective']['source_sha'],
            'method': 'Read sealed residuals only; no regeneration, discovery or refit. Counterfactual assumed noise is not actual changed observation noise.',
            'adequacy_noise_multiplier': s['adequacy_noise_multiplier'], 'numeric_floor': s['numeric_floor'], 'rows': rows}


def evaluate(p, public, wrapped, truth, heldout):
    """Apply oracle/heldout after seal. All coefficients are read from sealed candidates."""
    d, s, policy = wrapped['discovery'], p['scoring'], public['policy']
    ranks = d['ranking']
    candidates = [candidate_metrics(c, heldout, truth, policy) for c in ranks]
    has = bool(ranks)
    family = threshold_metrics(min(c['validation_rmse'] for c in ranks), truth['epsilon'], s) if has else None
    top = threshold_metrics(ranks[0]['validation_rmse'], truth['epsilon'], s) if has else None
    correct = bool(has and candidates[0]['oracle_structural_match'])
    relative = abs(ranks[0]['coefficient'] / truth['coefficient'] - 1) if has and truth['in_family'] else None
    credit = bool(correct and d['decision'] == 'stable_candidate' and
                  max(ranks[0]['training_rmse'], ranks[0]['validation_rmse'], candidates[0]['heldout_rmse']) <= policy['acceptance_validation_rmse']
                  and relative <= s['coefficient_relative_error_max'] and
                  not candidates[0]['leakage_contaminated'] and not candidates[0]['nuisance_atoms'])
    if candidates:
        candidates[0]['scientific_credit'] = credit
    expected_family = ('no_candidate_capability' if not has else 'family_inadequate_on_validation' if family['inadequate']
                       else 'contains_validation_adequate_member')
    expected_decision = 'stable_candidate' if has and not top['inadequate'] else 'no_stable_law'
    # Empty enumeration's actual engine uses no_candidate; handle it as capability, never recognition.
    decision_ok = d['decision'] == expected_decision if has else d['decision'] in ('no_stable_law', 'no_candidate')
    truth_ok = (truth['exponent'] == p['design']['stratified_exponents'][truth['block']] and
                truth['epsilon'] == p['design']['noise_levels'][truth['noise_index']] and
                truth['in_family'] == (truth['condition'] == 'adequate') and
                truth['curve_beta'] == (p['generation']['adequate_beta'] if truth['in_family'] else p['generation']['curvature_beta']))
    proof = bool(truth_ok and (truth['in_family'] and truth['curve_beta'] == 0 or
                 not truth['in_family'] and truth['curve_beta'] != 0 and truth['wrong_grammar_proof'] == p['generation']['proof'])
                 and set(public['features']) == {'x', 't', 'z'} and p['grammar']['max_denominator'] == 1)
    integrity = (d['family_assessment'] == expected_family and decision_ok and proof and
                 policy == policy_for(p, truth['epsilon']) and d['structural_recovery_claim'] is False and
                 all(not c['leakage_contaminated'] and (not c['scientific_credit'] or c['oracle_structural_match']) for c in candidates))
    stable = d['decision'] == 'stable_candidate'
    inadequate = bool(has and family['inadequate'])
    return {'block': truth['block'], 'condition': truth['condition'], 'noise_index': truth['noise_index'],
            'known_noise': truth['epsilon'], 'interpretable': has, 'integrity_pass': bool(integrity),
            'family': family, 'rank1': top, 'pre_reveal_family_assessment': d['family_assessment'],
            'pre_reveal_selection_decision': d['decision'], 'pre_reveal_approximation_status': d['approximation_status'],
            'rank1_class': ranks[0]['class_id'] if has else None, 'selected_class': d['top_class'] if stable else None,
            'rank1_heldout_error': candidates[0]['heldout_rmse'] if has else None,
            'family_minimum_heldout_error': min(c['heldout_rmse'] for c in candidates) if has else None,
            'heldout_approximation': bool(has and candidates[0]['heldout_approximation']),
            'oracle_structural_match': correct, 'structural_credit': credit, 'coefficient_relative_error': relative,
            'recognized_inadequacy': inadequate and not truth['in_family'],
            'missed_inadequacy': bool(has and not inadequate and not truth['in_family']),
            'unjustified_family_rejection': inadequate and truth['in_family'],
            'adequate_control_abstention': bool(has and not stable and truth['in_family']),
            'structurally_wrong_stable_selection': stable and not correct,
            'candidate_count': len(ranks), 'candidates': candidates, 'oracle_proof_verified': proof,
            'scientific_law_claim': False}


def aggregate(p, records, integrity=True, evidence_available=True):
    expected = dataset_ids(p)
    labels = p['evaluation']['labels']
    interpreted = [v for v in records.values() if v['interpretable']]
    identities = all(rid in expected and rid == f"b{v['block']+1:02d}-{v['condition']}-n{v['noise_index']+1}"
                     for rid, v in records.items())
    good_integrity = integrity and identities and all(v['integrity_pass'] for v in records.values())
    status = ('UNRESOLVED' if not evidence_available else 'FAIL' if not good_integrity else 'NO_GO' if not interpreted else
              'COMPLETE' if set(records) == set(expected) and len(interpreted) == len(expected) else 'PARTIAL')
    cells = {}
    counts = ['recognized_inadequacy', 'missed_inadequacy', 'unjustified_family_rejection',
              'adequate_control_abstention', 'structurally_wrong_stable_selection', 'structural_credit', 'heldout_approximation']
    for condition in p['design']['conditions']:
        for n, noise in enumerate(p['design']['noise_levels']):
            found = [v for v in records.values() if v['condition'] == condition and v['noise_index'] == n]
            count = sum(v['recognized_inadequacy'] for v in found)
            cells[f'{condition}-n{n+1}'] = {'known_noise': noise, 'condition': condition,
                'expected_blocks': p['design']['independent_blocks'], 'evaluated_blocks': len(found),
                'interpretable_blocks': sum(v['interpretable'] for v in found),
                **{k: sum(v[k] for v in found) for k in counts},
                'recognition_pattern': 'all_blocks' if count == p['design']['independent_blocks'] else 'some_blocks' if count else 'no_blocks',
                'family_margin_by_block': {str(v['block']): v['family']['signed_margin'] if v['family'] else None for v in found}}
    sequences = {}
    for b in range(p['design']['independent_blocks']):
        found = [records.get(f'b{b+1:02d}-curved-n{n+1}') for n in range(len(p['design']['noise_levels']))]
        seq = [v['recognized_inadequacy'] if v and v['interpretable'] else None for v in found]
        sequences[str(b)] = {'recognized_by_increasing_noise': seq,
                            'nonmonotonic_false_to_true': any(a is False and z is True for a, z in zip(seq, seq[1:]))}
    return {'schema': 'tnp-margin1/summary-v1', 'disposition': labels[status], 'expected_datasets': len(expected),
            'interpretable_datasets': len(interpreted), 'missing_ids': sorted(set(expected) - set(records)),
            'independent_blocks': p['design']['independent_blocks'], 'matched_conditions_per_block': len(p['design']['conditions']) * len(p['design']['noise_levels']),
            'integrity_pass': bool(good_integrity), 'cells': cells, 'curved_block_sequences': sequences,
            'completion_is_not_favorable_performance': True, 'review_status': 'PROVISIONAL — INDEPENDENT AUDIT PENDING',
            'interpretation': p['design']['analysis_unit'], 'scientific_law_claim': False, 'nonclaims': p['nonclaims']}
