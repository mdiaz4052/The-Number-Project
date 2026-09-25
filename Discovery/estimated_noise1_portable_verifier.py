"""Detached read-only correction for platform-dependent libm exp provenance.

No new observations, fits, estimates, decisions, or scientific allowances.
The original verifier/reference and every scientific byte remain immutable.
"""
from decimal import Decimal, localcontext
import hashlib
import itertools
import math
from unittest.mock import patch

from Discovery.estimated_noise1_reference import dec, require, source_draw


def exp_binding(stored, exponent):
    """Verify a faithfully rounded exp using 80-digit independent arithmetic.

    A stored binary64 must be within one binary64 ULP of exact exp(exponent).
    This is an explicit post-outcome portability check, not a tolerance on
    observations, estimates, scores, or scientific decision cutoffs. All stored
    input bytes remain additionally bound by the pre-discovery commitments.
    """
    require(type(stored) is float and math.isfinite(stored) and stored > 0,
            'positive finite binary64 exp value')
    with localcontext() as ctx:
        ctx.prec = 80
        exact = dec(exponent).exp()
        nearest = float(exact)
        require(math.isfinite(nearest) and nearest > 0, 'finite reference exp')
        require(abs(dec(stored)-exact) <= dec(math.ulp(nearest)),
                'independent exp provenance exceeds one ULP')


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
        exp_binding(bank['coefficient'], source_draw(child, 'law', 0, *g['coefficient_log_range']))
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
                    exponent = bank['centers'][k]+source_draw(child, split+':inputs', 3*i+j, *ranges[k])
                    exp_binding(row['features'][k], exponent)
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


def check():
    from Discovery import estimated_noise1_verifier as original
    from Discovery.estimated_noise1 import ROOT, git, blob, sha
    from Discovery.estimated_noise1_calibration import loads
    path = 'Notes/EstimatedNoise1/portable_verifier_manifest.json'
    manifest = loads((ROOT/path).read_bytes())
    commits = git('log', '--format=%H', '--', path).splitlines()
    require(len(commits) == 1, 'single detached correction epoch')
    epoch = commits[0]
    require(blob(epoch, path) == (ROOT/path).read_bytes(), 'committed correction manifest')
    original.ancestor(manifest['original_failed_head'], epoch)
    original.ancestor(epoch, git('rev-parse', 'HEAD'))
    for name, digest in manifest['source_manifest'].items():
        require(sha(blob(epoch, name)) == sha((ROOT/name).read_bytes()) == digest,
                'detached correction source pin '+name)
    for name, digest in manifest['unchanged_package_sources'].items():
        require(sha(blob(manifest['scientific_source'], name)) == sha((ROOT/name).read_bytes()) == digest,
                'unchanged package-local verifier dependency '+name)
    for name, digest in manifest['failure_evidence'].items():
        require(sha(blob(epoch, name)) == sha((ROOT/name).read_bytes()) == digest,
                'original CI failure retention '+name)
    # Temporary process-local replacement only; original source stays untouched.
    with patch.object(original.reference, 'generation', generation):
        result = original.check()
    return {**result, 'verification_route': 'detached-portable-exp-v1',
            'verifier_source_sha': epoch}


def main():
    import argparse
    from Discovery.estimated_noise1_calibration import encoded
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check'])
    parser.parse_args()
    print(encoded(check()).decode(), end='')


if __name__ == '__main__': main()
