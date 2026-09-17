"""Bounded, project-owned candidate semantics. No fitting or executable payloads.

See CandidateExchange1/contract.v1.md and interface.md. The caller supplies the
trusted manifest separately; no assertion in generator metadata is authoritative.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
import re

from Discovery.dimensions import Dimension, DIMENSIONLESS, BASE_DIMENSIONS
from Discovery.symbolic_benchmark_engine import encoded, digest, catalog_for

NS = 'tnp-candidate-exchange/1'
OPS = ['literal', 'variable', 'parameter', 'add', 'multiply', 'divide', 'power', 'exp', 'log']
LIMITS = dict(bytes=1048576, json_depth=64, values=100000, collection=4096,
              string=16384, integer_bits=256, expression_depth=24, nodes=256,
              arity=32, exponent=16, quantities=64, parameters=32, candidates=128,
              points=32, rational_bits=4096)
CANDIDATE_STATUS = 'GENERATED/FITTED CANDIDATE'
PROMOTION = {k: 'NOT_ASSESSED' for k in ('structural_recovery', 'empirical_support',
    'significance', 'formal_proof', 'independent_replication', 'family_adequacy')}


class ContractError(ValueError):
    def __init__(self, code, message, status='REJECTED'):
        self.code, self.message, self.status = code, message, status
        super().__init__(f'{code}: {message}')


def require(condition, code, message, status='REJECTED'):
    if not condition:
        raise ContractError(code, message, status)


def fields(obj, expected):
    require(type(obj) is dict and set(obj) == set(expected), 'FIELDS',
            'Missing, extra, or incorrect record fields.')


def schema(obj, kind, expected):
    fields(obj, {'schema', *expected})
    require(obj['schema'] == NS + '/' + kind, 'VERSION', 'Unknown version or record envelope.', 'UNSUPPORTED')


def bounded(value):
    """Iterative type/resource gate also protects callers supplying Python objects."""
    stack, count = [(value, 0)], 0
    while stack:
        obj, depth = stack.pop()
        count += 1
        require(count <= LIMITS['values'], 'SIZE', 'Too many JSON values.', 'UNSUPPORTED')
        if type(obj) in (dict, list):
            require(depth < LIMITS['json_depth'], 'DEPTH', 'JSON nesting limit.', 'UNSUPPORTED')
            require(len(obj) <= LIMITS['collection'], 'SIZE', 'Collection limit.', 'UNSUPPORTED')
            if type(obj) is dict:
                require(all(type(k) is str for k in obj), 'TYPE', 'Object keys must be strings.')
                stack.extend((k, depth + 1) for k in obj)
                stack.extend((v, depth + 1) for v in obj.values())
            else:
                stack.extend((v, depth + 1) for v in obj)
        elif type(obj) is str:
            require(len(obj) <= LIMITS['string'], 'SIZE', 'String limit.', 'UNSUPPORTED')
            try:
                obj.encode('utf-8')
            except UnicodeError as e:
                raise ContractError('UTF8', 'Invalid Unicode scalar.') from e
        elif type(obj) is int:
            require(obj.bit_length() <= LIMITS['integer_bits'], 'SIZE', 'Integer limit.', 'UNSUPPORTED')
        elif type(obj) is float:
            require(math.isfinite(obj), 'NONFINITE', 'Nonfinite JSON number.')
        else:
            require(obj is None or type(obj) is bool, 'TYPE', 'Not a JSON value.')
    return value


def loads(raw):
    require(type(raw) is bytes, 'TYPE', 'Input must be exact UTF-8 bytes.')
    require(len(raw) <= LIMITS['bytes'], 'SIZE', 'Input byte limit.', 'UNSUPPORTED')
    try:
        text = raw.decode('utf-8')
    except UnicodeError as e:
        raise ContractError('UTF8', 'Invalid UTF-8 input.') from e
    # Lexical nesting bound BEFORE recursive json.loads; escaped quotes are inert.
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            require(depth <= LIMITS['json_depth'], 'DEPTH', 'JSON nesting limit.', 'UNSUPPORTED')
        elif char in ']}':
            depth -= 1
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'DUPLICATE_KEY', 'Duplicate JSON key.')
            out[key] = value
        return out
    def integer(s):
        require(len(s.lstrip('-')) <= 78, 'SIZE', 'Integer token limit.', 'UNSUPPORTED')
        return int(s)
    def invalid(s):
        raise ContractError('NONFINITE', 'Nonfinite JSON token.')
    try:
        return bounded(json.loads(text, object_pairs_hook=pairs, parse_int=integer, parse_constant=invalid))
    except (json.JSONDecodeError, RecursionError) as e:
        raise ContractError('JSON', 'Malformed JSON.') from e


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(value):
    require(type(value) is str and value.isascii() and value.isidentifier(), 'IDENTIFIER', 'Invalid symbol.')
    return value


def opaque(value):
    require(type(value) is dict and all(':' in k and k.split(':')[0] for k in value),
            'METADATA', 'Opaque keys must be namespaced.')
    bounded(value)


def rational(n, d):
    require(type(n) is int and type(d) is int and d != 0, 'NUMBER', 'Rational needs integer numerator and nonzero denominator.')
    require(max(n.bit_length(), d.bit_length()) <= LIMITS['integer_bits'], 'SIZE', 'Rational input limit.', 'UNSUPPORTED')
    return Fraction(n, d)


def number(obj):
    require(type(obj) is dict and 'kind' in obj, 'NUMBER', 'Number must declare exact or approximate semantics.')
    if obj['kind'] == 'exact':
        fields(obj, {'kind', 'numerator', 'denominator'})
        return rational(obj['numerator'], obj['denominator'])
    require(obj['kind'] == 'approximate', 'NUMBER', 'Unsupported number encoding.', 'UNSUPPORTED')
    fields(obj, {'kind', 'value'})
    require(type(obj['value']) is float and math.isfinite(obj['value']), 'NUMBER', 'Approximate value must be a finite float.')
    return obj['value']


def dim(raw):
    require(type(raw) is dict and set(raw) <= set(BASE_DIMENSIONS), 'DIMENSION', 'Invalid SI dimension keys.')
    result = {}
    for k, v in raw.items():
        require(type(v) in (int, str), 'DIMENSION', 'Dimension exponent must be exact, never boolean.')
        if type(v) is str:
            require(re.fullmatch(r'-?[0-9]{1,78}(?:/[0-9]{1,78})?', v) is not None, 'DIMENSION', 'Exact rational dimension syntax required.')
        try:
            f = Fraction(v)
        except (ValueError, ZeroDivisionError) as e:
            raise ContractError('DIMENSION', 'Malformed rational dimension.') from e
        require(max(f.numerator.bit_length(), f.denominator.bit_length()) <= 256,
                'SIZE', 'Dimension rational limit.', 'UNSUPPORTED')
        result[k] = f
    return Dimension.from_mapping(result)


def unit(convention, dimension):
    require(convention == ('dimensionless' if dimension.is_dimensionless else 'coherent_si'),
            'UNIT', 'Unsupported or missing numeric unit convention.', 'UNSUPPORTED')


def declaration(d):
    fields(d, {'status', 'references'})
    require(d['status'] in ('exact_by_design', 'known_declared', 'unknown', 'not_assessed'), 'UNCERTAINTY', 'Invalid uncertainty/dependence declaration.')
    require(type(d['references']) is list and all(type(x) is str for x in d['references']), 'TYPE', 'References must be strings.')
    if d['status'] == 'known_declared':
        require(bool(d['references']), 'UNCERTAINTY', 'Known declaration requires references.')


def validate_manifest(m):
    bounded(m)
    schema(m, 'manifest', {'target', 'quantities', 'parameters', 'sources', 'splits', 'input_digest',
        'uncertainty', 'dependence', 'allowed_ops', 'opaque'})
    q = m['quantities']
    require(type(q) is dict and 1 <= len(q) <= LIMITS['quantities'], 'SIZE', 'Quantity registry limit.', 'UNSUPPORTED')
    require(type(m['target']) is str and m['target'] in q, 'TARGET', 'Missing target.')
    require(type(m['sources']) is list and bool(m['sources']) and all(type(x) is str for x in m['sources']), 'SOURCE', 'Source references required.')
    require(type(m['input_digest']) is str and len(m['input_digest']) == 64 and all(c in '0123456789abcdef' for c in m['input_digest']), 'DIGEST', 'Invalid input digest.')
    fields(m['splits'], {'training', 'validation', 'withheld'})
    require(all(type(v) is str and v for v in m['splits'].values()), 'SPLIT', 'Named data roles required.')
    require(len(set(m['splits'].values())) == 3, 'SPLIT', 'Training, validation and withheld roles must differ.')
    require(m['allowed_ops'] == OPS, 'FRAGMENT', 'Unsupported expression fragment.', 'UNSUPPORTED')
    declaration(m['uncertainty']); declaration(m['dependence']); opaque(m['opaque'])
    dimensions, features = {}, {}
    for name, spec in q.items():
        identifier(name)
        fields(spec, {'role', 'dimension', 'unit', 'domain', 'definition', 'dependencies'})
        dimensions[name] = dim(spec['dimension']); unit(spec['unit'], dimensions[name])
        require(spec['domain'] in ('real', 'nonzero', 'positive'), 'DOMAIN', 'Unsupported declared domain.', 'UNSUPPORTED')
        role = spec['role']
        require(role in ('target', 'observed', 'derived', 'alias') and (role == 'target') == (name == m['target']), 'ROLE', 'Invalid quantity role.')
        deps, definition = spec['dependencies'], spec['definition']
        require(type(deps) is list and all(type(k) is str for k in deps) and len(set(deps)) == len(deps), 'GRAPH', 'Invalid direct dependencies.')
        if role in ('observed', 'target'):
            require(definition is None and not deps, 'GRAPH', 'Observed/target quantity cannot carry a derivation.')
        else:
            require(type(definition) is dict and bool(definition) and set(deps) == set(definition), 'GRAPH', 'Derivation and direct edges disagree.')
            require(set(deps) <= set(q), 'GRAPH', 'Missing dependency node.')
            require(all(type(p) is int and abs(p) <= LIMITS['exponent'] for p in definition.values()), 'ALIAS', 'Only exact integer monomial definitions supported.', 'UNSUPPORTED')
            if role == 'alias':
                require(len(definition) == 1 and list(definition.values()) == [1], 'ALIAS', 'Alias must identify one quantity unchanged.')
        if name != m['target']:
            features[name] = {k: spec[k] for k in ('dimension', 'unit', 'definition')}
    # The legacy monomial catalog normalizes away zero exponents. Validate the
    # ORIGINAL edges first so a zero-weight edge cannot conceal a cycle or leak.
    visiting, visited = set(), set()
    def visit(name):
        require(name not in visiting, 'GRAPH', 'Cycle in original provenance edges.')
        if name in visited: return
        visiting.add(name)
        for dep in q[name]['dependencies']: visit(dep)
        visiting.remove(name); visited.add(name)
    for name, spec in q.items():
        visit(name)
        if spec['definition'] is not None:
            derived = DIMENSIONLESS
            for dep, power in spec['definition'].items(): derived = derived * dimensions[dep] ** power
            require(derived == dimensions[name], 'GRAPH', 'Derived dimension disagrees with registered definition.')
    catalog_features = {k: {**v, 'definition': v['definition'] if v['definition'] and any(v['definition'].values()) else None}
                        for k, v in features.items()}
    try:
        catalog_for(catalog_features, {'key': m['target'], 'dimension': q[m['target']]['dimension']})
    except (ValueError, TypeError, RecursionError) as e:
        raise ContractError('GRAPH', 'Invalid cyclic, missing, or dimensionally inconsistent provenance graph.') from e
    require(type(m['parameters']) is dict and len(m['parameters']) <= LIMITS['parameters'], 'SIZE', 'Parameter registry limit.', 'UNSUPPORTED')
    for name, p in m['parameters'].items():
        identifier(name); require(name not in q, 'IDENTIFIER', 'Parameter/quantity collision.')
        fields(p, {'dimension', 'unit', 'role', 'fit_context'})
        unit(p['unit'], dim(p['dimension']))
        require(p['role'] in ('fixed', 'training_fitted'), 'PARAMETER', 'Unsupported parameter role.')
        expected = {'split': m['splits']['training'], 'input_digest': m['input_digest']} if p['role'] == 'training_fitted' else None
        require(p['fit_context'] == expected, 'FIT_CONTEXT', 'Fitted parameter must reference only the original training context.')
    return dimensions, features


def validate_parameters(m, params):
    require(type(params) is dict and set(params) <= set(m['parameters']), 'PARAMETER', 'Unknown parameter.')
    for name, p in params.items():
        fields(p, {'value', 'dimension', 'unit', 'role', 'fit_context'})
        require({k: v for k, v in p.items() if k != 'value'} == m['parameters'][name], 'PARAMETER', 'Parameter role, dimension or fitting context mismatch.')
        number(p['value'])


def validate_expr(expr, m, params):
    stack, count, refs = [(expr, 1)], 0, set()
    while stack:
        n, depth = stack.pop(); count += 1
        require(depth <= LIMITS['expression_depth'] and count <= LIMITS['nodes'], 'EXPRESSION_LIMIT', 'Expression depth/node limit.', 'UNSUPPORTED')
        require(type(n) is dict and type(n.get('op')) is str, 'EXPRESSION', 'Malformed expression node.')
        op = n['op']
        require(op in OPS, 'OPERATOR', 'Unknown operator.', 'UNSUPPORTED')
        if op == 'literal':
            fields(n, {'op', 'number'}); number(n['number'])
        elif op in ('variable', 'parameter'):
            fields(n, {'op', 'name'}); identifier(n['name'])
            require(n['name'] in (m['quantities'] if op == 'variable' else params), 'SYMBOL', 'Unknown symbol.')
            if op == 'variable': refs.add(n['name'])
        elif op in ('add', 'multiply'):
            fields(n, {'op', 'args'})
            require(type(n['args']) is list and 2 <= len(n['args']) <= LIMITS['arity'], 'ARITY', 'Invalid operand count.', 'UNSUPPORTED')
            stack.extend((a, depth + 1) for a in n['args'])
        elif op == 'divide':
            fields(n, {'op', 'numerator', 'denominator'})
            stack.extend([(n['numerator'], depth + 1), (n['denominator'], depth + 1)])
        else:
            fields(n, {'op', 'arg', 'exponent'} if op == 'power' else {'op', 'arg'})
            if op == 'power':
                require(type(n['exponent']) is int and abs(n['exponent']) <= LIMITS['exponent'], 'POWER', 'Only bounded integer powers supported.', 'UNSUPPORTED')
            stack.append((n['arg'], depth + 1))
    return refs


def alias_expr(definition):
    parts = [{'op': 'power', 'arg': {'op': 'variable', 'name': k}, 'exponent': p} for k, p in definition.items()]
    return parts[0] if len(parts) == 1 else {'op': 'multiply', 'args': parts}


def expression_dimension(n, dimensions, params):
    op = n['op']
    if op == 'literal': return DIMENSIONLESS
    if op == 'variable': return dimensions[n['name']]
    if op == 'parameter': return dim(params[n['name']]['dimension'])
    if op in ('add', 'multiply'):
        ds = [expression_dimension(a, dimensions, params) for a in n['args']]
        if op == 'add':
            require(all(d == ds[0] for d in ds), 'DIMENSION', 'Addition requires identical dimensions.')
            return ds[0]
        result = DIMENSIONLESS
        for d in ds: result = result * d
        return result
    if op == 'divide':
        return expression_dimension(n['numerator'], dimensions, params) / expression_dimension(n['denominator'], dimensions, params)
    d = expression_dimension(n['arg'], dimensions, params)
    if op == 'power': return d ** n['exponent']
    require(d.is_dimensionless, 'DIMENSION', 'Log/exp argument must be dimensionless.')
    return DIMENSIONLESS


def fraction_bound(f):
    require(max(f.numerator.bit_length(), f.denominator.bit_length()) <= LIMITS['rational_bits'], 'NORMALIZATION_LIMIT', 'Exact normalization limit.', 'UNSUPPORTED')
    return f


def mono(coefficient=Fraction(1), terms=()):
    return ('monomial', str(fraction_bound(coefficient)), tuple(sorted((k, p) for k, p in terms if p)))


def atom(value):
    return mono(terms=((json.dumps(value, sort_keys=True, separators=(',', ':')), 1),))


def combine(forms, powers):
    coefficient, terms = Fraction(1), {}
    for f, p in zip(forms, powers):
        if f[0] != 'monomial': f = atom(f)
        c = Fraction(f[1])
        if c == 0 and p <= 0:
            return atom(('undefined_power', f, p))
        # Bound before exponentiation to avoid huge intermediate allocations.
        require(max(c.numerator.bit_length(), c.denominator.bit_length()) * abs(p) <= LIMITS['rational_bits'] + abs(p), 'NORMALIZATION_LIMIT', 'Exact power normalization limit.', 'UNSUPPORTED')
        coefficient = fraction_bound(coefficient * fraction_bound(c ** p))
        for key, power in f[2]: terms[key] = terms.get(key, 0) + p * power
    return mono(coefficient, terms.items())


def canonical(n, m, params, structural=False, cache=None):
    cache = {} if cache is None else cache
    op = n['op']
    if op == 'literal':
        v = number(n['number'])
        return mono(v) if type(v) is Fraction else atom(('approximate', v.hex()))
    if op == 'variable':
        key = n['name']; spec = m['quantities'][key]
        if spec['definition'] is not None:
            if key not in cache: cache[key] = canonical(alias_expr(spec['definition']), m, params, structural, cache)
            return cache[key]
        return atom(('variable', key))
    if op == 'parameter':
        p = params[n['name']]
        identity = {k: v for k, v in p.items() if not (structural and k == 'value')}
        return atom(('parameter', n['name'], identity))
    if op == 'multiply':
        return combine([canonical(a, m, params, structural, cache) for a in n['args']], [1] * len(n['args']))
    if op == 'divide':
        return combine([canonical(n[k], m, params, structural, cache) for k in ('numerator', 'denominator')], [1, -1])
    if op == 'power': return combine([canonical(n['arg'], m, params, structural, cache)], [n['exponent']])
    if op == 'add':
        parts = []
        for a in n['args']:
            f = canonical(a, m, params, structural, cache)
            parts.extend(f[1] if f[0] == 'sum' else [f])
        # Combine exact scalar constants only; no distributivity or zero erasure.
        constants = [Fraction(f[1]) for f in parts if f[0] == 'monomial' and not f[2]]
        parts = [f for f in parts if not (f[0] == 'monomial' and not f[2])]
        if constants: parts.append(mono(fraction_bound(sum(constants, Fraction(0)))))
        return parts[0] if len(parts) == 1 else ('sum', tuple(sorted(parts, key=repr)))
    return atom((op, canonical(n['arg'], m, params, structural, cache)))


def domain_conditions(n, m, params):
    conditions, visited = set(), set()
    def add(kind, node):
        form = canonical(node, m, params)
        if kind == 'nonzero' and form[0] == 'monomial' and Fraction(form[1]) != 0:
            for k, _ in form[2]: conditions.add(json.dumps([kind, k]))
        else:
            conditions.add(json.dumps([kind, form], sort_keys=True))
    def walk(node):
        op = node['op']
        if op == 'variable':
            name = node['name']; s = m['quantities'][name]
            if name in visited: return
            visited.add(name)
            if s['domain'] != 'real': add(s['domain'], node)
            if s['definition'] is not None: walk(alias_expr(s['definition']))
        elif op in ('add', 'multiply'):
            for a in node['args']: walk(a)
        elif op == 'divide':
            add('nonzero', node['denominator']); walk(node['numerator']); walk(node['denominator'])
        elif op in ('power', 'log', 'exp'):
            if op == 'power' and node['exponent'] <= 0: add('nonzero', node['arg'])
            if op == 'log': add('positive', node['arg'])
            walk(node['arg'])
    walk(n)
    return sorted(conditions)


def analyze(expr, m, params):
    dimensions, graph = validate_manifest(m); validate_parameters(m, params)
    refs = validate_expr(expr, m, params)
    reach_cache = {}
    def target_path(key):
        if key == m['target']: return True
        if key not in reach_cache:
            reach_cache[key] = any(target_path(dep) for dep in m['quantities'][key]['dependencies'])
        return reach_cache[key]
    leaking = sorted(k for k in refs if target_path(k))
    # Never infer eligibility from normalized expressions or coefficient values.
    require(not leaking, 'TARGET_DEPENDENCY', 'Registered target dependency: ' + ', '.join(leaking))
    dimension = expression_dimension(expr, dimensions, params)
    require(dimension == dimensions[m['target']], 'DIMENSION', 'Expression and target dimensions differ.')
    domains = domain_conditions(expr, m, params)
    model = {'manifest_digest': digest(m), 'form': canonical(expr, m, params), 'domains': domains}
    structure = {'manifest_digest': digest(m), 'form': canonical(expr, m, params, structural=True), 'domains': domains}
    return {'dimension': {k: str(v) for k, v in dimension.as_mapping().items()},
            'domains': domains, 'model_id': digest(model), 'structural_id': digest(structure),
            'normal_form': json.loads(encoded(model)), 'references': sorted(refs)}


def scalar(v):
    require(type(v) in (int, float) and (type(v) is not int or v.bit_length() <= 256), 'VALUE', 'Fixture values must be bounded real scalars.')
    require(math.isfinite(v), 'NONFINITE', 'Nonfinite fixture value.')
    return float(v)


def evaluate(expr, m, params, point):
    """Evaluate ORIGINAL tree; never use canonical tree to decide definedness."""
    require(type(point) is dict and set(point) <= set(m['quantities']), 'POINT', 'Unknown fixture quantity.')
    cache = {}
    def go(n):
        op = n['op']
        if op == 'literal': v = float(number(n['number']))
        elif op == 'parameter': v = float(number(params[n['name']]['value']))
        elif op == 'variable':
            name = n['name']; s = m['quantities'][name]
            if name in cache: return cache[name]
            if s['definition'] is None:
                require(name in point, 'POINT', 'Fixture quantity missing.')
                v = scalar(point[name])
            else:
                v = go(alias_expr(s['definition']))
                if name in point: require(scalar(point[name]) == v, 'ALIAS_VALUE', 'Fixture alias disagrees with declared definition.')
            require(s['domain'] == 'real' or (v > 0 if s['domain'] == 'positive' else v != 0), 'DOMAIN_INVALID', 'Declared quantity domain violated.')
            cache[name] = v
        elif op in ('add', 'multiply'):
            values = [go(a) for a in n['args']]
            v = math.fsum(values) if op == 'add' else math.prod(values)
        elif op == 'divide':
            a, b = go(n['numerator']), go(n['denominator'])
            require(b != 0, 'DOMAIN_INVALID', 'Division denominator is zero.')
            v = a / b
        else:
            a = go(n['arg'])
            if op == 'power':
                require(a != 0 or n['exponent'] > 0, 'DOMAIN_INVALID', 'Zero to a nonpositive power is invalid, including 0^0.')
                v = a ** n['exponent']
            elif op == 'log':
                require(a > 0, 'DOMAIN_INVALID', 'Natural log requires a positive argument.')
                v = math.log(a)
            else: v = math.exp(a)
        require(math.isfinite(v), 'NONFINITE_RESULT', 'Undefined or nonfinite arithmetic result.')
        return v
    try:
        return go(expr)
    except (OverflowError, ValueError, ZeroDivisionError) as e:
        if isinstance(e, ContractError): raise
        raise ContractError('NUMERIC_OVERFLOW', 'Arithmetic overflow or invalid real result.') from e


def equivalence(a, b):
    return 'ESTABLISHED_SUPPORTED_RULES' if a['model_id'] == b['model_id'] else 'NOT_ESTABLISHED'


def evidence_card(candidate, manifest, points):
    """Called only after binding verification by the exchange boundary."""
    card = {'schema': NS + '/card', 'candidate_id': candidate['candidate_id'],
        'manifest_digest': digest(manifest), 'candidate_digest': digest(candidate),
        'integrity': 'PASS', 'eligibility': 'NOT_ASSESSED', 'dimensions': 'NOT_ASSESSED',
        'domain': 'NOT_ASSESSED', 'representation': None, 'numerical_checks': [],
        'original_reported_metrics': candidate['diagnostics'], 'source_claims': candidate['claims'],
        'scientific_evidence': dict(PROMOTION), 'candidate_status': CANDIDATE_STATUS,
        'outcome': 'REJECTED', 'reasons': []}
    try:
        rep = analyze(candidate['expression'], manifest, candidate['parameters'])
        card.update(eligibility='ELIGIBLE_REGISTERED_GRAPH', dimensions='ADMISSIBLE', representation=rep)
        require(type(points) is list and len(points) <= LIMITS['points'], 'SIZE', 'Fixture point limit.', 'UNSUPPORTED')
        names = set()
        for point in points:
            fields(point, {'name', 'values'})
            require(type(point['name']) is str and point['name'] not in names, 'POINT', 'Fixture names must be unique strings.')
            names.add(point['name'])
            try:
                value = evaluate(candidate['expression'], manifest, candidate['parameters'], point['values'])
                result = {'name': point['name'], 'status': 'VALID', 'value': value, 'reason': None}
            except ContractError as e:
                result = {'name': point['name'], 'status': 'INVALID', 'value': None, 'reason': {'code': e.code, 'message': e.message}}
            card['numerical_checks'].append(result)
        valid = all(p['status'] == 'VALID' for p in card['numerical_checks'])
        card['domain'] = 'VALID_ON_NAMED_POINTS' if valid and points else 'INVALID_ON_NAMED_POINTS' if points else 'NOT_ASSESSED'
        card['outcome'] = 'PASS' if valid else 'REJECTED'
    except ContractError as e:
        card['outcome'] = e.status
        if e.code == 'TARGET_DEPENDENCY': card['eligibility'] = 'INELIGIBLE'
        if e.code == 'DIMENSION': card['dimensions'] = 'INADMISSIBLE'
        card['reasons'].append({'code': e.code, 'message': e.message})
    return card
