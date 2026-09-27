"""Independent 80-digit arithmetic; no production estimator/evaluator imports."""
from decimal import Decimal, localcontext
import hashlib
import itertools
import math


def dec(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('reference requires finite non-boolean number')
    return Decimal.from_float(value) if type(value) is float else Decimal(value)


def require(test, message):
    if not test:
        raise ValueError(message)


def calibration(pairs, settings, estimates, intended=None):
    """Numerical oracle uses observed binary64 inputs, not production differences."""
    with localcontext() as ctx:
        ctx.prec = 80
        logs = {v: dec(v).ln() for r in pairs for v in (r['response_1'], r['response_2'])}
        diffs = [logs[r['response_1']]-logs[r['response_2']] for r in pairs]
        float_diffs = [math.log(r['response_1'])-math.log(r['response_2']) for r in pairs]
        observed_errors = [abs(dec(x)-y) for x, y in zip(float_diffs, diffs)]
        intended_errors = ([] if intended is None else [abs(d-dec(v)) for d, v in zip(diffs, intended)])
        require(intended is None or len(intended) == len(pairs), 'intended difference inventory')
        require(max(observed_errors, default=Decimal(0)) <= dec(settings['pad']), 'numeric difference pad exceeded')
        require(max(intended_errors, default=Decimal(0)) <= dec(settings['pad']), 'intended difference pad exceeded')
        rows = {}
        for m in settings['budgets']:
            e = estimates[str(m)]
            q = 1-(1-(dec(settings['alpha']).ln()/dec(m)).exp()).sqrt()
            inversion = (2*q-q*q)**m
            require(abs(inversion-dec(settings['alpha'])) < Decimal('1e-65'), 'quantile inversion')
            require(abs(dec(e['q'])-q) < Decimal('1e-14'), 'wrong upper quantile')
            maximum = max(abs(v) for v in diffs[:m])
            sumsq = sum(v*v for v in diffs[:m])
            point = (Decimal('1.5')*sumsq/dec(m)).sqrt()
            ideal = maximum/(2*q)
            padded = (maximum+dec(settings['pad']))/(2*q)
            for key, value in (('sum_squared_differences', sumsq), ('maximum_absolute_difference', maximum),
                               ('point', point), ('ideal_upper', ideal), ('padded_upper', padded)):
                require(abs(dec(e[key])-value) <= Decimal('1e-12'), 'independent calibration '+key)
            require(dec(e['padded_upper']) >= ideal, 'pad fails to cover ideal numeric underestimate')
            if intended is not None:
                intended_ideal = max(abs(dec(v)) for v in intended[:m])/(2*q)
                require(dec(e['padded_upper']) >= intended_ideal, 'pad fails intended-error upper bound')
            rows[str(m)] = {'quantile_absolute_error': float(abs(dec(e['q'])-q)),
                           'ideal_upper_absolute_error': float(abs(dec(e['ideal_upper'])-ideal)),
                           'point_absolute_error': float(abs(dec(e['point'])-point)),
                           'pad_covers_underestimate': True}
        return {'pair_count': len(pairs), 'max_observed_log_difference_error': float(max(observed_errors)),
                'max_intended_difference_error': float(max(intended_errors)) if intended_errors else None,
                'budgets': rows, 'pass': True}


def candidate_arithmetic(public, ranking, *, heldout=None, truth=None, metrics=None):
    with localcontext() as ctx:
        ctx.prec = 80
        rows = {}
        max_error = Decimal(0)
        for c in ranking:
            def residual(row, intercept):
                return intercept+sum(dec(int(e))*dec(row['features'][k]).ln()
                                     for k, e in c['expanded'].items())-dec(row['target']).ln()
            intercept = -sum(residual(r, Decimal(0)) for r in public['train'])/len(public['train'])
            discrepancy = abs(dec(c['log_coefficient'])-intercept)
            require(discrepancy <= Decimal('1e-10'), 'training-only intercept mismatch')
            coefficient_relative_error = abs(dec(c['coefficient'])/intercept.exp()-1)
            require(coefficient_relative_error <= Decimal('1e-10'), 'coefficient arithmetic mismatch')
            per = {'log_coefficient_error': float(discrepancy),
                   'coefficient_relative_numeric_error': float(coefficient_relative_error)}
            for split, actual in [('train', public['train']), ('validation', public['validation'])] + (
                    [('heldout', heldout)] if heldout is not None else []):
                # Evaluate the sealed intercept, never replace it with the oracle fit.
                residuals = [residual(r, dec(c['log_coefficient'])) for r in actual]
                error = (sum(v*v for v in residuals)/len(actual)).sqrt()
                key = 'training_rmse' if split == 'train' else split+'_rmse'
                reported = c[key] if split != 'heldout' else metrics[c['class_id']]['heldout_rmse']
                delta = abs(dec(reported)-error)
                require(delta <= Decimal('1e-10'), 'independent candidate metric '+key)
                max_error = max(max_error, delta)
                per[key+'_error'] = float(delta)
                if truth is not None and truth['in_family'] and c['expanded'] == truth['base_signature']:
                    require(max(abs(v) for v in residuals) <= 2*dec(truth['epsilon'])+Decimal('1e-10'),
                            'adequate member residual exceeds 2 epsilon allowance')
            rows[c['class_id']] = per
        return {'classes': rows, 'max_metric_error': float(max_error), 'pass': True}


def source_draw(seed, name, counter, low, high):
    """Independent statement of the prescribed finite stream, used after reveal."""
    h = hashlib.sha256(f'{seed}:{name}:{counter}'.encode()).digest()
    return low+(high-low)*(int.from_bytes(h[:8], 'big')/2**64)


def generation(p, public, calibration_records, heldout, oracle):
    """Read-only provenance checks of retained inputs/draws. No generated bank returned."""
    g, d, seed = p['generation'], p['design'], oracle['seed']
    order = list(itertools.product(range(16), range(2), range(3)))
    order.sort(key=lambda t: (hashlib.sha256(
        (seed+':estimated-noise1:anon:'+':'.join(map(str, t))).encode()).hexdigest(), t))
    mapping = {f'd{i+1:03d}': t for i, t in enumerate(order)}
    require(set(public) == set(calibration_records) == set(heldout) == set(oracle['datasets']) == set(mapping),
            'all-96 generation inventory')
    require(set(oracle['blocks']) == set(map(str, range(16))), 'block inventory')
    max_response_error = Decimal(0)
    for b in range(16):
        bank = oracle['blocks'][str(b)]
        child = hashlib.sha256(f'{seed}:estimated-noise1:block:{b}'.encode()).hexdigest()
        require(child == bank['child_seed'], 'block seed binding')
        require(bank['exponent'] == d['stratified_exponents'][b], 'stratified exponent')
        require(bank['coefficient'] == math.exp(source_draw(child, 'law', 0, *g['coefficient_log_range'])),
                'coefficient draw')
        for i, k in enumerate(g['feature_order'], 1):
            require(bank['centers'][k] == source_draw(child, 'law', i, *g['scale_center_log_ranges'][k]),
                    'center draw including zero-width draw')
        for split in ('train', 'validation', 'heldout', 'calibration'):
            rows = bank['calibration'] if split == 'calibration' else bank['splits'][split]
            expected_count = d['calibration_pairs_per_dataset'] if split == 'calibration' else d['discovery_rows'][split]
            require(len(rows) == expected_count, 'row count')
            ranges = g['heldout_offset_log_ranges' if split == 'heldout' else 'base_offset_log_ranges']
            for i, row in enumerate(rows):
                for j, k in enumerate(g['feature_order']):
                    value = math.exp(bank['centers'][k]+source_draw(child, split+':inputs', 3*i+j, *ranges[k]))
                    require(row['features'][k] == value, 'feature stream binding')
                if split == 'calibration':
                    require(row['pair_id'] == f'p{i+1:03d}', 'ordered calibration pair')
                    for n in (1, 2):
                        require(row[f'u{n}'] == source_draw(child, f'calibration:noise:{n}', i, -1, 1),
                                'independent repeat stream')
                else:
                    require(row['u'] == source_draw(child, split+':noise', i, -1, 1), 'split noise stream')
    with localcontext() as ctx:
        ctx.prec = 80
        for rid, (b, ci, ni) in mapping.items():
            truth = oracle['datasets'][rid]
            bank = oracle['blocks'][str(b)]
            condition, epsilon = d['conditions'][ci], d['noise_half_widths'][ni]
            beta = g['adequate_beta'] if condition == 'adequate' else g['curved_beta']
            expected = {'block': b, 'condition': condition, 'noise_index': ni, 'epsilon': epsilon,
                'coefficient': bank['coefficient'], 'exponent': bank['exponent'], 'beta': beta,
                'in_family': condition == 'adequate',
                'base_signature': {'t': '-2', 'x': '1', 'z': str(bank['exponent'])}}
            require(truth == expected, 'anonymous condition mapping / truth binding')
            require(public[rid]['features'] == p['features'] and public[rid]['target'] == p['grammar']['target'],
                    'public registry')
            for split in ('train', 'validation', 'heldout', 'calibration'):
                raw = calibration_records[rid] if split == 'calibration' else heldout[rid] if split == 'heldout' else public[rid][split]
                source = bank['calibration'] if split == 'calibration' else bank['splits'][split]
                require(len(raw) == len(source), 'matched row inventory')
                for row, origin in zip(raw, source):
                    v = origin['features']
                    lz = dec(v['z']).ln()
                    clean = (dec(bank['coefficient']).ln()+dec(v['x']).ln()-2*dec(v['t']).ln()+
                             dec(bank['exponent'])*lz+dec(beta)*lz*lz)
                    responses = [(row[f'response_{n}'], origin[f'u{n}']) for n in (1, 2)] if split == 'calibration' else [(row['target'], origin['u'])]
                    if split != 'calibration':
                        require(row['features'] == v and row['group'] == 'g0', 'matched features')
                    else:
                        require(row['pair_id'] == origin['pair_id'], 'calibration matching')
                    for response, u in responses:
                        delta = abs(dec(response).ln()-(clean+dec(epsilon)*dec(u)))
                        max_response_error = max(max_response_error, delta)
                        require(delta <= Decimal('1e-12'), 'generated response numeric error')
    return {'pass': True, 'anonymous_datasets': 96, 'blocks': 16,
            'discovery_observations': sum(len(public[r]['train'])+len(public[r]['validation'])+len(heldout[r]) for r in mapping),
            'calibration_response_values': 2*sum(len(calibration_records[r]) for r in mapping),
            'max_response_log_error': float(max_response_error), 'matching_and_streams_verified': True}
