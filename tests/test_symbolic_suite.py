"""Outcome-independent fixtures; never generate a Suite 1 or Benchmark 0 world."""
import copy
import math
from pathlib import Path
import tempfile
import unittest

from Discovery import symbolic_suite_engine as engine
from Discovery import symbolic_suite_runner as runner
from Discovery.symbolic_benchmark_engine import rmse


def fixture():
    meta={k:{'dimension':d,'unit':u,'definition':None} for k,d,u in
        [('x',{'L':1},'m'),('t',{'T':1},'s'),('z',{},'1')]}
    splits={}
    for split,offset in [('train',0),('validation',53)]:
        rows=[]
        for i in range(1,25):
            j=i+offset
            x,t,z=math.exp((j*11%31)/17),math.exp((j*7%29)/19),math.exp((j*13%37)/23)
            rows.append({'features':{'x':x,'t':t,'z':z},'target':1.7*x/t**2/z,'group':'g0'})
        splits[split]=rows
    return {'features':meta,'target':{'key':'y','dimension':{'L':1,'T':-2}},**splits,
        'policy':{'max_factors':3,'max_abs_power':2,'max_denominator':1,'complexity_lambda':0.001,
                  'acceptance_validation_rmse':1e-8,'approximation_rmse_max':0.071}}


class ForwardReceiptTests(unittest.TestCase):
    def test_missing_cache_and_completed_reads_live(self):
        result=runner.staged_discovery(fixture())
        self.assertTrue(runner.valid_receipt(result))
        receipt=result['receipt']
        self.assertEqual(len(receipt['expected_missing_cache_attempts']),len(runner.ENGINE_FILES))
        self.assertFalse(set(receipt['successful_reads']) & set(receipt['expected_missing_cache_attempts']))
        self.assertEqual(result['discovery']['top_class'],'t:-2|x:1|z:-1')
        self.assertEqual(receipt['inventory_before'],receipt['inventory_after'])

    def test_present_stale_cache_read_is_not_a_miss(self):
        result=runner.staged_discovery(fixture(),stale_cache=True,enforce=False)
        path='<stage>/Discovery/__pycache__/symbolic_suite_engine.cpython-312.pyc'
        self.assertIn(path,result['receipt']['successful_reads'])
        self.assertNotIn(path,result['receipt']['expected_missing_cache_attempts'])
        self.assertIn(path[8:],result['receipt']['inventory_before'])
        self.assertFalse(runner.valid_receipt(result))
        with self.assertRaises(runner.RunnerFailure): runner.staged_discovery(fixture(),stale_cache=True)

    def test_unexpected_source_cache_oracle_modules_rejected(self):
        for probe in ('<stage>/Discovery/unexpected.py','<stage>/Discovery/__pycache__/unexpected.cpython-312.pyc',
                      '<stage>/oracle.json','module:Discovery.symbolic_suite_worlds','module:http'):
            with self.subTest(probe=probe):
                result=runner.staged_discovery(fixture(),probe=probe,enforce=False)
                self.assertIsNotNone(result['error'])
                self.assertTrue(result['receipt']['denied_unexpected_attempts'])
                self.assertFalse(runner.valid_receipt(result))
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'oracle.json'; p.write_text('never read')
            with self.assertRaises(runner.RunnerFailure): runner.staged_discovery(fixture(),probe=str(p))

    def test_receipt_tamper_rejected(self):
        result=runner.staged_discovery(fixture())
        for key,value in [('successful_reads',[]),('expected_missing_cache_attempts',[]),
                          ('discovery_modules',['Discovery']),('inventory_after',{})]:
            altered=copy.deepcopy(result); altered['receipt'][key]=value
            self.assertFalse(runner.valid_receipt(altered))


class ScientificBoundaryTests(unittest.TestCase):
    def test_leakage_poison_reconstructive_and_cancelling_paths(self):
        raw=fixture()
        raw['features'].update({
            'leak':{'dimension':{'L':1,'T':-2},'unit':'a','definition':{'y':1}},
            'transitive':{'dimension':{'L':1,'T':-2},'unit':'a','definition':{'leak':1}},
            'transform':{'dimension':{'L':1,'T':-2},'unit':'a','definition':{'transitive':1,'z':1}},
            'power':{'dimension':{'L':2,'T':-4},'unit':'a2','definition':{'transitive':2}},
            'cancel':{'dimension':{},'unit':'1','definition':{'transitive':1,'y':-1}}})
        forbidden={'leak','transitive','transform','power','cancel'}
        for split in ('train','validation'):
            for row in raw[split]: row['features'].update({k:object() for k in forbidden})
        payload,classes=engine.prepare(raw)
        self.assertEqual({k for k,v in classes.items() if v['status']=='ineligible'},forbidden)
        result=engine.discover(payload)
        self.assertEqual(result['top_class'],'t:-2|x:1|z:-1')
        self.assertFalse(any(set(m)&forbidden for c in result['ranking'] for m in c['members']))
        with self.assertRaises(ValueError): engine.discover(raw)

    def test_api_rejects_hidden_information(self):
        for field in ('seed','oracle','heldout','truth','cell','world','law'):
            payload=fixture(); payload[field]='forbidden'
            with self.assertRaises(ValueError): engine.discover(payload)

    def test_approximation_is_not_adequacy_or_structural_credit(self):
        payload=fixture()
        for split in ('train','validation'):
            for row in payload[split]: row['target']*=math.exp(0.013*math.log(row['features']['z'])**2)
        payload['policy']['acceptance_validation_rmse']=0.00005
        result=engine.discover(payload)
        self.assertEqual(result['decision'],'no_stable_law')
        self.assertEqual(result['family_assessment'],'family_inadequate_on_validation')
        self.assertEqual(result['approximation_status'],'predictive_approximation')
        self.assertFalse(result['structural_recovery_claim'])
        payload['policy']['acceptance_validation_rmse']=0.12
        changed=engine.discover(payload)
        self.assertEqual(changed['family_assessment'],'contains_validation_adequate_member')

    def test_sealed_engine_cannot_access_heldout_and_tamper_fails(self):
        from Discovery.symbolic_suite import check_bound_data
        result=engine.discover(fixture()); before=copy.deepcopy(result)
        held=[{'features':{'x':1.,'t':1.,'z':1.},'target':1.7,'group':'g0'}]
        first=rmse(result['ranking'][0]['representative'],result['ranking'][0]['log_coefficient'],held)
        held[0]['target']*=9
        second=rmse(result['ranking'][0]['representative'],result['ranking'][0]['log_coefficient'],held)
        self.assertGreater(second,first); self.assertEqual(result,before)
        from Discovery.symbolic_benchmark_engine import digest
        commitment={'oracle_sha256':digest({'seed':'fixture'}),'heldout_sha256':digest(held)}
        seal={'commitment_sha256':digest(commitment),'selection_sha256':digest(result)}
        check_bound_data(commitment,seal,result,{'seed':'fixture'},held)
        for obj in ('selection','oracle','heldout'):
            with self.assertRaises(ValueError):
                check_bound_data(commitment,seal,{} if obj=='selection' else result,
                    {} if obj=='oracle' else {'seed':'fixture'},[] if obj=='heldout' else held)

    def test_metrics_against_independent_hand_calculation(self):
        from Discovery.symbolic_benchmark_engine import fit
        rows=[{'features':{'a':3},'target':15,'group':'g0'},
              {'features':{'a':7},'target':140,'group':'g0'}]
        self.assertAlmostEqual(math.exp(fit({'a':1},rows)),10)
        self.assertAlmostEqual(rmse({'a':1},math.log(10),rows),math.log(2))

class ForwardEvaluationTests(unittest.TestCase):
    def test_different_frozen_tolerances_and_regime_factor(self):
        from Discovery.symbolic_suite_evaluation import candidate_metrics,pair_diagnostic
        candidate={'representative':{'x':'1'},'log_coefficient':0.,'class_id':'x:1','rank':1,
            'expanded':{'x':'1'},'members':[{'x':'1'}],'validation_rmse':0.052}
        truth={'in_family':False,'base_signature':{'x':'2'},'irrelevant_atoms':[], 'forbidden_features':[]}
        rows=[{'features':{'x':2.},'target':2*math.exp(0.052),'group':'g0'}]
        policy={'acceptance_validation_rmse':0.061,'approximation_rmse_max':0.071}
        metric=candidate_metrics(candidate,rows,truth,policy)
        self.assertTrue(metric['validation_adequate']); self.assertTrue(metric['heldout_adequate'])
        self.assertTrue(metric['heldout_approximation']); self.assertFalse(metric['scientific_credit'])
        policy.update(acceptance_validation_rmse=0.041,approximation_rmse_max=0.049)
        changed=candidate_metrics(candidate,rows,truth,policy)
        self.assertFalse(changed['validation_adequate']); self.assertFalse(changed['heldout_approximation'])
        paired=[{'features':{'x':2},'target':3,'group':'g0'},
                {'features':{'x':2},'target':22.5,'group':'g1'}]
        self.assertTrue(pair_diagnostic(paired,7.5,1e-13))
        self.assertFalse(pair_diagnostic(paired,4.,1e-13))
        paired[1]['target']+=3e-5
        self.assertTrue(pair_diagnostic(paired,7.5,2e-5))
        self.assertFalse(pair_diagnostic(paired,7.5,1e-7))

    def test_noise_policy_is_derived_not_copied_literal(self):
        from Discovery.symbolic_suite_worlds import policy_for
        prereg={'grammar':{'max_factors':2,'max_abs_power':4,'max_denominator':1},
            'scoring':{'complexity_lambda':0.017,'adequacy_noise_multiplier':3.5,
                'numeric_floor':0.0002,'approximation_rmse_max':0.087}}
        self.assertAlmostEqual(policy_for(prereg,0.02)['acceptance_validation_rmse'],0.0702)
        self.assertEqual(policy_for(prereg,0.02)['approximation_rmse_max'],0.087)

    def test_equivalence_and_descendant_ablations_match_reenumeration(self):
        payload=fixture()
        payload['features'].update({
            'a':{'dimension':{'L':1,'T':-2},'unit':'a','definition':{'x':1,'t':-2}},
            'v':{'dimension':{'L':1,'T':-1},'unit':'v','definition':{'x':1,'t':-1}},
            'n':{'dimension':{},'unit':'1','definition':None},
            'n_alias':{'dimension':{},'unit':'1','definition':{'n':1}}})
        for split in ('train','validation'):
            for i,row in enumerate(payload[split]):
                f=row['features']; n=math.exp(0.0003*(-1)**i)
                f.update(a=f['x']/f['t']**2,v=f['x']/f['t'],n=n,n_alias=n)
        result=engine.discover(payload)
        self.assertGreaterEqual(len(result['ranking'][0]['members']),3)
        self.assertEqual(result['ranking'][0]['expanded_complexity'],4)
        self.assertEqual(result['top_class'],result['ablations']['n']['top_class'])
        self.assertIn('n_alias',result['ablations']['n']['removed_features'])
        for atom,ablation in result['ablations'].items():
            removed=set(ablation['removed_features']); masked=copy.deepcopy(payload)
            masked['features']={k:v for k,v in masked['features'].items() if k not in removed}
            for split in ('train','validation'):
                for row in masked[split]: row['features']={k:v for k,v in row['features'].items() if k not in removed}
            self.assertEqual(engine.discover(masked)['top_class'],ablation['top_class'])

    def test_aggregation_is_strict_and_retains_partial_counts(self):
        from Discovery.symbolic_suite_evaluation import aggregate
        prereg={'design':{'cells':['fixture'],'replicates_per_cell':4,'total_realizations':4},
            'evaluation':{'labels':{k:k for k in ('PASS','PARTIAL','FAIL','NO_GO_CAPABILITY')}},'nonclaims':[]}
        item={'cell':'fixture','success':True,'checks':{'leakage_safe':True},'false_positive_selection':False,
              'justified_abstention':False,'grammar_recognition':False}
        results={str(i):copy.deepcopy(item) for i in range(4)}
        self.assertEqual(aggregate(prereg,results,True)['disposition'],'PASS')
        results['3']['success']=False
        self.assertEqual(aggregate(prereg,results,True)['disposition'],'PARTIAL')
        self.assertEqual(aggregate(prereg,results,False)['disposition'],'FAIL')
        self.assertEqual(aggregate(prereg,{},True)['disposition'],'NO_GO_CAPABILITY')
        del results['3']
        self.assertEqual(aggregate(prereg,results,True)['evaluated_realizations'],3)
        self.assertEqual(aggregate(prereg,results,True)['disposition'],'PARTIAL')

    def test_disposition_routing_rejects_raw_fail_as_authoritative(self):
        from unittest.mock import patch
        from Discovery import symbolic_suite as h
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for path,value in [('raw.json',{'disposition':'FAIL'}),('corrected.json',{'disposition':'PASS'}),('suite.json',{'disposition':'PASS'})]:
                h.write_new(root/path,value)
            def entry(path): return {'path':path,'sha256':h.sha_file(root/path),'disposition':h.read(root/path)['disposition']}
            index={'schema':'tnp-symbolic-discovery/disposition-routing-v1',
                'Benchmark0':{'raw_epoch':entry('raw.json'),'reconciliation':entry('corrected.json'),'authoritative':'reconciliation','suite_aggregation':None},
                'BenchmarkSuite1':{'raw_epoch':entry('suite.json'),'reconciliation':None,'authoritative':'raw_epoch','suite_aggregation':entry('suite.json')}}
            with patch.object(h,'ROOT',root):
                h.validate_index(index)
                bad=copy.deepcopy(index); bad['Benchmark0']['authoritative']='raw_epoch'
                with self.assertRaises(ValueError): h.validate_index(bad)
                bad=copy.deepcopy(index); bad['Benchmark0']['reconciliation']['sha256']='0'*64
                with self.assertRaises(ValueError): h.validate_index(bad)

class NegativeFamilyTests(unittest.TestCase):
    def test_fractional_power_excluded_and_regimes_abstain(self):
        payload=fixture()
        for split in ('train','validation'):
            for row in payload[split]: row['target']*=row['features']['z']**1.5
        result=engine.discover(payload)
        self.assertEqual(result['decision'],'no_stable_law')
        self.assertEqual(result['family_assessment'],'family_inadequate_on_validation')
        self.assertTrue(result['ranking'])
        self.assertFalse(any(c['expanded'].get('z')=='1/2' for c in result['ranking']))
        payload=fixture()
        for split in ('train','validation'):
            pairs=[]
            for row in payload[split]:
                other=copy.deepcopy(row); other['target']*=6.5; other['group']='g1'
                pairs.extend([row,other])
            payload[split]=pairs
        result=engine.discover(payload)
        self.assertEqual(result['decision'],'no_stable_law')
        self.assertGreaterEqual(min(c['validation_rmse'] for c in result['ranking']),math.log(6.5)/2-1e-12)
