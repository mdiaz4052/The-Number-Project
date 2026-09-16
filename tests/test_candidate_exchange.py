"""Independent semantic assertions for the bounded candidate exchange contract."""
from copy import deepcopy
from fractions import Fraction
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from Discovery import candidate_exchange as c
from Discovery import candidate_exchange_adapters as a
from Discovery import candidate_exchange_fixtures as f


class ExchangeTests(unittest.TestCase):
    def card(self, expression, *, manifest=None, params=None, values=None, claims=None):
        m = manifest or f.manifest(True)
        raw = f.raw([f.tree_item(expression, params, claims)], m)
        bundle = a.ingest(m, raw, 'mock-tree/1')
        self.assertNotIn('run_rejection', bundle)
        if not bundle['candidates']:
            return bundle['receipt']['inventory'][0]
        result = a.evaluate_records(m, raw, 'mock-tree/1', bundle,
            [{'name': 'p', 'values': values if values is not None else {'x': 2., 't': 2., 'z': 1.}}])
        self.assertNotIn('run_rejection', result)
        return result['cards'][0]

    def test_lawful_paired_adapters(self):
        m = f.manifest()
        for pair in f.paired():
            cards = []
            for fmt, key in [('mock-tree/1', 'tree'), ('mock-postfix/1', 'postfix')]:
                raw = f.raw([pair[key]], m, fmt)
                bundle = a.ingest(m, raw, fmt)
                result = a.evaluate_records(m, raw, fmt, bundle, f.fixed_points())
                card = result['cards'][0]; cards.append(card)
                self.assertEqual(card['outcome'], 'PASS')
                self.assertEqual(card['eligibility'], 'ELIGIBLE_REGISTERED_GRAPH')
                self.assertEqual(card['representation']['dimension'], {'M':'0','L':'1','T':'-2','I':'0','Theta':'0','N':'0','J':'0'})
                self.assertEqual(bundle['receipt']['kind'], 'mock')
                self.assertEqual(bundle['candidates'][0]['source_item'], pair[key])
                for actual, expected in zip(card['numerical_checks'], pair['expected']):
                    self.assertAlmostEqual(actual['value'], expected, places=13)
            self.assertEqual(cards[0]['representation']['model_id'], cards[1]['representation']['model_id'])
            self.assertEqual(cards[0]['representation']['domains'], cards[1]['representation']['domains'])
            # Dimensionless-log condition is independently required, never inferred from sample agreement.
            conditions = cards[0]['representation']['domains']
            self.assertTrue(any('nonzero' in x and 't' in x for x in conditions))
            if pair['expected'] == [0., 2.]: self.assertTrue(any('positive' in x and 'z' in x for x in conditions))

    def test_exp_and_fitted_scalar(self):
        m = f.manifest(); p = {'k': {**m['parameters']['k'], 'value': {'kind': 'approximate', 'value': 3.0}}}
        e = f.mul({'op':'parameter','name':'k'}, f.div(f.var('x'),f.power(f.var('t'),2)), f.exp(f.lit(0)))
        card = self.card(e, manifest=m, params=p, values={'x':8.,'t':2.})
        self.assertEqual(card['outcome'], 'PASS'); self.assertEqual(card['numerical_checks'][0]['value'], 6.)
        self.assertEqual(card['scientific_evidence'], c.PROMOTION)

    def test_domain_erasure(self):
        # Designated mutation assertion: multiplication by zero cannot erase log's domain.
        e = f.mul(f.lit(0), f.log(f.var('x')))
        card = self.card(e, values={'x':0.})
        self.assertEqual(card['domain'], 'INVALID_ON_NAMED_POINTS')
        self.assertEqual(card['numerical_checks'][0]['reason']['code'], 'DOMAIN_INVALID')

    def test_all_original_domain_restrictions(self):
        for e, values in [(f.div(f.var('x'),f.var('x')), {'x':0.}),
            (f.mul(f.lit(0),f.div(f.lit(1),f.var('x'))), {'x':0.}),
            (f.power(f.var('x'),0), {'x':0.}), (f.power(f.var('x'),-1), {'x':0.}),
            (f.add(f.log(f.var('x')),f.mul(f.lit(-1),f.log(f.var('x')))), {'x':-1.}),
            (f.mul(f.lit(0),f.exp(f.lit(1000))), {})]:
            with self.subTest(expr=e):
                self.assertEqual(self.card(e, values=values)['domain'], 'INVALID_ON_NAMED_POINTS')
        xoverx = self.card(f.div(f.var('x'),f.var('x')))
        one = self.card(f.lit(1))
        self.assertEqual(xoverx['numerical_checks'][0]['value'], 1.)
        self.assertEqual(c.equivalence(xoverx['representation'], one['representation']), 'NOT_ESTABLISHED')

    def test_target_leakage(self):
        # Designated mutation assertion: transitive canceled/zero-weighted paths survive.
        for e in [f.var('y'),f.var('direct'),f.var('transitive'),
                  f.div(f.var('transitive'),f.var('transitive')),
                  f.mul(f.lit(0),f.var('transitive'))]:
            card = self.card(e)
            self.assertEqual(card['eligibility'], 'INELIGIBLE')
            self.assertEqual(card['reasons'][0]['code'], 'TARGET_DEPENDENCY')

    def test_dimension_bypass(self):
        # Designated mutation assertion: numeric value cannot authorize wrong dimensions.
        card = self.card(f.var('x'), manifest=f.manifest())
        self.assertEqual(card['dimensions'], 'INADMISSIBLE')

    def test_dimension_and_unit_rules(self):
        m=f.manifest()
        for expr in [f.add(f.var('x'),f.var('t')),f.log(f.var('x')),f.exp(f.var('t'))]:
            self.assertEqual(self.card(expr,manifest=m)['reasons'][0]['code'],'DIMENSION')
        for unit in [None,'cm','SI','unknown']:
            bad=deepcopy(m);bad['quantities']['x']['unit']=unit
            self.assertEqual(a.ingest(bad,f.raw([],bad),'mock-tree/1')['run_rejection']['code'],'UNIT')
        bad=deepcopy(m);del bad['quantities']['x']['unit']
        self.assertEqual(a.ingest(bad,f.raw([],bad),'mock-tree/1')['run_rejection']['code'],'FIELDS')
        p={'k':{**m['parameters']['k'],'value':{'kind':'approximate','value':2.0},'dimension':{'L':1}}}
        self.assertEqual(self.card({'op':'parameter','name':'k'},manifest=m,params=p)['reason']['code'],'PARAMETER')
        # Correctly registered dimensionful parameter still counts toward final dimension.
        m['parameters']['k'].update(dimension={'L':1},unit='coherent_si')
        p['k']={**m['parameters']['k'],'value':{'kind':'approximate','value':2.0}}
        self.assertEqual(self.card({'op':'parameter','name':'k'},manifest=m,params=p)['dimensions'],'INADMISSIBLE')

    def test_evidence_promotion(self):
        # Designated mutation assertion: generator claims cannot update trusted card fields.
        claims={'eligibility':'ELIGIBLE','structural_recovery':'STRUCTURALLY_RECOVERED',
                'empirical_support':'SUPPORTED','significance':0.,'formal_proof':True,
                'independent_replication':True,'family_adequacy':'ADEQUATE'}
        card=self.card(f.lit(1),claims=claims)
        self.assertEqual(card['scientific_evidence'],c.PROMOTION)
        self.assertEqual(card['candidate_status'],'GENERATED/FITTED CANDIDATE')
        self.assertEqual(card['source_claims'],claims)

    def test_raw_binding_tampering(self):
        # Designated mutation assertion: edit expression then refresh cheap hashes is insufficient.
        m=f.manifest(True);raw=f.raw([f.tree_item(f.lit(1))],m)
        bundle=a.ingest(m,raw,'mock-tree/1');bundle['candidates'][0]['expression']=f.lit(2)
        result=a.evaluate_records(m,raw,'mock-tree/1',bundle,[])
        self.assertIn('run_rejection',result)
        self.assertEqual(result['run_rejection']['code'],'RAW_BINDING')

    def test_candidate_inventory(self):
        # Designated mutation assertion: duplicates and low-rank outputs are retained.
        m=f.manifest(True);items=[f.tree_item(f.lit(1)),f.tree_item(f.lit(1)),f.tree_item(f.lit(2))]
        raw=f.raw(items,m);bundle=a.ingest(m,raw,'mock-tree/1')
        self.assertEqual(len(bundle['candidates']),3)
        self.assertEqual([x['source_item'] for x in bundle['candidates']],items)
        self.assertEqual(bundle['receipt']['candidate_ids'],['item-0000','item-0001','item-0002'])
        self.assertEqual([x['original_id'] for x in bundle['receipt']['inventory']],['visible-case']*3)

    def test_record_tampering_and_routing(self):
        m=f.manifest(True);raw=f.raw([f.tree_item(f.lit(1)),f.tree_item(f.lit(2))],m)
        original=a.ingest(m,raw,'mock-tree/1')
        for kind in ('drop','reorder','raw','manifest','extra','envelope','receipt'):
            b=deepcopy(original)
            if kind=='drop': b['candidates'].pop()
            elif kind=='reorder': b['candidates'].reverse()
            elif kind=='raw': b['candidates'][0]['raw_binding']['item_digest']='0'*64
            elif kind=='manifest': b['candidates'][0]['manifest_digest']='0'*64
            elif kind=='extra': b['candidates'][0]['eligibility']='eligible'
            elif kind=='envelope': b['candidates'][0]['schema']=c.NS+'/receipt'
            else: b['receipt']['candidate_count']=1
            self.assertIn('run_rejection',a.evaluate_records(m,raw,'mock-tree/1',b,[]))
        result=a.evaluate_records(m,raw,'mock-tree/1',original,[])
        for kind in ('promotion','disposition','summary','extra'):
            bad=deepcopy(result)
            if kind=='promotion':bad['cards'][0]['scientific_evidence']['structural_recovery']='STRUCTURALLY_RECOVERED'
            elif kind=='disposition':bad['cards'][0]['outcome']='CANDIDATE_EXCHANGE_1_PASS'
            elif kind=='summary':bad={'summary':bad}
            else:bad['cards'][0]['trusted_eligibility']=True
            with self.assertRaises(c.ContractError):a.verify_cards(m,raw,'mock-tree/1',original,[],bad)

    def test_manifest_laundering(self):
        m=f.manifest(True);data=c.loads(f.raw([],m))
        data['manifest_digest']='0'*64
        self.assertEqual(a.ingest(m,c.encoded(data),'mock-tree/1')['run_rejection']['code'],'MANIFEST_BINDING')
        data=c.loads(f.raw([],m));data['manifest_echo']=deepcopy(m)
        data['manifest_echo']['quantities']['direct'].update(role='observed',definition=None,dependencies=[])
        self.assertEqual(a.ingest(m,c.encoded(data),'mock-tree/1')['run_rejection']['code'],'MANIFEST_LAUNDERING')
        for change in ('cycle','missing','observed','alias','edges','alias_dimension'):
            bad=deepcopy(m)
            if change=='cycle':bad['quantities']['direct'].update(definition={'transitive':1},dependencies=['transitive'])
            elif change=='missing':bad['quantities']['direct'].update(definition={'missing':1},dependencies=['missing'])
            elif change=='observed':bad['quantities']['direct']['role']='observed'
            elif change=='alias':bad['quantities']['transitive']['definition']={'direct':2}
            elif change=='edges':bad['quantities']['direct']['dependencies']=[]
            else:bad['quantities']['transitive'].update(dimension={'L':1},unit='coherent_si')
            self.assertIn('run_rejection',a.ingest(bad,f.raw([],bad),'mock-tree/1'))

    def test_alias_meaning_and_domains(self):
        m=f.manifest(True)
        m['quantities']['u']={'role':'derived','dimension':{},'unit':'dimensionless','domain':'real','definition':{'x':-1},'dependencies':['x']}
        self.assertEqual(self.card(f.var('u'),manifest=m,values={'x':2.})['numerical_checks'][0]['value'],.5)
        self.assertEqual(self.card(f.var('u'),manifest=m,values={'x':0.})['domain'],'INVALID_ON_NAMED_POINTS')
        self.assertEqual(self.card(f.var('u'),manifest=m,values={'x':2.,'u':3.})['numerical_checks'][0]['reason']['code'],'ALIAS_VALUE')
        # A zero exponent still retains the registered target dependency.
        m['quantities']['u'].update(definition={'y':0},dependencies=['y'])
        self.assertEqual(self.card(f.var('u'),manifest=m)['eligibility'],'INELIGIBLE')

    def test_parameter_identity_and_context(self):
        m=f.manifest(True);expr={'op':'parameter','name':'k'}
        p={'k':{**m['parameters']['k'],'value':{'kind':'approximate','value':2.}}}
        first=self.card(expr,manifest=m,params=p)
        p['k']['value']['value']=3.;second=self.card(expr,manifest=m,params=p)
        self.assertEqual(first['representation']['structural_id'],second['representation']['structural_id'])
        self.assertNotEqual(first['representation']['model_id'],second['representation']['model_id'])
        for value in [True,[2.,3.],{'callable':'hidden'},float('inf')]:
            p['k']['value']['value']=value
            with self.assertRaises((c.ContractError,ValueError)):
                c.validate_parameters(m,p)
        bad=deepcopy(m);bad['parameters']['k']['fit_context']['split']='fixture_validation'
        self.assertIn('run_rejection',a.ingest(bad,f.raw([],bad),'mock-tree/1'))
        p={'k':{**m['parameters']['k'],'value':{'kind':'approximate','value':2.},'fit_context':{'split':'fixture_training','input_digest':'0'*64}}}
        self.assertEqual(self.card(expr,manifest=m,params=p)['reason']['code'],'PARAMETER')

    def test_conservative_equivalence(self):
        m=f.manifest(True)
        expressions=[f.mul(f.var('x'),f.var('z')), f.mul(f.var('z'),f.var('x')),
            f.power(f.mul(f.var('x'),f.var('z')),1)]
        reps=[c.analyze(e,m,{}) for e in expressions]
        self.assertTrue(all(c.equivalence(reps[0],r)=='ESTABLISHED_SUPPORTED_RULES' for r in reps))
        self.assertEqual(c.analyze(f.lit(2,4),m,{})['model_id'],c.analyze(f.lit(1,2),m,{})['model_id'])
        exact=c.analyze(f.lit(1),m,{})
        approximate=c.analyze({'op':'literal','number':{'kind':'approximate','value':1.}},m,{})
        self.assertEqual(c.equivalence(exact,approximate),'NOT_ESTABLISHED')
        # x and x² agree at x=0,1, but finite sample agreement cannot prove identity.
        for x in [0.,1.]:self.assertEqual(c.evaluate(f.var('x'),m,{}, {'x':x}),c.evaluate(f.power(f.var('x'),2),m,{}, {'x':x}))
        self.assertEqual(c.equivalence(c.analyze(f.var('x'),m,{}),c.analyze(f.power(f.var('x'),2),m,{})),'NOT_ESTABLISHED')
        sums=[f.add(f.var('x'),f.add(f.lit(1),f.var('z'))),f.add(f.var('z'),f.var('x'),f.lit(1))]
        self.assertEqual(c.analyze(sums[0],m,{})['model_id'],c.analyze(sums[1],m,{})['model_id'])

    def test_hostile_and_unsupported_payloads(self):
        m=f.manifest(True)
        for expr in [{'op':'call','name':'system'},f.power(f.var('x'),.5),f.power(f.var('x'),True),
            f.var('not_registered'),{'op':'literal','number':{'kind':'exact','numerator':True,'denominator':1}},
            {'op':'add','args':[f.lit(1)]},{'op':'variable','name':'x','extra':1},[]]:
            result=a.ingest(m,f.raw([f.tree_item(expr)],m),'mock-tree/1')
            self.assertEqual(result['receipt']['candidate_count'],0)
            self.assertIsNotNone(result['receipt']['inventory'][0]['reason'])
        for raw in [b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1e999}',b'{',b'\xff']:
            with self.assertRaises(c.ContractError):c.loads(raw)
        item=f.tree_item(f.lit(1));item['display']="__import__('os').system('touch SHOULD_NOT_EXIST')"
        b=a.ingest(m,f.raw([item],m),'mock-tree/1')
        self.assertEqual(b['candidates'][0]['display'],item['display'])
        self.assertFalse(Path('SHOULD_NOT_EXIST').exists())
        data=c.loads(f.raw([],m));data['schema']='mock-tree/2'
        self.assertEqual(a.ingest(m,c.encoded(data),'mock-tree/1')['run_rejection']['status'],'UNSUPPORTED')
        self.assertEqual(a.ingest(m,f.raw([],m),'unknown')['run_rejection']['status'],'UNSUPPORTED')
        m['schema']=c.NS.replace('/1','/2')+'/manifest'
        self.assertEqual(a.ingest(m,f.raw([],m),'mock-tree/1')['run_rejection']['status'],'UNSUPPORTED')

    def test_empty_failure_and_rejection_inventory(self):
        m=f.manifest(True)
        for status,failure,expected in [('success',None,'EMPTY_OUTPUT'),('failed','engine did not start','OPERATIONAL_FAILURE')]:
            raw=f.raw([],m,status=status,failure=failure);b=a.ingest(m,raw,'mock-tree/1')
            r=a.evaluate_records(m,raw,'mock-tree/1',b,[])
            self.assertEqual(r['run_status'],expected);self.assertEqual(r['cards'],[]);self.assertEqual(r['scientific_evidence'],c.PROMOTION)
        items=[f.tree_item(f.lit(1)),f.tree_item({'op':'unsupported'}),f.tree_item(f.lit(2))]
        b=a.ingest(m,f.raw(items,m),'mock-tree/1')
        self.assertEqual(len(b['receipt']['inventory']),3)
        self.assertEqual([x['status'] for x in b['receipt']['inventory']],['RETAINED','UNSUPPORTED','RETAINED'])
        self.assertEqual(b['receipt']['candidate_ids'],['item-0000','item-0002'])

    def test_json_resource_limits(self):
        # Each exact boundary succeeds; its next value fails.
        c.loads(b'0'+b' '*(c.LIMITS['bytes']-1))
        with self.assertRaises(c.ContractError):c.loads(b'0'+b' '*c.LIMITS['bytes'])
        c.loads(b'['*64+b'0'+b']'*64)
        with self.assertRaises(c.ContractError):c.loads(b'['*65+b'0'+b']'*65)
        for v,bad in [([0]*4096,[0]*4097),('x'*16384,'x'*16385),(2**256-1,2**256)]:
            c.bounded(v)
            with self.assertRaises(c.ContractError):c.bounded(bad)
        c.bounded([[0]*999 for _ in range(100-1)]+[0]*999)  # below value bound
        # Precisely 100000 visited values: root + 99 lists*(1000+1) + 900 scalars.
        exact=[[0]*1000 for _ in range(99)]+[0]*900
        c.bounded(exact)
        exact.append(0)
        with self.assertRaises(c.ContractError):c.bounded(exact)

    def test_expression_resource_limits(self):
        m=f.manifest(True)
        e=f.lit(1)
        for _ in range(23):e=f.power(e,1)
        c.validate_expr(e,m,{})
        with self.assertRaises(c.ContractError):c.validate_expr(f.power(e,1),m,{})
        c.validate_expr(f.add(*[f.lit(1)]*32),m,{})
        with self.assertRaises(c.ContractError):c.validate_expr(f.add(*[f.lit(1)]*33),m,{})
        c.validate_expr(f.power(f.lit(1),16),m,{})
        with self.assertRaises(c.ContractError):c.validate_expr(f.power(f.lit(1),17),m,{})
        # root + 7*(multiply + 32 leaves) + (multiply + 23 leaves) = 256 nodes.
        e=f.add(*([f.mul(*[f.lit(1)]*32)]*7+[f.mul(*[f.lit(1)]*23)]))
        c.validate_expr(e,m,{})
        e['args'][-1]['args'].append(f.lit(1))
        with self.assertRaises(c.ContractError):c.validate_expr(e,m,{})
        c.fraction_bound(Fraction(2**4095,1))
        with self.assertRaises(c.ContractError):c.fraction_bound(Fraction(2**4096,1))

    def test_registry_and_inventory_limits(self):
        m=f.manifest(True)
        while len(m['quantities'])<64:
            m['quantities']['q'+str(len(m['quantities']))]=deepcopy(m['quantities']['x'])
        c.validate_manifest(m)
        m['quantities']['too_many']=deepcopy(m['quantities']['x'])
        with self.assertRaises(c.ContractError):c.validate_manifest(m)
        m=f.manifest(True)
        while len(m['parameters'])<32:m['parameters']['p'+str(len(m['parameters']))]=deepcopy(m['parameters']['k'])
        c.validate_manifest(m)
        m['parameters']['too_many']=deepcopy(m['parameters']['k'])
        with self.assertRaises(c.ContractError):c.validate_manifest(m)
        m=f.manifest(True);items=[f.tree_item(f.lit(1))]*128
        self.assertEqual(a.ingest(m,f.raw(items,m),'mock-tree/1')['receipt']['candidate_count'],128)
        self.assertIn('run_rejection',a.ingest(m,f.raw(items+[items[0]],m),'mock-tree/1'))
        raw=f.raw(items[:1],m);bundle=a.ingest(m,raw,'mock-tree/1')
        points=[{'name':str(i),'values':{}} for i in range(32)]
        self.assertEqual(a.evaluate_records(m,raw,'mock-tree/1',bundle,points)['cards'][0]['outcome'],'PASS')
        self.assertEqual(a.evaluate_records(m,raw,'mock-tree/1',bundle,points+[{'name':'32','values':{}}])['cards'][0]['outcome'],'UNSUPPORTED')

    def test_unknown_uncertainty_preserved(self):
        m=f.manifest(True)
        for state in ['exact_by_design','known_declared','unknown','not_assessed']:
            m['uncertainty']={'status':state,'references':['source'] if state=='known_declared' else []}
            c.validate_manifest(m)
            raw=f.raw([f.tree_item(f.lit(1))],m);b=a.ingest(m,raw,'mock-tree/1')
            self.assertEqual(b['receipt']['manifest_digest'],c.digest(m))
            self.assertEqual(m['dependence']['status'],'unknown')

    def test_historical_rankings(self):
        from Discovery.candidate_exchange_history import imported,BLOBS,PIN,MARGIN
        # Any accidental call to a fitted discovery path is a failure.
        with patch('Discovery.symbolic_benchmark_engine.discover',side_effect=AssertionError('discovery forbidden')), patch('Discovery.symbolic_benchmark_engine.fit',side_effect=AssertionError('fit forbidden')):
            for name in BLOBS:
                m,raw,b=imported(name);original=json.loads(raw)['discovery']['ranking']
                self.assertEqual(len(b['candidates']),5)
                self.assertEqual([x['source_item'] for x in b['candidates']],original)
                self.assertEqual([x['diagnostics'] for x in b['candidates']],original)
                self.assertEqual([x['source_item']['rank'] for x in b['candidates']],[1,2,3,4,5])
                self.assertEqual(b['receipt']['metadata']['fixture_mode'],'retrospective_outcome_known')
                points=f.fixed_points()
                result=a.evaluate_records(m,raw,'internal-margin1/1',b,points,PIN+':'+MARGIN+'/selection/'+name+'.json')
                for old,card in zip(original,result['cards']):
                    self.assertEqual(card['outcome'],'PASS')
                    self.assertEqual(card['scientific_evidence'],c.PROMOTION)
                    for point,row in zip(points,card['numerical_checks']):
                        expected=math.exp(old['log_coefficient']+math.fsum(float(Fraction(p))*math.log(point['values'][k]) for k,p in old['representative'].items()))
                        self.assertTrue(math.isclose(row['value'],expected,rel_tol=2e-12,abs_tol=1e-14))

    def test_context_identity_and_dense_dag(self):
        m=f.manifest(True);a1=c.analyze(f.var('x'),m,{})
        other=deepcopy(m);other['input_digest']='0'*64
        other['parameters']['k']['fit_context']['input_digest']='0'*64
        self.assertNotEqual(a1['model_id'],c.analyze(f.var('x'),other,{})['model_id'])
        # Shared subgraphs must be visited once, not exponentially revisited.
        for i in range(40):
            deps=['x','z'] if i<2 else ['d'+str(i-1),'d'+str(i-2)]
            m['quantities']['d'+str(i)]={'role':'derived','dimension':{},'unit':'dimensionless','domain':'real',
                'definition':dict.fromkeys(deps,1),'dependencies':deps}
        self.assertEqual(self.card(f.mul(f.lit(0),f.var('d39')),manifest=m,values={'x':1.,'z':1.})['outcome'],'PASS')
        bad=deepcopy(m);bad['quantities']['x']['dimension']={'L':'1e999999999999'}
        self.assertIn('run_rejection',a.ingest(bad,f.raw([],bad),'mock-tree/1'))

    def test_postfix_bounds_and_malformed_records(self):
        # 1 atom + 127 (atom,+) pairs + one unary = exactly 256 tokens.
        tokens=[f.lit(1)]+[t for _ in range(127) for t in [f.lit(1),'+']]+['exp']
        a.postfix(tokens)
        with self.assertRaises(c.ContractError):a.postfix(tokens+['log'])
        m=f.manifest(True)
        for tokens in [[],['+'],[f.lit(1),f.lit(2)],[{'operator':'arbitrary','exponent':1}],['__import__']]:
            item={'label':'bad','tokens':tokens,'coefficients':{},'metrics':{},'assertions':{},'render':'inert','opaque':{}}
            r=a.ingest(m,f.raw([item],m,'mock-postfix/1'),'mock-postfix/1')
            self.assertEqual(r['receipt']['candidate_count'],0)
        for raw in [b'[]',b'null',b'1',b'{"discovery":{},"error":null,"receipt":{}}']:
            self.assertIn('run_rejection',a.ingest(m,raw,'internal-margin1/1'))
        bad=deepcopy(m);bad['extra_semantic_authority']=True
        self.assertEqual(a.ingest(bad,f.raw([],bad),'mock-tree/1')['run_rejection']['code'],'FIELDS')



class CommittedEvidenceTests(unittest.TestCase):
    def test_read_only_evidence_guard(self):
        from Discovery.candidate_exchange_conformance import check
        check()


if __name__ == '__main__':unittest.main()
