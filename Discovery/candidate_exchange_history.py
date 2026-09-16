"""Read-only importer of exactly two accepted Margin1 rankings; no runner imports."""
import json
from pathlib import Path
import subprocess

from Discovery import candidate_exchange as cx
from Discovery.candidate_exchange_adapters import ingest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'Experiments/SymbolicDiscovery/CandidateExchange1'
MARGIN = 'Experiments/SymbolicDiscovery/MisspecificationMargin1'
PIN = '7405d07e717fbe1e84d3c1afb5b7f737e86c6103'
BLOBS = {'b01-adequate-n1': '7937d9f84d56e2c12a39cbe2e6ee44a21247b338',
         'b01-curved-n2': '6e3124c349e746d994d9a860ecd25e193653898f'}


def pinned(path):
    # Only project-owned constants reach this function, never generator paths.
    return subprocess.check_output(['git', 'show', f'{PIN}:{path}'], cwd=ROOT)


def git_blob(raw):
    import hashlib
    return hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()


def imported(name):
    cx.require(name in BLOBS, 'HISTORICAL', 'Only two fixed accepted selections are authorized.')
    path = f'{MARGIN}/selection/{name}.json'
    raw = pinned(path)
    cx.require(git_blob(raw) == BLOBS[name], 'SOURCE_PIN', 'Historical selection Git blob mismatch.')
    bindings = json.loads((PACKAGE / 'historical_metadata.json').read_text())
    metadata = bindings['selections'][name]
    # Read only the two authorized public payloads from the pinned public source.
    # No discovery, fitting, heldout, oracle, or generation imports occur here.
    input_bytes = pinned(f'{MARGIN}/inputs.json')
    cx.require(cx.sha(input_bytes) == bindings['inputs_sha256'], 'SOURCE_PIN', 'Pinned public input file mismatch.')
    inputs = json.loads(input_bytes)[name]
    selected = cx.loads(raw)
    cx.require(cx.digest(inputs) == selected['discovery']['input_sha256'] == metadata['input_digest'],
               'SOURCE_PIN', 'Selection original input digest mismatch.')
    cx.require(metadata['features'] == inputs['features'] and metadata['target'] == inputs['target'] and metadata['policy'] == inputs['policy'],
               'SOURCE_PIN', 'Historical manifest metadata differs from pinned design input.')
    design = pinned(f'{MARGIN}/preregistration.v1.json')
    cx.require(cx.sha(design) == bindings['design_sha256'], 'SOURCE_PIN', 'Pinned design digest mismatch.')
    manifest = historical_manifest(metadata, name)
    return manifest, raw, ingest(manifest, raw, 'internal-margin1/1', PIN + ':' + path)


def historical_manifest(meta, name):
    quantities = {}
    specs = {**meta['features'], meta['target']['key']: {'dimension': meta['target']['dimension'], 'definition': None}}
    for key, spec in specs.items():
        quantities[key] = {'role': 'target' if key == meta['target']['key'] else 'observed' if spec['definition'] is None else 'derived',
            'dimension': spec['dimension'], 'unit': 'dimensionless' if cx.dim(spec['dimension']).is_dimensionless else 'coherent_si',
            'domain': 'positive', 'definition': spec['definition'], 'dependencies': list(spec['definition'] or {})}
    return {'schema': cx.NS + '/manifest', 'target': meta['target']['key'], 'quantities': quantities,
        'parameters': {'coefficient': {'dimension': {}, 'unit': 'dimensionless', 'role': 'training_fitted',
            'fit_context': {'split': 'original_training', 'input_digest': meta['input_digest']}}},
        'sources': [f'{PIN}:{MARGIN}/inputs.json#/{name}', f'{PIN}:{MARGIN}/preregistration.v1.json'],
        'splits': {'training': 'original_training', 'validation': 'original_validation', 'withheld': 'withheld_not_accessed'},
        'input_digest': meta['input_digest'], 'uncertainty': {'status': 'known_declared', 'references': ['pinned_synthetic_design']},
        'dependence': {'status': 'not_assessed', 'references': []}, 'allowed_ops': cx.OPS,
        'opaque': {'tnp:unit_basis': 'coherent SI numeric convention bound to synthetic design; not metrological certification',
                   'tnp:evidence_mode': 'retrospective_outcome_known', 'tnp:historical_policy': meta['policy']}}
