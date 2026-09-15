"""Trusted Suite 1 synthetic generator, excluded from staged engine closure."""
import hashlib
import math


class Stream:
    def __init__(self, seed, name):
        self.seed, self.name, self.counter = seed, name, 0

    def uniform(self, low=0., high=1.):
        value = hashlib.sha256(f'{self.seed}:{self.name}:{self.counter}'.encode()).digest()
        self.counter += 1
        return low + (high-low) * (int.from_bytes(value[:8], 'big') / 2**64)

    def choice(self, values):
        return values[min(int(self.uniform() * len(values)), len(values)-1)]


def child_seed(seed, cell, replicate):
    return hashlib.sha256(f'{seed}:suite1:{cell}:{replicate}'.encode()).hexdigest()


def policy_for(prereg, epsilon):
    scoring = prereg['scoring']
    return {**{k: prereg['grammar'][k] for k in ('max_factors', 'max_abs_power', 'max_denominator')},
        'complexity_lambda': scoring['complexity_lambda'],
        'acceptance_validation_rmse': scoring['adequacy_noise_multiplier']*epsilon + scoring['numeric_floor'],
        'approximation_rmse_max': scoring['approximation_rmse_max']}


def definitions(values, target, metadata):
    known = {**values, 'y': target}
    pending = {k: s['definition'] for k, s in metadata.items() if s['definition'] is not None}
    while pending:
        ready = [k for k, v in pending.items() if set(v) <= known.keys()]
        if not ready:
            raise ValueError('unresolved operational definition')
        for k in ready:
            known[k] = math.prod(known[a] ** p for a, p in pending.pop(k).items())
    return {k: known[k] for k in metadata}


def generate(prereg, seed):
    if len(seed) != 64 or any(c not in '0123456789abcdef' for c in seed):
        raise ValueError('invalid 256-bit seed')
    g = prereg['generation']
    public, heldout, truths = {}, {}, {}
    for cell in prereg['design']['cells']:
        spec = prereg['cells'][cell]
        for rep in range(prereg['design']['replicates_per_cell']):
            rid = f'{cell}-{rep+1:02d}'
            seed_i = child_seed(seed, cell, rep)
            law = Stream(seed_i, 'law')
            coefficient = math.exp(law.uniform(*g['coefficient_log_range']))
            centers = {k: law.uniform(*v) for k, v in g['scale_center_log_ranges'].items()}
            domain = g['curve_exponent_domain'] if cell == 'wrong_curve' else g['exponent_domain']
            exponent = law.choice(domain)
            if cell == 'wrong_power':
                exponent = g['wrong_power_exponent']
            beta = law.uniform(*g['curve_beta_range']) if cell == 'wrong_curve' else 0.
            multiplier = law.choice(g['regime_multiplier_domain']) if cell == 'regime' else 1.
            meta = {k: prereg['features'][k] for k in spec['features']}
            splits = {}
            for split, count in g['sample_counts'].items():
                stream, noise, nuisance = (Stream(seed_i, split+':'+kind) for kind in ('inputs','noise','nuisance'))
                ranges = g['heldout_offset_log_ranges' if split == 'heldout' else 'base_offset_log_ranges']
                paired = spec.get('paired_all_splits', False)
                rows = []
                for i in range(count//2 if paired else count):
                    values = {k: math.exp(centers[k]+stream.uniform(*ranges[k])) for k in ('x','t','z')}
                    log_clean = math.log(coefficient)+math.log(values['x'])-2*math.log(values['t'])+exponent*math.log(values['z'])+beta*math.log(values['z'])**2
                    if cell == 'nuisance':
                        n = g['nuisance']
                        values['n0'] = math.exp(nuisance.uniform(*n['n0_log_range']))
                        width = spec['epsilon']*n['n1_half_width_noise_ratio']
                        values['n1'] = math.exp(nuisance.uniform(-width,width))
                        fraction = 0 if split == 'train' else n[split+'_independent_q_fraction']
                        independent = i >= count*(1-fraction)
                        values['q'] = (math.exp(centers['x']+nuisance.uniform(*ranges['x'])) if independent else
                            values['x']*math.exp(nuisance.uniform(-n['q_correlated_log_jitter'],n['q_correlated_log_jitter'])))
                    for group in ('g0','g1') if paired else ('g0',):
                        target = math.exp(log_clean + noise.uniform(-spec['epsilon'],spec['epsilon'])) * (multiplier if group == 'g1' else 1)
                        rows.append({'features':definitions(values,target,meta),'target':target,'group':group})
                splits[split] = rows
            public[rid] = {'features':meta,'target':prereg['grammar']['target'],
                'train':splits['train'],'validation':splits['validation'],'policy':policy_for(prereg,spec['epsilon'])}
            heldout[rid] = splits['heldout']
            adequate = cell in ('clean','leakage','nuisance')
            truths[rid] = {'cell':cell,'replicate':rep,'child_seed':seed_i,'coefficient':coefficient,'scale_centers':centers,
                'exponent':exponent,'curve_beta':beta,'regime_multiplier':multiplier,'epsilon':spec['epsilon'],
                'in_family':adequate,'base_signature':{'x':'1','t':'-2','z':str(exponent)},
                'irrelevant_atoms':['n0','n1','q'] if cell == 'nuisance' else [],
                'forbidden_features':[k for k in meta if k.startswith('leak')],
                'wrong_grammar_proof':spec.get('proof')}
    return public, heldout, {'seed':seed,'generator_version':g['version'],'realizations':truths}
