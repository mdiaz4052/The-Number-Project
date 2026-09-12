"""Bounded parser for pinned lean4export NDJSON 3.1.0; never a kernel checker.

Expression references and generated declaration dependencies are retained. Unknown
records, dangling references, duplicate identifiers and missing targets fail closed.
"""
from __future__ import annotations

from collections import Counter, deque
import gzip
import hashlib
import json
from pathlib import Path


class ClosureError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise ClosureError(reason)


def dumps(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique(pairs):
    out = {}
    for k, v in pairs:
        require(k not in out, 'duplicate JSON key: ' + k)
        out[k] = v
    return out


def read_json(raw):
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda s: require(False, 'nonfinite JSON'))


def write_json(path, value):
    Path(path).write_text(dumps(value) + '\n')


def gzip_lines(path, values):
    with open(path, 'wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, filename='') as z:
            for v in values:
                z.write((dumps(v) + '\n').encode())


class Export:
    def __init__(self, path, limits):
        self.names = {0: ''}
        self.name_structures = {0: []}
        self.printed_name_structures = {'': []}
        self.levels = {0: digest(b'zero')}
        self.exprs = {}
        self.decls = {}
        self.meta = None
        self.limits = limits
        path = Path(path)
        require(path.stat().st_size <= limits['export_bytes_per_target'], 'export byte cap')
        with path.open() as f:
            for lineno, line in enumerate(f, 1):
                require(line.endswith('\n'), 'truncated NDJSON line')
                row = read_json(line)
                require(isinstance(row, dict), 'nonobject export record')
                self.add(row, lineno)
        require(self.meta is not None and self.decls, 'missing metadata/declarations; no empty success')

    def name(self, n):
        require(type(n) is int and n in self.names, 'unresolved name ' + str(n))
        return self.names[n]

    def level(self, n):
        require(type(n) is int and n in self.levels, 'unresolved level ' + str(n))
        return self.levels[n]

    def expression(self, n):
        require(type(n) is int and n in self.exprs, 'unresolved expression ' + str(n))
        return self.exprs[n]

    def add(self, row, lineno):
        if 'meta' in row:
            require(lineno == 1 and set(row) == {'meta'}, 'misplaced metadata')
            self.meta = row['meta']
            require(self.meta['format']['version'] == '3.1.0', 'unsupported export format')
            return
        require(self.meta is not None, 'metadata must be first')
        if 'in' in row:
            i = row['in']
            require(type(i) is int and i not in self.names, 'duplicate name id')
            kind = next((k for k in ('str', 'num') if k in row), None)
            require(kind is not None and len(row) == 2, 'unknown name record')
            d = row[kind]
            prefix = self.name(d['pre'])
            part = d['str'] if kind == 'str' else str(d['i'])
            # Preserve Lean name components, including numeric or dotted components,
            # in identity hashing; printed names alone are not an injective encoding.
            self.names[i] = prefix + ('.' if prefix else '') + part
            structure = self.name_structures[d['pre']] + [[kind,d['str'] if kind=='str' else d['i']]]
            printed = self.names[i]
            require(printed not in self.printed_name_structures or self.printed_name_structures[printed]==structure,
                    'ambiguous rendered Lean name')
            self.name_structures[i]=structure; self.printed_name_structures[printed]=structure
            return
        if 'il' in row:
            i = row['il']
            require(type(i) is int and i not in self.levels, 'duplicate level id')
            kinds = set(row) - {'il'}
            require(len(kinds) == 1, 'malformed level')
            k = next(iter(kinds)); v = row[k]
            if k == 'succ': v = self.level(v)
            elif k in ('max', 'imax'): v = [self.level(x) for x in v]
            elif k == 'param': self.name(v); v = self.name_structures[v]
            else: raise ClosureError('unknown level kind ' + k)
            self.levels[i] = digest(dumps([k, v]).encode())
            return
        if 'ie' in row:
            i = row['ie']
            require(type(i) is int and i not in self.exprs, 'duplicate expression id')
            kinds = set(row) - {'ie'}
            require(len(kinds) == 1, 'malformed expression')
            k = next(iter(kinds)); v = row[k]
            refs, consts = [], []
            norm = v
            if k == 'const':
                consts = [self.name(v['name'])]
                norm = [self.name_structures[v['name']], [self.level(x) for x in v['us']]]
            elif k == 'sort': norm = self.level(v)
            elif k == 'app': refs = [v['fn'], v['arg']]
            elif k in ('lam', 'forallE'): refs = [v['type'], v['body']]
            elif k == 'letE': refs = [v['type'], v['value'], v['body']]
            elif k == 'proj':
                refs = [v['struct']]; consts = [self.name(v['typeName'])]
            elif k == 'mdata': refs = [v['expr']]
            elif k not in ('bvar', 'natVal', 'strVal'): raise ClosureError('unknown expression kind ' + k)
            child_hashes = [self.expression(x)['digest'] for x in refs]
            if refs:
                # Binder names are preserved, not alpha-normalized away.
                attrs = {a:b for a,b in v.items() if a not in ('fn','arg','type','body','value','struct','expr')}
                for a in ('name','typeName'):
                    if a in attrs: self.name(attrs[a]); attrs[a] = self.name_structures[attrs[a]]
                norm = [attrs, child_hashes]
            self.exprs[i] = {'refs':refs, 'constants':consts, 'digest':digest(dumps([k,norm]).encode())}
            return
        require(len(row) == 1, 'unknown export row')
        k, v = next(iter(row.items()))
        if k == 'inductive':
            require(set(v) == {'types','ctors','recs'}, 'unknown inductive fields')
            for group, kind in [('types','inductive'),('ctors','constructor'),('recs','recursor')]:
                for d in v[group]: self.add_decl(kind, d)
        else:
            require(k in ('axiom','def','thm','opaque','quot'), 'unknown declaration kind ' + k)
            self.add_decl(k, v)

    def constants(self, eid):
        todo, seen, out = [eid], set(), set()
        while todo:
            n = todo.pop()
            if n in seen: continue
            seen.add(n)
            e = self.expression(n)
            out.update(e['constants']); todo.extend(e['refs'])
        return out

    def add_decl(self, kind, d):
        n = self.name(d['name'])
        require(n not in self.decls, 'duplicate or ambiguous printed declaration name ' + n)
        for p in d.get('levelParams', []): self.name(p)
        edges = {(x,'type') for x in self.constants(d['type'])}
        if 'value' in d:
            edges.update((x,'proof_or_value') for x in self.constants(d['value']))
        for field in ('all','ctors'):
            edges.update((self.name(x),'generated_or_structural') for x in d.get(field, []))
        if 'induct' in d: edges.add((self.name(d['induct']),'generated_or_structural'))
        for rule in d.get('rules', []):
            edges.add((self.name(rule['ctor']),'generated_or_structural'))
            edges.update((x,'generated_or_structural') for x in self.constants(rule['rhs']))
        self.decls[n] = {'name':n, 'kind':kind, 'safety':d.get('safety', 'unsafe' if d.get('isUnsafe') else 'safe' if 'isUnsafe' in d else 'unknown'),
                         'module':'unknown', 'namespace':n.rpartition('.')[0], 'instance':'unknown',
                         'body_present':'value' in d, 'type_digest':self.expression(d['type'])['digest'],
                         'universes':[self.name(x) for x in d.get('levelParams',[])], 'edges':sorted(edges)}
        require(len(self.decls) <= self.limits['nodes_per_target'], 'node cap')

    def graph(self, target, outdir=None, key=None):
        require(target in self.decls, 'missing exact target ' + target)
        require(self.decls[target]['kind'] == 'thm', 'requested target is not a theorem')
        seen, todo, parent, edges = set(), deque([target]), {target:None}, []
        while todo:
            n = todo.popleft()
            if n in seen: continue
            require(n in self.decls, 'missing referenced constant ' + n)
            seen.add(n)
            for dest, kind in self.decls[n]['edges']:
                edges.append({'source':n,'destination':dest,'kind':kind})
                if dest not in parent:
                    parent[dest] = n; todo.append(dest)
            require(len(seen) <= self.limits['nodes_per_target'], 'node cap')
            require(len(edges) <= self.limits['edges_per_target'], 'edge cap')
        nodes = [{k:v for k,v in self.decls[n].items() if k != 'edges'} for n in sorted(seen)]
        edges.sort(key=lambda e:(e['source'],e['destination'],e['kind']))
        def path(n):
            p=[]
            while n is not None:
                p.append(n); n=parent[n]
            return p[::-1]
        axioms = sorted(n for n in seen if self.decls[n]['kind']=='axiom')
        trusted = sorted(n for n in seen if self.decls[n]['kind'] in ('axiom','quot') or self.decls[n]['safety'] in ('unsafe','partial'))
        type_seen=set(); type_todo=[x for x,k in self.decls[target]['edges'] if k=='type']
        while type_todo:
            n=type_todo.pop()
            if n in type_seen:continue
            type_seen.add(n)
            type_todo.extend(x for x,k in self.decls[n]['edges'])
        result = {'target':target,'status':'COMPLETE','node_count':len(nodes),'edge_count':len(edges),
                  'unresolved_references':[], 'fixed_point':True,'nodes_by_kind':dict(Counter(n['kind'] for n in nodes)),
                  'nodes_by_namespace':dict(Counter(n['namespace'] for n in nodes)),
                  'direct_type_constants':sorted(x for x,k in self.decls[target]['edges'] if k=='type'),
                  'direct_proof_or_value_constants':sorted(x for x,k in self.decls[target]['edges'] if k=='proof_or_value'),
                  'target_type_definition_nodes':sorted(n for n in type_seen if self.decls[n]['kind'] in ('def','opaque')),
                  'proof_ancestry_outside_type_closure':sorted(seen-type_seen-{target}),
                  'navier_stokes_nodes':[n for n in nodes if n['name'].startswith('NavierStokes.')],
                  'axioms':axioms,'trusted_nodes':[self.decls[n] for n in trusted],
                  'trusted_paths':{n:path(n) for n in trusted},'type_digest':self.decls[target]['type_digest'],
                  'instance_status':'unknown; export does not provide reliable instance registrations',
                  'limitations':['Expression ancestry is not semantic validation.','Kernel/OS/compiler/runtime correctness and scanner defects are outside closure.','Ordinary opaque declarations with kernel-checked values are not axioms.']}
        if outdir is not None:
            outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
            for suffix, values in [('nodes',nodes),('edges',edges)]:
                p=outdir/(key+'.'+suffix+'.ndjson.gz'); gzip_lines(p,values)
                result[suffix+'_sha256']=digest(p.read_bytes())
        return result, seen, path


def classify_axiom(name, permitted):
    if name in permitted: return 'frozen_permitted_foundation'
    if name == 'sorryAx': return 'sorryAx'
    if name == 'Lean.ofReduceBool': return 'native_computation_trust_bridge'
    return 'custom_or_other_unpermitted_axiom'


def print_axioms(raw, target):
    # #print axioms can wrap across lines. Absence is failure, never [].
    import re
    pattern = re.escape("'"+target+"' depends on axioms: ") + r'\[([^\]]*)\]'
    m=re.search(pattern,raw,re.S)
    if m: return sorted(x.strip() for x in m[1].split(',') if x.strip())
    if "'"+target+"' does not depend on any axioms" in raw: return []
    raise ClosureError('missing target-specific #print axioms output')
