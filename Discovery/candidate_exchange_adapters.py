"""Two mock wire formats and raw-bound exchange records; no real engine adapter."""
from copy import deepcopy
from pathlib import Path

from Discovery import candidate_exchange as cx

FORMATS = ('mock-tree/1', 'mock-postfix/1', 'internal-margin1/1')
CANDIDATE_FIELDS = {'candidate_id', 'manifest_digest', 'raw_binding', 'expression', 'parameters',
                    'diagnostics', 'claims', 'display', 'opaque', 'ancestry', 'source_item'}
RECEIPT_FIELDS = {'generator', 'kind', 'manifest_digest', 'input_digest', 'configuration',
                  'configuration_digest', 'adapter', 'source', 'run_status', 'failure',
                  'metadata', 'input_count', 'candidate_count', 'candidate_ids', 'inventory'}
CARD_FIELDS = {'candidate_id', 'manifest_digest', 'candidate_digest', 'integrity', 'eligibility',
               'dimensions', 'domain', 'representation', 'numerical_checks', 'original_reported_metrics',
               'source_claims', 'scientific_evidence', 'candidate_status', 'outcome', 'reasons'}


def postfix(tokens):
    cx.require(type(tokens) is list and len(tokens) <= cx.LIMITS['nodes'], 'EXPRESSION_LIMIT', 'Postfix token limit.', 'UNSUPPORTED')
    stack = []
    for token in tokens:
        if type(token) is dict and 'op' in token:
            cx.require(token['op'] in ('variable', 'literal', 'parameter'), 'OPERATOR', 'Only atoms are postfix leaf tokens.', 'UNSUPPORTED')
            stack.append(deepcopy(token))
        elif type(token) is dict:
            cx.fields(token, {'operator', 'exponent'})
            cx.require(token['operator'] == 'power', 'OPERATOR', 'Unknown postfix operator.', 'UNSUPPORTED')
            cx.require(len(stack) >= 1, 'POSTFIX', 'Postfix stack underflow.')
            stack.append({'op': 'power', 'arg': stack.pop(), 'exponent': token['exponent']})
        else:
            cx.require(type(token) is str and token in ('+', '*', '/', 'exp', 'log'), 'OPERATOR', 'Unknown postfix operator.', 'UNSUPPORTED')
            unary = token in ('exp', 'log')
            cx.require(len(stack) >= (1 if unary else 2), 'POSTFIX', 'Postfix stack underflow.')
            b = stack.pop()
            if unary: n = {'op': token, 'arg': b}
            else:
                a = stack.pop()
                n = {'op': 'divide', 'numerator': a, 'denominator': b} if token == '/' else {'op': 'add' if token == '+' else 'multiply', 'args': [a, b]}
            stack.append(n)
    cx.require(len(stack) == 1, 'POSTFIX', 'Postfix must produce one expression.')
    return stack[0]


def translate(item, fmt, manifest):
    """Translate inert records only. Every historical field remains in source_item."""
    if fmt == 'mock-tree/1':
        cx.fields(item, {'id', 'expression', 'parameters', 'diagnostics', 'claims', 'display', 'opaque'})
        expression, params = deepcopy(item['expression']), deepcopy(item['parameters'])
        engine_id, diagnostics, claims, display, opaque = (item[k] for k in ('id', 'diagnostics', 'claims', 'display', 'opaque'))
    elif fmt == 'mock-postfix/1':
        cx.fields(item, {'label', 'tokens', 'coefficients', 'metrics', 'assertions', 'render', 'opaque'})
        expression, params = postfix(item['tokens']), deepcopy(item['coefficients'])
        engine_id, diagnostics, claims, display, opaque = (item[k] for k in ('label', 'metrics', 'assertions', 'render', 'opaque'))
    else:
        cx.require(fmt == 'internal-margin1/1', 'VERSION', 'Unsupported adapter.', 'UNSUPPORTED')
        cx.fields(item, {'class_id', 'coefficient', 'evidence_class', 'expanded', 'expanded_complexity',
            'log_coefficient', 'members', 'rank', 'rank_score', 'representative', 'scientific_significance',
            'training_rmse', 'validation_rmse'})
        cx.require(type(item['coefficient']) is float, 'NUMBER', 'Historical fitted coefficient must remain approximate.')
        parts = [{'op': 'parameter', 'name': 'coefficient'}]
        from fractions import Fraction
        for name, power in item['representative'].items():
            cx.require(type(power) is str, 'POWER', 'Historical power must retain exact string representation.')
            import re
            cx.require(re.fullmatch(r'-?[0-9]{1,78}(?:/[0-9]{1,78})?', power) is not None, 'POWER', 'Exact historical exponent syntax required.')
            try: exponent = Fraction(power)
            except (ValueError, ZeroDivisionError) as e: raise cx.ContractError('POWER', 'Malformed historical exponent.') from e
            cx.require(exponent.denominator == 1, 'POWER', 'Historical noninteger powers unsupported.', 'UNSUPPORTED')
            parts.append({'op': 'power', 'arg': {'op': 'variable', 'name': name}, 'exponent': exponent.numerator})
        expression = parts[0] if len(parts) == 1 else {'op': 'multiply', 'args': parts}
        params = {'coefficient': {**manifest['parameters']['coefficient'], 'value': {'kind': 'approximate', 'value': item['coefficient']}}}
        engine_id, diagnostics, claims, display, opaque = item['class_id'], deepcopy(item), {
            'evidence_class': item['evidence_class'], 'scientific_significance': item['scientific_significance']}, item['class_id'], {}
    cx.require(type(engine_id) is str and type(display) is str, 'TYPE', 'Display and engine ID must be strings.')
    cx.require(type(diagnostics) is dict and type(claims) is dict, 'TYPE', 'Diagnostics and untrusted claims must be objects.')
    cx.opaque(opaque)
    cx.validate_parameters(manifest, params); cx.validate_expr(expression, manifest, params)
    return dict(expression=expression, parameters=params, diagnostics=deepcopy(diagnostics),
                claims=deepcopy(claims), display=display, opaque=deepcopy(opaque)), engine_id


def unpack(raw, fmt, manifest):
    data = cx.loads(raw)
    cx.require(fmt in FORMATS, 'VERSION', 'Unknown adapter format.', 'UNSUPPORTED')
    if fmt == 'internal-margin1/1':
        cx.fields(data, {'discovery', 'error', 'receipt'})
        cx.require(data['error'] is None and type(data['discovery']) is dict, 'HISTORICAL', 'Pinned historical selection unavailable.')
        cx.require(type(data['receipt']) is dict and type(data['discovery'].get('ranking')) is list,
                   'HISTORICAL', 'Malformed historical ranking or source receipt.')
        items = data['discovery']['ranking']
        return items, 'success', None, {'seed': 'unknown', 'environment': data['receipt'].get('cache_tag', 'unknown'),
            'budget': 'recorded_in_pinned_design', 'stopping': 'recorded_bounded_enumeration',
            'training_target_exposure': 'original_training_fit', 'fixture_mode': 'retrospective_outcome_known',
            'original_discovery_context': {k: v for k, v in data['discovery'].items() if k != 'ranking'},
            'original_receipt': data['receipt']}
    cx.fields(data, {'schema', 'manifest_digest', 'manifest_echo', 'items', 'status', 'failure', 'metadata'})
    cx.require(data['schema'] == fmt, 'VERSION', 'Unknown mock wire format.', 'UNSUPPORTED')
    cx.require(data['manifest_digest'] == cx.digest(manifest), 'MANIFEST_BINDING', 'Generator references a different manifest.')
    cx.require(data['manifest_echo'] is None or data['manifest_echo'] == manifest, 'MANIFEST_LAUNDERING', 'Generator metadata disagrees with trusted manifest.')
    cx.opaque(data['metadata'])
    cx.require(data['status'] in ('success', 'failed'), 'RUN_STATUS', 'Unknown run state.')
    cx.require((data['status'] == 'success' and data['failure'] is None) or
               (data['status'] == 'failed' and type(data['failure']) is str and bool(data['failure'])), 'RUN_STATUS', 'Success and operational failure must be explicit.')
    return data['items'], data['status'], data['failure'], {'seed': 'not_applicable', 'environment': 'unknown',
            'budget': 'not_applicable', 'stopping': 'static_fixture', 'training_target_exposure': 'not_applicable',
            'fixture_mode': 'visible_deterministic_mock', 'opaque': data['metadata']}


def ingest(manifest, raw, fmt, source='supplied_bytes'):
    """Return complete records or one explicit run rejection. Never execute display text."""
    try:
        cx.validate_manifest(manifest)
        cx.require(type(source) is str and bool(source), 'SOURCE', 'Source location required.')
        items, state, failure, metadata = unpack(raw, fmt, manifest)
        cx.require(type(items) is list and len(items) <= cx.LIMITS['candidates'], 'SIZE', 'Candidate inventory limit.', 'UNSUPPORTED')
        source_binding = {'location': source, 'sha256': cx.sha(raw), 'bytes': len(raw)}
        candidates, inventory = [], []
        for index, item in enumerate(items):
            cid = f'item-{index:04d}'
            binding = {**source_binding, 'locator': f'/discovery/ranking/{index}' if fmt == 'internal-margin1/1' else f'/items/{index}', 'item_digest': cx.digest(item)}
            try:
                translated, original_id = translate(item, fmt, manifest)
                candidate = {'schema': cx.NS + '/candidate', 'candidate_id': cid, 'manifest_digest': cx.digest(manifest),
                    'raw_binding': binding, **translated, 'ancestry': [source], 'source_item': deepcopy(item)}
                candidates.append(candidate)
                row = {'index': index, 'candidate_id': cid, 'original_id': original_id, 'status': 'RETAINED', 'reason': None, 'raw_binding': binding}
            except cx.ContractError as e:
                row = {'index': index, 'candidate_id': cid, 'original_id': item.get('id', item.get('label', item.get('class_id'))) if type(item) is dict else None,
                    'status': e.status, 'reason': {'code': e.code, 'message': e.message}, 'raw_binding': binding}
            inventory.append(row)
        config = {'format': fmt, 'limits': cx.LIMITS, 'numeric_convention': 'coherent_si_or_dimensionless'}
        receipt = {'schema': cx.NS + '/receipt', 'generator': fmt,
            'kind': 'internal_record_import' if fmt == 'internal-margin1/1' else 'mock',
            'manifest_digest': cx.digest(manifest), 'input_digest': manifest['input_digest'],
            'configuration': config, 'configuration_digest': cx.digest(config),
            'adapter': {'path': 'Discovery/candidate_exchange_adapters.py', 'sha256': cx.sha(Path(__file__).read_bytes())},
            'source': source_binding, 'run_status': 'OPERATIONAL_FAILURE' if state == 'failed' else 'EMPTY_OUTPUT' if not items else 'OUTPUT_RECEIVED',
            'failure': failure, 'metadata': metadata, 'input_count': len(items), 'candidate_count': len(candidates),
            'candidate_ids': [c['candidate_id'] for c in candidates], 'inventory': inventory}
        return {'receipt': receipt, 'candidates': candidates}
    except cx.ContractError as e:
        return {'run_rejection': {'status': e.status, 'code': e.code, 'message': e.message}}


def verify_records(manifest, raw, fmt, bundle, source='supplied_bytes'):
    """Trusted replay binds raw and normalized records, including all rejected items."""
    cx.bounded(bundle)
    cx.fields(bundle, {'receipt', 'candidates'})
    cx.schema(bundle['receipt'], 'receipt', RECEIPT_FIELDS)
    cx.require(type(bundle['candidates']) is list, 'TYPE', 'Candidate records must be a list.')
    for c in bundle['candidates']: cx.schema(c, 'candidate', CANDIDATE_FIELDS)
    expected = ingest(manifest, raw, fmt, source)
    cx.require('run_rejection' not in expected, 'RAW_BINDING', 'Raw source does not produce a valid receipt.')
    cx.require(bundle == expected, 'RAW_BINDING', 'Receipt, inventory or normalized records disagree with exact raw source.')
    return True


def evaluate_records(manifest, raw, fmt, bundle, points, source='supplied_bytes'):
    try:
        verify_records(manifest, raw, fmt, bundle, source)
        if bundle['receipt']['run_status'] != 'OUTPUT_RECEIVED':
            return {'run_status': bundle['receipt']['run_status'], 'cards': [], 'scientific_evidence': dict(cx.PROMOTION)}
        return {'run_status': 'OUTPUT_RECEIVED', 'cards': [cx.evidence_card(c, manifest, points) for c in bundle['candidates']],
                'scientific_evidence': dict(cx.PROMOTION)}
    except cx.ContractError as e:
        return {'run_rejection': {'status': e.status, 'code': e.code, 'message': e.message}}


def verify_cards(manifest, raw, fmt, bundle, points, result, source='supplied_bytes'):
    cx.bounded(result)
    cx.fields(result, {'run_status', 'cards', 'scientific_evidence'})
    cx.require(type(result['cards']) is list, 'TYPE', 'Cards must be a list.')
    for card in result['cards']: cx.schema(card, 'card', CARD_FIELDS)
    cx.require(result == evaluate_records(manifest, raw, fmt, bundle, points, source), 'CARD_BINDING', 'Stored trusted cards disagree with recomputed evaluation.')
    return True
