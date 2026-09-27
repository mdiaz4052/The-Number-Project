"""Closed schemas for the forward estimated-noise package.

Canonical-byte comparisons supplement these shape/type checks; false never
compares equal to zero across an evidence boundary.
"""
import math
import re
from Discovery.estimated_noise1_calibration import loads, encoded

NUM, NONNEG, POS, INTEGER, HASH, SHA = '@number', '@nonnegative', '@positive', '@integer', '@hash', '@sha'
def seq(spec): return ('list', spec)
def mapping(spec): return ('map', spec)
def optional(spec): return ('nullable', spec)
def enum(*values): return ('enum', values)


def validate(value, spec, path='$'):
    def fail(): raise ValueError('schema mismatch at '+path)
    if type(spec) is dict:
        if type(value) is not dict or set(value) != set(spec): fail()
        for k, s in spec.items(): validate(value[k], s, path+'.'+k)
    elif type(spec) is tuple:
        mode, sub = spec
        if mode == 'nullable':
            if value is not None: validate(value, sub, path)
        elif mode == 'enum':
            if not any(type(value) is type(x) and value == x for x in sub): fail()
        elif mode == 'map':
            if type(value) is not dict or any(type(k) is not str for k in value): fail()
            for k, v in value.items(): validate(v, sub, path+'.'+k)
        elif mode == 'list':
            if type(value) is not list: fail()
            for i, v in enumerate(value): validate(v, sub, path+f'[{i}]')
        else: fail()
    elif spec in (NUM, NONNEG, POS):
        if type(value) not in (float, int) or not math.isfinite(value): fail()
        if spec == NONNEG and value < 0 or spec == POS and value <= 0: fail()
    elif spec == INTEGER:
        if type(value) is not int: fail()
    elif spec in (HASH, SHA):
        if type(value) is not str or not re.fullmatch('[0-9a-f]{'+('64' if spec == HASH else '40')+'}', value): fail()
    elif spec in (str, bool, int, float):
        if type(value) is not spec: fail()
    elif spec is None:
        if value is not None: fail()
    else: fail()


def same(actual, expected, message):
    if encoded(actual) != encoded(expected):
        raise ValueError(message)


FEATURES = {k: POS for k in ('x', 't', 'z')}
ROW = {'features': FEATURES, 'target': POS, 'group': str}
PAIR = {'pair_id': str, 'response_1': POS, 'response_2': POS}
REGISTRY = {k: {'definition': None, 'dimension': mapping(INTEGER), 'unit': str} for k in ('x', 't', 'z')}
TARGET = {'key': str, 'dimension': mapping(INTEGER)}
PUBLIC = {'features': REGISTRY, 'target': TARGET, 'train': seq(ROW), 'validation': seq(ROW)}
POLICY = {'max_factors': INTEGER, 'max_abs_power': INTEGER, 'max_denominator': INTEGER,
          'complexity_lambda': NONNEG, 'approximation_rmse_max': NONNEG, 'acceptance_validation_rmse': NONNEG}
SETTINGS = {'alpha': POS, 'budgets': seq(INTEGER), 'pair_count': INTEGER, 'pad': NONNEG,
            'floor': NONNEG, 'multiplier': POS}
ESTIMATE = {'n': INTEGER, 'prefix_sha256': HASH, 'sum_squared_differences': NONNEG,
            'maximum_absolute_difference': NONNEG, 'point': NONNEG, 'q': POS,
            'ideal_upper': NONNEG, 'padded_upper': NONNEG, 'pad': NONNEG,
            'point_threshold': NONNEG, 'upper95_threshold': NONNEG}
CAL_RESULT = {'dataset_id': str, 'input_sha256': HASH, 'estimates': mapping(ESTIMATE)}
CANDIDATE = {'class_id': str, 'expanded': mapping(str), 'members': seq(mapping(INTEGER)),
             'representative': mapping(INTEGER), 'log_coefficient': NUM, 'coefficient': POS,
             'training_rmse': NONNEG, 'validation_rmse': NONNEG, 'expanded_complexity': INTEGER,
             'rank_score': NONNEG, 'evidence_class': str, 'scientific_significance': str, 'rank': INTEGER}
ABLATION = {'removed_features': seq(str), 'top_class': optional(str), 'decision': str}
DISCOVERY = {'input_sha256': HASH, 'evidence_class': str, 'ranking': seq(CANDIDATE),
    'top_class': optional(str), 'decision': str, 'equivalence_map': mapping(seq(mapping(INTEGER))),
    'surface_count': INTEGER, 'class_count': INTEGER, 'ablations': mapping(ABLATION),
    'group_diagnostics': mapping({'training_rmse': NONNEG, 'group_fitted_training_rmse': NONNEG,
        'group_fitted_log_coefficient': NUM, 'validation_rmse': optional(NONNEG)}),
    'dimensional_system': {'rank': INTEGER, 'nullity': INTEGER, 'status': str},
    'family_assessment': str, 'minimum_validation_rmse': optional(NONNEG),
    'approximation_status': str, 'structural_recovery_claim': bool}
INVENTORY_FILE = {'kind': str, 'size': INTEGER, 'sha256': HASH}
RECEIPT = {'version': INTEGER, 'python_minor': str, 'cache_tag': str,
    **{k: seq(str) for k in ('successful_reads', 'expected_missing_cache_attempts',
        'denied_unexpected_attempts', 'successful_opens', 'audit_open_attempts',
        'discovery_modules', 'unexpected_modules')},
    'inventory_before': None, 'inventory_after': None, 'worker_sha256': HASH}


def worker(value, result_schema):
    spec = {'discovery': result_schema, 'error': None, 'receipt': {
        k: v for k, v in RECEIPT.items() if not k.startswith('inventory_')}}
    compact = {**value, 'receipt': {k: v for k, v in value['receipt'].items()
                                   if not k.startswith('inventory_')}}
    validate(compact, spec)
    for key in ('inventory_before', 'inventory_after'):
        inventory = value['receipt'][key]
        if type(inventory) is not dict: raise ValueError('invalid inventory')
        for name, item in inventory.items():
            validate(item, {'kind': enum('directory')} if name == 'Discovery' else INVENTORY_FILE)
    if set(value['receipt']) != set(RECEIPT): raise ValueError('receipt fields')


ASSESS = {'threshold': NONNEG, 'family_validation_rmse': NONNEG, 'rank1_validation_rmse': NONNEG,
          'family_margin': NUM, 'rank1_margin': NUM, 'family_rejected': bool, 'rank1_decision': str}
RULE = {**ASSESS, 'ablations': mapping(ABLATION)}
OPERATIONAL = {'rules': mapping(RULE), 'rank1_class': str, 'approximation': bool,
               'independent_inventory': mapping(mapping(str))}
TRUTH = {'block': INTEGER, 'condition': enum('adequate', 'curved'), 'noise_index': INTEGER,
         'epsilon': POS, 'coefficient': POS, 'exponent': INTEGER, 'beta': NONNEG,
         'in_family': bool, 'base_signature': mapping(str)}
BANK = {'child_seed': HASH, 'coefficient': POS, 'centers': {k: NUM for k in ('x', 't', 'z')},
        'exponent': INTEGER, 'splits': {k: seq({'features': FEATURES, 'u': NUM}) for k in ('train', 'validation', 'heldout')},
        'calibration': seq({'pair_id': str, 'features': FEATURES, 'u1': NUM, 'u2': NUM})}
ORACLE = {'seed': HASH, 'generator_version': str, 'blocks': mapping(BANK), 'datasets': mapping(TRUTH)}
BINDINGS = {'actual_base_sha': SHA, 'freeze_sha': SHA, 'preregistration_sha256': HASH, 'science_sha256': HASH}


def envelope(kind, data, bindings):
    validate(bindings, BINDINGS)
    return {'task': 'NP-ESTIMATED-NOISE-01', 'revision': 1,
            'schema': 'tnp-estimated-noise/'+kind+'-v1', 'bindings': bindings, 'data': data}


def unwrap(raw, kind, bindings=None):
    value = loads(raw) if isinstance(raw, (bytes, str)) else raw
    if type(value) is not dict or set(value) != {'task', 'revision', 'schema', 'bindings', 'data'}:
        raise ValueError('artifact envelope fields')
    same({k: value[k] for k in ('task', 'revision', 'schema')},
         {'task': 'NP-ESTIMATED-NOISE-01', 'revision': 1, 'schema': 'tnp-estimated-noise/'+kind+'-v1'},
         'artifact identity')
    validate(value['bindings'], BINDINGS)
    if bindings is not None: same(value['bindings'], bindings, 'artifact bindings')
    return value['data']


def scientific_inputs(public, calibration_records, heldout=None, oracle=None):
    validate(public, mapping(PUBLIC)); validate(calibration_records, mapping(seq(PAIR)))
    ids = {f'd{i:03d}' for i in range(1, 97)}
    if set(public) != ids or set(calibration_records) != ids: raise ValueError('96 anonymous ids required')
    for rid in ids:
        if len(public[rid]['train']) != 64 or len(public[rid]['validation']) != 48 or len(calibration_records[rid]) != 256:
            raise ValueError('fixed input counts')
    if heldout is not None:
        validate(heldout, mapping(seq(ROW)))
        if set(heldout) != ids or any(len(v) != 64 for v in heldout.values()): raise ValueError('heldout count')
    if oracle is not None:
        validate(oracle, ORACLE)
        if set(oracle['datasets']) != ids: raise ValueError('oracle count')


ENVIRONMENT = {'implementation': str, 'version': str, 'version_info': seq(INTEGER),
    'executable': str, 'executable_sha256': HASH, 'platform': str, 'machine': str, 'cache_tag': str}
SOURCE_MANIFEST = mapping(HASH)
STATUS = {'state': enum('INTERPRETABLE', 'FAILED', 'NOT_EXECUTED'), 'stage': str, 'reason': optional(str)}
SEED = {'source_sha': SHA, 'source_manifest_sha256': HASH, 'seed_sha256': HASH,
        'environment': ENVIRONMENT, 'created_utc': str}
REMOTE = {'head': SHA, 'ref': str, 'url': str, 'observed_utc': str}
COMMITMENT = {'source_sha': SHA, 'seed_commit_sha': SHA, 'remote_readback': REMOTE,
    'generated_utc': str, 'public_sha256': HASH, 'calibration_sha256': HASH,
    'private_hashes': {'oracle_reveal.json': HASH, 'heldout.json': HASH, 'seed.txt': HASH},
    'dataset_ids': seq(str)}
CAL_SEAL = {'source_sha': SHA, 'data_commit_sha': SHA, 'estimates_sha256': HASH,
    'calibration_sha256': HASH, 'record_count': INTEGER, 'settings': SETTINGS,
    'output_hashes': mapping(HASH), 'created_utc': str}
SELECTION_SEAL = {'source_sha': SHA, 'calibration_seal_commit_sha': SHA, 'files': mapping(HASH),
    'created_utc': str, 'record_count': INTEGER, 'principal_fits': INTEGER, 'diagnostic_refits': INTEGER}
RESULT = {'source_sha': SHA, 'selection_seal_commit_sha': optional(SHA),
    'summary_sha256': HASH, 'evaluation_sha256': optional(HASH), 'controls_sha256': optional(HASH),
    'disposition': str, 'evidence_integrity': str, 'interpretable_datasets': INTEGER,
    'expected_datasets': INTEGER, 'review_status': str, 'operational_status': str,
    'outcome_blind': bool, 'scientific_law_claim': bool}


def validate_selection(value):
    if set(value) != {'dataset_id', 'source_sha', 'data_commit_sha', 'calibration_seal_sha256',
                     'calibration_seal_commit_sha', 'payload_sha256', 'worker', 'operational'}:
        raise ValueError('selection fields')
    validate({k: v for k, v in value.items() if k not in ('worker', 'operational')}, {
        'dataset_id': str, 'source_sha': SHA, 'data_commit_sha': SHA, 'calibration_seal_sha256': HASH,
        'calibration_seal_commit_sha': SHA, 'payload_sha256': HASH})
    worker(value['worker'], DISCOVERY)
    validate(value['operational'], OPERATIONAL)
